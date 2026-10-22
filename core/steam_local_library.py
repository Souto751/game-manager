"""Steam local library - fetches full game catalog without an API key.

Uses the public Steam profile XML endpoint. Requires the user's profile
to be set to Public in Steam Privacy Settings.
"""

import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

from core.game_manager import Game

STEAM_CDN = "https://cdn.akamai.steamstatic.com/steam/apps"
STEAM3_OFFSET = 76561197960265728


def get_local_steam_id() -> Optional[str]:
    """Read the currently active Steam user ID from the registry."""
    if not WINREG_AVAILABLE:
        return None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Valve\Steam\ActiveProcess")
        steam3_id, _ = winreg.QueryValueEx(key, "ActiveUser")
        winreg.CloseKey(key)
        if steam3_id and steam3_id != 0:
            steam64 = steam3_id + STEAM3_OFFSET
            return str(steam64)
    except Exception:
        pass

    # Fallback: scan userdata folders
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\WOW6432Node\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        userdata = Path(steam_path) / "userdata"
        if userdata.exists():
            folders = [f for f in userdata.iterdir() if f.is_dir() and f.name.isdigit()]
            if folders:
                steam3 = int(folders[0].name)
                return str(steam3 + STEAM3_OFFSET)
    except Exception:
        pass

    return None


def fetch_library_by_steam_id(steam_id: str) -> list[Game]:
    """
    Fetch all owned games via the public Steam profile XML.
    Returns an empty list if the profile is private.
    """
    url = f"https://steamcommunity.com/profiles/{steam_id}/games?xml=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GameManager/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar con Steam: {e}") from e

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        raise ValueError(f"Respuesta de Steam invalida: {e}") from e

    # Check if profile is private
    error = root.findtext("error")
    if error:
        raise PermissionError(
            "Perfil de Steam privado.\n\n"
            "Para importar tu biblioteca sin API key, tu perfil debe estar en Publico:\n"
            "Steam > Perfil > Editar perfil > Configuracion de privacidad > "
            "Juegos > Publico"
        )

    games = []
    for game_el in root.findall(".//game"):
        app_id = game_el.findtext("appID") or ""
        name = game_el.findtext("name") or f"App {app_id}"
        hours_text = game_el.findtext("hoursOnRecord") or "0"
        try:
            hours = float(hours_text.replace(",", "."))
        except ValueError:
            hours = 0.0

        if not app_id:
            continue

        games.append(Game(
            id=str(uuid.uuid4()),
            name=name,
            executable="",
            cover_image=f"{STEAM_CDN}/{app_id}/library_600x900.jpg",
            platform="steam",
            install_path="",
            steam_app_id=app_id,
            tags=["steam", "cloud"],
        ))

    return games
