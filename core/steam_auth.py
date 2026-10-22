"""Steam OpenID authentication.

Opens the user's browser to the Steam login page.  Steam redirects back to a
local HTTP server; we extract the Steam64 ID from the OpenID response.
No API key required — works with any public Steam profile.
"""

import re
import urllib.parse
import urllib.request
import webbrowser
from typing import Optional

from core.oauth_helper import wait_for_callback

_PORT = 7421
_CB_PATH = "/steam/callback"
_RETURN_TO = f"http://localhost:{_PORT}{_CB_PATH}"


def steam_login_url() -> str:
    params = {
        "openid.ns":         "http://specs.openid.net/auth/2.0",
        "openid.mode":       "checkid_setup",
        "openid.return_to":  _RETURN_TO,
        "openid.realm":      f"http://localhost:{_PORT}",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.identity":   "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return "https://steamcommunity.com/openid/login?" + urllib.parse.urlencode(params)


def authenticate() -> Optional[str]:
    """
    Open Steam login in browser and wait for the redirect.
    Returns the Steam64 ID string on success, None on failure/timeout.
    """
    webbrowser.open(steam_login_url())
    raw = wait_for_callback(_PORT, _CB_PATH, timeout=120)
    if not raw:
        return None
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
    params = {k: v[0] for k, v in qs.items()}
    claimed = params.get("openid.claimed_id")
    if not claimed or not params.get("openid.return_to", "").startswith(_RETURN_TO):
        return None
    m = re.fullmatch(r"https://steamcommunity\.com/openid/id/(\d{17})", claimed)
    if not m:
        return None
    # Ask Steam to confirm the response really came from it (anyone could
    # otherwise open the local callback URL with a made-up Steam ID).
    if not _verify_with_steam(params):
        return None
    return m.group(1)


def _verify_with_steam(params: dict) -> bool:
    check = dict(params)
    check["openid.mode"] = "check_authentication"
    body = urllib.parse.urlencode(check).encode()
    req = urllib.request.Request(
        "https://steamcommunity.com/openid/login", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "GameManager/1.1"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return False
    return "is_valid:true" in text


def fetch_games_for_id(steam_id: str) -> list:
    """Fetch full game library for the given Steam64 ID (no API key needed)."""
    from core.steam_local_library import fetch_library_by_steam_id
    return fetch_library_by_steam_id(steam_id)
