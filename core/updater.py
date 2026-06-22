"""Checks GitHub Releases for a newer version of the app.

Usage (non-blocking):
    from core.updater import check_for_updates_async
    check_for_updates_async(on_update_available=lambda info: ...)
"""

import threading
import urllib.request
import urllib.error
import json
from typing import Callable, Optional

from version import __version__, GITHUB_REPO

_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"


def _parse_version(v: str) -> tuple:
    """Convert '1.2.3' (or 'v1.2.3') to (1, 2, 3) for comparison."""
    v = v.lstrip("v").strip()
    try:
        return tuple(int(x) for x in v.split(".")[:3])
    except ValueError:
        return (0, 0, 0)


def check_for_updates() -> Optional[dict]:
    """
    Fetches the latest release from GitHub.
    Returns a dict with keys {tag, name, url, body} if a newer version exists,
    or None if already up to date or on any error.
    """
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"User-Agent": "game-manager-updater/1.0",
                     "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        tag = data.get("tag_name", "")
        if not tag:
            return None

        latest = _parse_version(tag)
        current = _parse_version(__version__)

        if latest > current:
            return {
                "tag": tag,
                "name": data.get("name", tag),
                "url": data.get("html_url", _RELEASES_URL),
                "body": data.get("body", ""),
                "current": __version__,
            }
        return None
    except Exception:
        return None


def check_for_updates_async(
    on_update_available: Callable[[dict], None],
    delay_seconds: float = 4.0,
) -> None:
    """
    Runs the update check in a daemon thread after `delay_seconds`.
    Calls `on_update_available(info)` on the background thread if a
    new version is found — the caller must marshal to the UI thread with
    `widget.after(0, ...)` before touching Tkinter widgets.
    """
    def _run():
        import time
        time.sleep(delay_seconds)
        info = check_for_updates()
        if info:
            on_update_available(info)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
