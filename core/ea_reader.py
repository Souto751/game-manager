"""EA App — detects installed EA/Origin games on Windows.

Scans multiple sources:
  1. EA Desktop InstallData JSON files (per-machine and per-user)
  2. installerdata.xml inside __Installer subdirs of each game folder
  3. Common install directories (Program Files)
  4. Windows registry (EA Games / Electronic Arts keys)
"""

import json
import os
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from core.game_manager import Game

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

_EXCLUDED = {"unins", "setup", "crash", "report", "redist", "eaanticheat",
             "activation", "helper", "launcher", "easteam", "dxsetup",
             "vcredist", "directx", "install", "prereq"}

_INSTALL_DATA_DIRS = [
    Path(r"C:\ProgramData\EA Desktop\InstallData"),
    Path(r"C:\ProgramData\Origin\InstallData"),
    Path(r"C:\ProgramData\Electronic Arts\EA Desktop\InstallData"),
]

def _user_install_data_dirs() -> list:
    dirs = []
    for env_var in ("LOCALAPPDATA", "APPDATA"):
        base = os.environ.get(env_var, "")
        if not base:
            continue
        for sub in (
            r"Electronic Arts\EA Desktop\InstallData",
            r"EA Desktop\InstallData",
            r"Origin\InstallData",
        ):
            p = Path(base) / sub
            if p.exists():
                dirs.append(p)
    return dirs

_COMMON_DIRS = [
    Path(r"C:\Program Files\EA Games"),
    Path(r"C:\Program Files (x86)\EA Games"),
    Path(r"C:\Program Files\Electronic Arts"),
    Path(r"C:\Program Files (x86)\Electronic Arts"),
    Path(r"C:\Program Files\Origin Games"),
    Path(r"C:\Program Files (x86)\Origin Games"),
]

_REG_PATHS = [
    r"SOFTWARE\WOW6432Node\EA Games",
    r"SOFTWARE\EA Games",
    r"SOFTWARE\WOW6432Node\Electronic Arts\EA Games",
    r"SOFTWARE\Electronic Arts\EA Games",
    r"SOFTWARE\WOW6432Node\Electronic Arts",
    r"SOFTWARE\Electronic Arts",
    r"SOFTWARE\WOW6432Node\Origin",
    r"SOFTWARE\Origin",
]


def detect_ea_games() -> list:
    games = []
    games.extend(_from_install_data())
    games.extend(_from_common_dirs())
    games.extend(_from_registry())

    seen_paths: set = set()
    seen_names: set = set()
    unique = []
    for g in games:
        path_key = g.install_path.lower() if g.install_path else ""
        name_key = g.name.lower()
        if path_key and path_key in seen_paths:
            continue
        if not path_key and name_key in seen_names:
            continue
        if path_key:
            seen_paths.add(path_key)
        seen_names.add(name_key)
        unique.append(g)
    return unique


# ── Source 1: InstallData JSON files ─────────────────────────────────────────

def _from_install_data() -> list:
    games = []
    all_dirs = list(_INSTALL_DATA_DIRS) + _user_install_data_dirs()
    for base in all_dirs:
        if not base.exists():
            continue
        for jf in base.rglob("*.json"):
            try:
                data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
                g = _game_from_json(data)
                if g:
                    games.append(g)
            except Exception:
                continue
    return games


def _game_from_json(data: dict) -> Optional[Game]:
    name = (data.get("baseGameTitle") or data.get("softwareName")
            or data.get("displayName") or data.get("gameTitle") or "").strip()
    install_path = (data.get("installPath") or data.get("baseInstallPath")
                    or data.get("installLocation") or data.get("baseInstallLocation")
                    or "").strip()
    if not name:
        return None

    exe_rel = (data.get("executablePath") or data.get("baseExecutablePath") or "").strip()
    full_exe = _resolve_exe(install_path, exe_rel) if install_path else ""
    content_id = (data.get("contentId") or data.get("softwareId")
                  or data.get("baseGameId") or "").strip()

    return Game(
        id=str(uuid.uuid4()),
        name=name,
        executable=full_exe,
        cover_image=None,
        cover_fetch_hint=("ea", name, install_path, content_id),
        platform="ea",
        install_path=install_path,
        tags=["ea"],
    )


# ── Source 2: Common install directories ─────────────────────────────────────

def _from_common_dirs() -> list:
    games = []
    for root_dir in _COMMON_DIRS:
        if not root_dir.exists():
            continue
        for entry in root_dir.iterdir():
            if not entry.is_dir():
                continue
            g = _game_from_installer_xml(entry)
            if not g:
                exe = _find_main_exe(entry)
                g = Game(
                    id=str(uuid.uuid4()),
                    name=entry.name,
                    executable=exe or "",
                    cover_image=None,
                    cover_fetch_hint=("ea", entry.name, str(entry), ""),
                    platform="ea",
                    install_path=str(entry),
                    tags=["ea"],
                )
            games.append(g)
    return games


# ── Source 3: Windows registry ────────────────────────────────────────────────

def _from_registry() -> list:
    if not WINREG_AVAILABLE:
        return []
    games = []
    for reg_path in _REG_PATHS:
        try:
            root_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        except OSError:
            continue
        i = 0
        while True:
            try:
                sub_name = winreg.EnumKey(root_key, i)
                sub = winreg.OpenKey(root_key, sub_name)
                try:
                    install_dir = (_regval(sub, "Install Dir")
                                   or _regval(sub, "InstallLocation")
                                   or _regval(sub, "InstallPath")
                                   or _regval(sub, "Install Path") or "")
                    name = (_regval(sub, "DisplayName")
                            or _regval(sub, "GameName") or sub_name)
                    content_id = (_regval(sub, "ContentId")
                                  or _regval(sub, "contentId") or "")
                    if not install_dir or not Path(install_dir).exists():
                        i += 1
                        continue
                    g = _game_from_installer_xml(Path(install_dir))
                    if not g:
                        exe = _find_main_exe(Path(install_dir))
                        g = Game(
                            id=str(uuid.uuid4()),
                            name=name,
                            executable=exe or "",
                            cover_image=None,
                            cover_fetch_hint=("ea", name, install_dir, content_id),
                            platform="ea",
                            install_path=install_dir,
                            tags=["ea"],
                        )
                    games.append(g)
                finally:
                    winreg.CloseKey(sub)
            except OSError:
                break
            i += 1
        winreg.CloseKey(root_key)
    return games


# ── installerdata.xml parser ──────────────────────────────────────────────────

def _game_from_installer_xml(game_dir: Path) -> Optional[Game]:
    xml_path = game_dir / "__Installer" / "installerdata.xml"
    if not xml_path.exists():
        return None
    try:
        tree = ET.parse(xml_path)
        root_el = tree.getroot()

        name = ""
        for tag in ("gameTitle", "contentTitle", "softwareName", "DisplayName"):
            el = root_el.find(".//" + tag)
            if el is not None and el.text:
                name = el.text.strip()
                break
        if not name:
            name = game_dir.name

        content_id = ""
        for tag in ("contentID", "contentId", "gameID", "softwareID"):
            el = root_el.find(".//" + tag)
            if el is not None and el.text:
                content_id = el.text.strip()
                break

        exe_rel = ""
        for tag in ("executable", "executablePath", "launchPath"):
            el = root_el.find(".//" + tag)
            if el is not None and el.text:
                exe_rel = el.text.strip()
                break

        full_exe = _resolve_exe(str(game_dir), exe_rel)

        return Game(
            id=str(uuid.uuid4()),
            name=name,
            executable=full_exe,
            cover_image=None,
            cover_fetch_hint=("ea", name, str(game_dir), content_id),
            platform="ea",
            install_path=str(game_dir),
            tags=["ea"],
        )
    except Exception:
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_exe(install_path: str, exe_rel: str) -> str:
    if not exe_rel:
        return _find_main_exe(Path(install_path)) or "" if install_path else ""
    p = Path(exe_rel)
    if p.is_absolute():
        return str(p) if p.exists() else ""
    if install_path:
        candidate = Path(install_path) / exe_rel
        return str(candidate) if candidate.exists() else ""
    return ""


def _find_main_exe(directory: Path) -> Optional[str]:
    if not directory.exists():
        return None
    candidates = []
    for exe in directory.glob("*.exe"):
        stem = exe.stem.lower()
        if not any(exc in stem for exc in _EXCLUDED):
            try:
                if exe.stat().st_size > 200_000:
                    candidates.append(exe)
            except OSError:
                pass
    if not candidates:
        for exe in directory.rglob("*.exe"):
            parts_lower = [part.lower() for part in exe.parts]
            if any(x in parts_lower for x in ("__installer", "redist", "support", "prereq")):
                continue
            stem = exe.stem.lower()
            if not any(exc in stem for exc in _EXCLUDED):
                try:
                    if exe.stat().st_size > 500_000:
                        candidates.append(exe)
                except OSError:
                    pass
            if len(candidates) >= 8:
                break
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_size, reverse=True)
    return str(candidates[0])


def _regval(key, name: str) -> str:
    try:
        v, _ = winreg.QueryValueEx(key, name)
        return str(v).strip()
    except Exception:
        return ""
