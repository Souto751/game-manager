"""GOG Galaxy - detects installed GOG games from registry."""

import uuid
from pathlib import Path
from typing import Optional

from core.game_manager import Game

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

GOG_CDN = "https://images.gog-statics.com"


def detect_gog_games() -> list[Game]:
    if not WINREG_AVAILABLE:
        return []
    games = []
    for reg_path in [
        r"SOFTWARE\WOW6432Node\GOG.com\Games",
        r"SOFTWARE\GOG.com\Games",
    ]:
        games.extend(_read_gog_registry(reg_path))

    seen, unique = set(), []
    for g in games:
        key = g.install_path.lower() if g.install_path else g.name.lower()
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique


def _read_gog_registry(reg_path: str) -> list[Game]:
    games = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        i = 0
        while True:
            try:
                sub_name = winreg.EnumKey(root, i)
                sub = winreg.OpenKey(root, sub_name)
                try:
                    name = _qv(sub, "GAMENAME") or _qv(sub, "gameName") or sub_name
                    exe = _qv(sub, "EXE") or _qv(sub, "exe") or ""
                    install_path = _qv(sub, "PATH") or _qv(sub, "path") or ""
                    gog_id = _qv(sub, "PRODUCTID") or _qv(sub, "productId") or sub_name
                    workerdir = _qv(sub, "WORKINGDIR") or install_path

                    if not name:
                        i += 1
                        continue

                    full_exe = ""
                    if exe:
                        candidate = Path(exe) if Path(exe).is_absolute() else Path(workerdir) / exe
                        if candidate.exists():
                            full_exe = str(candidate)
                    if not full_exe and install_path and Path(install_path).exists():
                        full_exe = _find_main_exe(Path(install_path)) or ""

                    cover = _gog_cover_url(gog_id)

                    games.append(Game(
                        id=str(uuid.uuid4()),
                        name=name,
                        executable=full_exe,
                        cover_image=cover,
                        platform="gog",
                        install_path=install_path,
                        tags=["gog"],
                    ))
                finally:
                    winreg.CloseKey(sub)
                i += 1
            except OSError:
                break
        winreg.CloseKey(root)
    except Exception:
        pass
    return games


def _qv(key, name: str) -> str:
    try:
        val, _ = winreg.QueryValueEx(key, name)
        return str(val).strip()
    except Exception:
        return ""


def _gog_cover_url(gog_id: str) -> Optional[str]:
    """GOG cover images via their CDN - portrait format."""
    if not gog_id:
        return None
    return f"https://images.gog-statics.com/5643a7c831df452d29005caeca24c28cdbfbc058f8cc4b35ea9a3a9bf5cf66ac/product/{gog_id}/product-card-game-cover_160.jpg"


def _find_main_exe(directory: Path) -> Optional[str]:
    excluded = {"unins", "setup", "crash", "report", "redist", "galaxyclient"}
    candidates = [
        exe for exe in directory.glob("*.exe")
        if not any(exc in exe.stem.lower() for exc in excluded)
        and exe.stat().st_size > 200_000
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_size, reverse=True)
    return str(candidates[0])
