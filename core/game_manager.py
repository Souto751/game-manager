"""Game Manager - Core logic for managing games."""

import json
import os
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Iterable, Optional

from core.non_games import is_non_game
from core.paths import data_file


class Game:
    def __init__(
        self,
        id: str,
        name: str,
        executable: str,
        cover_image: Optional[str] = None,
        platform: str = "custom",
        install_path: str = "",
        play_count: int = 0,
        last_played: Optional[str] = None,
        tags: list[str] = None,
        steam_app_id: str = "",
        cover_fetch_hint: tuple = None,   # ("epic", name), ("ea", name, path) or ("gog", product_id)
    ):
        self.id = id
        self.name = name
        self.executable = executable
        self.cover_image = cover_image
        self.platform = platform
        self.install_path = install_path
        self.play_count = play_count
        self.last_played = last_played
        self.tags = tags or []
        self.steam_app_id = steam_app_id
        # How to look up a cover online when cover_image is empty. Persisted so
        # the lookup can be retried on the next launch if it failed.
        self.cover_fetch_hint = tuple(cover_fetch_hint) if cover_fetch_hint else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "executable": self.executable,
            "cover_image": self.cover_image,
            "platform": self.platform,
            "install_path": self.install_path,
            "play_count": self.play_count,
            "last_played": self.last_played,
            "tags": self.tags,
            "steam_app_id": self.steam_app_id,
            "cover_hint": list(self.cover_fetch_hint) if self.cover_fetch_hint else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            executable=data.get("executable", ""),
            cover_image=data.get("cover_image"),
            platform=data.get("platform", "custom"),
            install_path=data.get("install_path", ""),
            play_count=data.get("play_count", 0),
            last_played=data.get("last_played"),
            tags=data.get("tags", []),
            steam_app_id=data.get("steam_app_id", ""),
            cover_fetch_hint=data.get("cover_hint"),
        )

    def launch(self):
        # Steam games: always launch via steam:// protocol so Steam handles
        # license validation, DRM, overlay, and cloud saves correctly.
        if self.platform == "steam" and self.steam_app_id:
            os.startfile(f"steam://rungameid/{self.steam_app_id}")
            return

        if not self.executable or not Path(self.executable).exists():
            raise FileNotFoundError(f"Executable not found: {self.executable}")
        subprocess.Popen([self.executable], cwd=self.install_path or None)


class GameManager:
    """Owns the game list. Safe to call from background threads (import/sync)."""

    def __init__(self):
        self.games: list[Game] = []
        self._lock = threading.RLock()
        self._path = data_file("games.json")
        self.load()

    def load(self):
        with self._lock:
            if self._path.exists():
                try:
                    data = json.loads(self._path.read_text(encoding="utf-8"))
                    games = [Game.from_dict(g) for g in data.get("games", [])]
                    # Drop tools/runtimes imported by older versions (e.g. EA Desktop).
                    self.games = [g for g in games if not is_non_game(g.name, g.steam_app_id)]
                    if len(self.games) != len(games):
                        self.save()
                except (OSError, ValueError):
                    # Corrupt file: keep a copy for recovery and start empty.
                    try:
                        self._path.replace(self._path.with_suffix(".json.bak"))
                    except OSError:
                        pass
                    self.games = []
            else:
                self.games = []

    def save(self):
        with self._lock:
            payload = json.dumps({"games": [g.to_dict() for g in self.games]},
                                 indent=2, ensure_ascii=False)
            # Write to a temp file first so a crash never leaves a half-written library.
            tmp = self._path.with_suffix(".json.tmp")
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, self._path)

    def _is_duplicate(self, game: Game) -> bool:
        # Prefer steam_app_id for Steam, then exe path, then name+platform.
        if game.platform == "steam" and game.steam_app_id:
            return any(g.steam_app_id == game.steam_app_id for g in self.games)
        if game.executable:
            return any(g.executable == game.executable for g in self.games)
        return any(g.name == game.name and g.platform == game.platform for g in self.games)

    def add_game(self, game: Game) -> bool:
        """Add one game. Returns True if it was new."""
        return self.add_games([game]) == 1

    def add_games(self, games: Iterable[Game]) -> int:
        """Add many games with a single save. Returns how many were new."""
        added = 0
        with self._lock:
            for game in games:
                if is_non_game(game.name, game.steam_app_id):
                    continue
                if not self._is_duplicate(game):
                    self.games.append(game)
                    added += 1
            if added:
                self.save()
        return added

    def set_cover(self, game_id: str, cover: str):
        """Persist a cover found after import (Epic/EA/GOG lookups)."""
        with self._lock:
            game = self.get_game(game_id)
            if game and game.cover_image != cover:
                game.cover_image = cover
                self.save()

    def remove_game(self, game_id: str):
        with self._lock:
            self.games = [g for g in self.games if g.id != game_id]
            self.save()

    def get_game(self, game_id: str) -> Optional[Game]:
        return next((g for g in self.games if g.id == game_id), None)

    def filter_by_platform(self, platform: str) -> list[Game]:
        if platform == "all":
            return self.games
        return [g for g in self.games if g.platform == platform]
