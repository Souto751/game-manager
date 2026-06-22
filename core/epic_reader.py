"""Epic Games - reads local manifest files to detect installed games."""

import json
import uuid
from pathlib import Path
from typing import Optional

from core.game_manager import Game

MANIFESTS_DIR = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests")


def detect_epic_games(manifests_dir: Path = MANIFESTS_DIR) -> list[Game]:
    if not manifests_dir.exists():
        return []

    games = []
    for item_file in manifests_dir.glob("*.item"):
        try:
            data = json.loads(item_file.read_text(encoding="utf-8"))
            name = data.get("DisplayName", "")
            install_path = data.get("InstallLocation", "")
            exe_path = data.get("LaunchExecutable", "")
            if not name:
                continue

            full_exe = ""
            if install_path and exe_path:
                candidate = Path(install_path) / exe_path
                if candidate.exists():
                    full_exe = str(candidate)

            # Try to get cover from local install dir first
            cover = _find_local_cover(install_path)

            games.append(Game(
                id=str(uuid.uuid4()),
                name=name,
                executable=full_exe,
                cover_image=cover,   # will be enriched async in game_card
                cover_fetch_hint=("epic", name),
                platform="epic",
                install_path=install_path,
                tags=["epic"],
            ))
        except Exception:
            continue

    return games


def _find_local_cover(install_path: str) -> Optional[str]:
    if not install_path:
        return None
    root = Path(install_path)
    for name in ["cover", "header", "poster", "thumbnail"]:
        for ext in [".jpg", ".png", ".jpeg"]:
            p = root / f"{name}{ext}"
            if p.exists():
                return str(p)
    return None
