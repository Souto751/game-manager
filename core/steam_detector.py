"""Steam game detector - finds installed Steam games on Windows."""

import re
import uuid
from pathlib import Path
from typing import Optional

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

from core.game_manager import Game

STEAM_CDN = "https://cdn.akamai.steamstatic.com/steam/apps"


def get_steam_install_path() -> Optional[Path]:
    if not WINREG_AVAILABLE:
        return None
    for reg_path in [r"SOFTWARE\WOW6432Node\Valve\Steam", r"SOFTWARE\Valve\Steam"]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            return Path(path)
        except Exception:
            continue
    return None


def get_steam_library_folders(steam_path: Path) -> list[Path]:
    """Returns all Steam library steamapps folders, including extra drives."""
    folders = [steam_path / "steamapps"]

    vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"
    if not vdf_path.exists():
        return folders

    content = vdf_path.read_text(encoding="utf-8", errors="ignore")
    # Match both "path" entries and numeric-keyed path values
    for match in re.finditer(r'"path"\s+"([^"]+)"', content):
        folder = Path(match.group(1).replace("\\\\", "\\")) / "steamapps"
        if folder.exists() and folder not in folders:
            folders.append(folder)

    return folders


def parse_acf(acf_path: Path) -> dict:
    result = {}
    content = acf_path.read_text(encoding="utf-8", errors="ignore")
    for match in re.finditer(r'"(\w+)"\s+"([^"]*)"', content):
        result[match.group(1)] = match.group(2)
    return result


def detect_steam_games() -> list[Game]:
    steam_path = get_steam_install_path()
    if not steam_path or not steam_path.exists():
        return []

    games = []
    library_folders = get_steam_library_folders(steam_path)

    for library in library_folders:
        if not library.exists():
            continue
        for acf_file in library.glob("appmanifest_*.acf"):
            try:
                data = parse_acf(acf_file)
                app_id = data.get("appid", "")
                name = data.get("name", "")
                install_dir = data.get("installdir", "")
                if not name or not app_id:
                    continue

                install_path = library / "common" / install_dir
                executable = find_executable(install_path, name)

                # Use CDN URL for cover (portrait format)
                cover = f"{STEAM_CDN}/{app_id}/library_600x900.jpg"

                games.append(Game(
                    id=str(uuid.uuid4()),
                    name=name,
                    executable=executable or "",
                    cover_image=cover,
                    platform="steam",
                    install_path=str(install_path),
                    steam_app_id=app_id,
                    tags=["steam"],
                ))
            except Exception:
                continue

    return games


def find_executable(install_path: Path, game_name: str) -> Optional[str]:
    if not install_path.exists():
        return None
    excluded = {"unins", "setup", "redist", "vcredist", "directx", "crashreport",
                "register", "dxsetup", "dotnet", "uninst", "_commonredist"}
    candidates = []
    for exe in install_path.glob("*.exe"):
        if not any(exc in exe.stem.lower() for exc in excluded):
            candidates.append(exe)
    if not candidates:
        for exe in install_path.glob("**/*.exe"):
            if not any(exc in exe.stem.lower() for exc in excluded):
                candidates.append(exe)
                if len(candidates) >= 10:
                    break
    if not candidates:
        return None
    game_words = set(game_name.lower().split())
    for exe in candidates:
        if any(word in exe.stem.lower() for word in game_words if len(word) > 3):
            return str(exe)
    candidates.sort(key=lambda x: x.stat().st_size, reverse=True)
    return str(candidates[0])
