"""Account manager — persists linked platform credentials."""

import json
from pathlib import Path

from core.paths import data_file


def _accounts_path() -> Path:
    return data_file("accounts.json")


class AccountManager:
    def __init__(self):
        self._path = _accounts_path()
        self._data: dict = {}
        self._load()

    def _load(self):
        try:
            if self._path.exists():
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            self._data = {}

    def _save(self):
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Generic helpers ───────────────────────────────────────────────────────

    def _get(self, platform: str, key: str) -> str:
        return self._data.get(platform, {}).get(key, "")

    def _set_platform(self, platform: str, fields: dict):
        self._data.setdefault(platform, {}).update(fields)
        self._save()

    def clear(self, platform: str):
        self._data.pop(platform, None)
        self._save()

    def linked(self, platform: str) -> bool:
        d = self._data.get(platform, {})
        return any(v.strip() for v in d.values())

    # ── Steam ─────────────────────────────────────────────────────────────────

    @property
    def steam_api_key(self) -> str:
        return self._get("steam", "api_key")

    @property
    def steam_id(self) -> str:
        return self._get("steam", "steam_id")

    def save_steam(self, api_key: str, steam_id: str):
        self._set_platform("steam", {"api_key": api_key.strip(), "steam_id": steam_id.strip()})

    # ── Xbox ──────────────────────────────────────────────────────────────────

    @property
    def xbox_gamertag(self) -> str:
        return self._get("xbox", "gamertag")

    def save_xbox(self, gamertag: str):
        self._set_platform("xbox", {"gamertag": gamertag.strip()})

    # ── EA App ────────────────────────────────────────────────────────────────

    @property
    def ea_email(self) -> str:
        return self._get("ea", "email")

    def save_ea(self, email: str):
        self._set_platform("ea", {"email": email.strip()})

    # ── Epic Games ────────────────────────────────────────────────────────────

    @property
    def epic_username(self) -> str:
        return self._get("epic", "username")

    def save_epic(self, username: str):
        self._set_platform("epic", {"username": username.strip()})
