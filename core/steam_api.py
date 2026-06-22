"""Steam Web API - fetches full game catalog for a Steam account (including non-installed)."""

import urllib.request
import urllib.parse
import json
import uuid
from typing import Optional

from core.game_manager import Game

STEAM_API_BASE = "https://api.steampowered.com"
STEAM_CDN = "https://cdn.akamai.steamstatic.com/steam/apps"


def fetch_owned_games(api_key: str, steam_id: str) -> list[Game]:
    """
    Return all games owned by the Steam account.
    Requires:
      - api_key: from https://steamcommunity.com/dev/apikey
      - steam_id: 64-bit Steam ID (e.g. 76561198XXXXXXXXX)
    """
    params = urllib.parse.urlencode({
        "key": api_key,
        "steamid": steam_id,
        "include_appinfo": 1,
        "include_played_free_games": 1,
        "format": "json",
    })
    url = f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v1/?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        raise ConnectionError(f"Error al conectar con Steam API: {e}") from e

    raw_games = data.get("response", {}).get("games", [])
    games = []
    for g in raw_games:
        app_id = str(g.get("appid", ""))
        name = g.get("name", f"App {app_id}")
        playtime = g.get("playtime_forever", 0)  # minutes

        # Best available cover: portrait (600×900) preferred, fallback to header
        cover = _best_cover_url(app_id)

        games.append(Game(
            id=str(uuid.uuid4()),
            name=name,
            executable="",          # unknown until installed
            cover_image=cover,
            platform="steam",
            install_path="",
            play_count=0,
            tags=["steam", "cloud"],
            last_played=None,
        ))
    return games


def _best_cover_url(app_id: str) -> str:
    """Return Steam CDN URL for the game cover image."""
    # We store the URL directly; game_card will download it if needed
    return f"{STEAM_CDN}/{app_id}/library_600x900.jpg"


def validate_steam_id(steam_id: str) -> bool:
    """Basic validation: Steam64 IDs are 17-digit numbers starting with 7656."""
    return steam_id.isdigit() and len(steam_id) == 17 and steam_id.startswith("7656")
