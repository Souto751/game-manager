"""Where the app keeps its files.

- User data (games.json, config.json, accounts.json, covers/) lives in
  %APPDATA%\\GameManager, so the app works even when installed in a
  read-only folder such as Program Files, and updates never touch it.
- Bundled resources (assets/icon.ico) are read from the PyInstaller bundle
  (sys._MEIPASS) when frozen, or from the project root in development.
"""

import os
import shutil
import sys
from pathlib import Path

APP_DIR_NAME = "GameManager"
_DATA_FILES = ("games.json", "config.json", "accounts.json")

_data_dir_cache: Path | None = None


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    """Path to a bundled, read-only resource (e.g. resource_path('assets', 'icon.ico'))."""
    base = Path(getattr(sys, "_MEIPASS", _project_root()))
    return base.joinpath(*parts)


def _legacy_data_dirs() -> list[Path]:
    """Places where versions <= 1.0.0 stored user data (next to the exe).

    1.0.0 installed into Program Files by default and 1.1 installs per user,
    so the old install folder is checked too.
    """
    if not getattr(sys, "frozen", False):
        return [_project_root() / "data"]
    install_dirs = [Path(sys.executable).parent]
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        install_dirs.append(Path(program_files) / "Game Manager")
    dirs = []
    for d in install_dirs:
        dirs += [d / "data", d / "_internal" / "data"]
    return dirs


def _migrate_legacy_data(target: Path) -> None:
    """Copy data from the old location once, without overwriting anything."""
    if any((target / name).exists() for name in _DATA_FILES):
        return
    for legacy in _legacy_data_dirs():
        if not legacy.is_dir():
            continue
        found = False
        for name in _DATA_FILES:
            src = legacy / name
            if src.is_file():
                shutil.copy2(src, target / name)
                found = True
        covers = legacy / "covers"
        if covers.is_dir() and not (target / "covers").exists():
            shutil.copytree(covers, target / "covers")
        if found:
            return


def data_dir() -> Path:
    """Writable per-user data directory (created on first use)."""
    global _data_dir_cache
    if _data_dir_cache is not None:
        return _data_dir_cache

    if getattr(sys, "frozen", False) or os.environ.get("APPDATA"):
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        target = base / APP_DIR_NAME
    else:
        # Non-Windows development fallback.
        target = _project_root() / "data"

    target.mkdir(parents=True, exist_ok=True)
    try:
        _migrate_legacy_data(target)
    except OSError:
        pass  # Migration is best-effort; a fresh library is still usable.

    _data_dir_cache = target
    return target


def data_file(name: str) -> Path:
    return data_dir() / name


def covers_dir() -> Path:
    d = data_dir() / "covers"
    d.mkdir(parents=True, exist_ok=True)
    return d
