"""Game Manager - Core logic for managing games."""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional


def _get_data_file() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    return base / "data" / "games.json"


DATA_FILE = _get_data_file()


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
        cover_fetch_hint: tuple = None,   # ("epic", name) or ("ea", name, path)
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
        self.cover_fetch_hint = cover_fetch_hint  # transient, not persisted

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
    def __init__(self):
        self.games: list[Game] = []
        self.load()

    def load(self):
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.games = [Game.from_dict(g) for g in data.get("games", [])]
        else:
            self.games = []

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"games": [g.to_dict() for g in self.games]}, f,
                      indent=2, ensure_ascii=False)

    def add_game(self, game: Game):
        # Deduplicate: prefer steam_app_id match for Steam, then exe path, then name+platform
        if game.platform == "steam" and game.steam_app_id:
            if any(g.steam_app_id == game.steam_app_id for g in self.games):
                return
        elif game.executable:
            if any(g.executable == game.executable for g in self.games):
                return
        else:
            if any(g.name == game.name and g.platform == game.platform
                   for g in self.games):
                return
        self.games.append(game)
        self.save()

    def remove_game(self, game_id: str):
        self.games = [g for g in self.games if g.id != game_id]
        self.save()

    def get_game(self, game_id: str) -> Optional[Game]:
        return next((g for g in self.games if g.id == game_id), None)

    def filter_by_platform(self, platform: str) -> list[Game]:
        if platform == "all":
            return self.games
        return [g for g in self.games if g.platform == platform]
