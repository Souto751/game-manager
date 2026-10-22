"""Folder scanner - finds game executables in user-selected directories."""

import uuid
from pathlib import Path

from core.game_manager import Game


# Executables to ignore (installers, tools, runtimes)
EXCLUDED_STEMS = {
    "unins000", "setup", "install", "uninstall", "uninst", "launcher",
    "vcredist_x86", "vcredist_x64", "dxsetup", "dotnetfx", "crashhandler",
    "crashreporter", "register", "activate", "cefsharp", "conhost",
    "upc", "uplay", "steam", "epicgameslauncher", "galaxyclient",
}

EXCLUDED_SUBSTRINGS = {
    "redist", "directx", "_commonredist", "dotnet", "vcredist",
    "physx", "dxwebsetup", "crashpad", "breakpad",
}


def is_likely_game_exe(exe: Path) -> bool:
    stem = exe.stem.lower()
    if stem in EXCLUDED_STEMS:
        return False
    if any(sub in str(exe).lower() for sub in EXCLUDED_SUBSTRINGS):
        return False
    # Skip very small files (< 500 KB) — likely helpers
    try:
        if exe.stat().st_size < 500 * 1024:
            return False
    except OSError:
        return False
    return True


def scan_folder(folder_path: str, depth: int = 2) -> list[Game]:
    """
    Scan a folder for game executables up to `depth` levels deep.
    Each top-level subfolder is treated as one potential game.
    """
    root = Path(folder_path)
    if not root.is_dir():
        return []

    games = []

    try:
        children = list(root.iterdir())
    except OSError:
        return []

    # Each immediate child directory = one potential game
    for game_dir in children:
        try:
            if not game_dir.is_dir():
                continue
        except OSError:
            continue

        exes = _find_executables(game_dir, current_depth=0, max_depth=depth)
        if not exes:
            continue

        # Best candidate: largest exe that passes filter
        best_exe = max(exes, key=_size_or_zero)

        games.append(Game(
            id=str(uuid.uuid4()),
            name=_pretty_name(game_dir.name),
            executable=str(best_exe),
            cover_image=_find_cover_image(game_dir),
            platform="custom",
            install_path=str(game_dir),
            tags=["scanned"],
        ))

    return games


def _find_executables(directory: Path, current_depth: int, max_depth: int) -> list[Path]:
    results = []
    try:
        for item in directory.iterdir():
            try:
                if item.is_file() and item.suffix.lower() == ".exe" and is_likely_game_exe(item):
                    results.append(item)
                elif item.is_dir() and current_depth < max_depth:
                    results.extend(_find_executables(item, current_depth + 1, max_depth))
            except OSError:
                continue
    except OSError:  # PermissionError, broken links, disconnected drives...
        pass
    return results


def _size_or_zero(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _find_cover_image(directory: Path) -> str | None:
    """Look for a cover/header image inside the game folder."""
    image_names = ["cover", "header", "poster", "thumbnail", "box", "icon"]
    image_exts = {".jpg", ".jpeg", ".png", ".webp"}

    for name in image_names:
        for ext in image_exts:
            candidate = directory / f"{name}{ext}"
            if candidate.exists():
                return str(candidate)

    # Fallback: first image file found
    try:
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() in image_exts:
                return str(item)
    except OSError:
        pass

    return None


def _pretty_name(folder_name: str) -> str:
    """Convert folder name to a readable game name."""
    # Replace separators with spaces
    name = folder_name.replace("_", " ").replace("-", " ").replace(".", " ")
    name = " ".join(name.split())
    # Only title-case all-lowercase names: keep "GTA V", "DOOM", "SpaceEngine" as written.
    return name.title() if name.islower() else name
