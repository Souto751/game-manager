"""Xbox Game Pass — detects games installed via Xbox app on Windows.

No OAuth required: reads the local XboxGames folder and the Windows registry
entries written by the Xbox app / Gaming Services.
Launching uses the ms-xboxlive:// protocol so the Xbox app handles auth.
"""

import uuid
from pathlib import Path
from typing import Optional

from core.game_manager import Game

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

# Default Xbox Game Pass installation directory (user-configurable in Xbox app)
_DEFAULT_XBOX_DIR = Path(r"C:\XboxGames")

# Known alternative roots
_EXTRA_ROOTS = [
    Path(r"C:\Program Files\ModifiableWindowsApps"),
]


def detect_xbox_games() -> list[Game]:
    games: list[Game] = []
    games.extend(_scan_xbox_dir(_DEFAULT_XBOX_DIR))
    for root in _EXTRA_ROOTS:
        games.extend(_scan_xbox_dir(root))
    games.extend(_from_registry())

    # Deduplicate by install path
    seen, unique = set(), []
    for g in games:
        key = g.install_path.lower() if g.install_path else g.name.lower()
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique


def _scan_xbox_dir(root: Path) -> list[Game]:
    """Each subfolder of root is typically one Xbox Game Pass game."""
    if not root.exists():
        return []
    games = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        name = _clean_name(entry.name)
        exe = _find_main_exe(entry)
        games.append(Game(
            id=str(uuid.uuid4()),
            name=name,
            executable=exe or "",
            cover_image=None,
            platform="xbox",
            install_path=str(entry),
            tags=["xbox", "gamepass"],
        ))
    return games


def _from_registry() -> list[Game]:
    """Read Gaming Services registry entries for installed Game Pass titles."""
    if not WINREG_AVAILABLE:
        return []
    games = []
    reg_paths = [
        r"SOFTWARE\Microsoft\GamingServices\PackageRepository\Root",
        r"SOFTWARE\Microsoft\GamingServices\PackageRepository\Package",
        r"SOFTWARE\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\Repository\Packages",
    ]
    for rp in reg_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rp)
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(key, i)
                    sub = winreg.OpenKey(key, sub_name)
                    try:
                        install_loc = _qv(sub, "Root") or _qv(sub, "PackageRootFolder") or ""
                        display = _qv(sub, "DisplayName") or _clean_name(sub_name)
                        if install_loc and Path(install_loc).exists():
                            exe = _find_main_exe(Path(install_loc))
                            games.append(Game(
                                id=str(uuid.uuid4()),
                                name=display,
                                executable=exe or "",
                                platform="xbox",
                                install_path=install_loc,
                                tags=["xbox", "gamepass"],
                            ))
                    finally:
                        winreg.CloseKey(sub)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            continue
    return games


def _qv(key, name: str) -> str:
    try:
        val, _ = winreg.QueryValueEx(key, name)
        return str(val).strip()
    except Exception:
        return ""


def _clean_name(folder_name: str) -> str:
    """Turn 'Halo Infinite_Content' → 'Halo Infinite'."""
    import re
    name = re.sub(r"[_\-\.]\d[\d\.]*$", "", folder_name)   # strip trailing version
    name = re.sub(r"_Content$|_Final$|_Game$", "", name, flags=re.I)
    return name.replace("_", " ").strip() or folder_name


def _find_main_exe(directory: Path) -> Optional[str]:
    excluded = {"unins", "setup", "crash", "report", "redist", "dx", "vcredist",
                "gamingservices", "gamelaunchhelper"}
    candidates = []
    for exe in directory.rglob("*.exe"):
        if any(exc in exe.stem.lower() for exc in excluded):
            continue
        try:
            if exe.stat().st_size > 100_000:
                candidates.append(exe)
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_size, reverse=True)
    return str(candidates[0])
