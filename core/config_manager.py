"""App configuration — persists user preferences (theme, language, etc.)."""

import json
from pathlib import Path

from core.paths import data_file

_DEFAULTS = {
    "language": "es",
    "theme": "dark",
    "start_with_windows": False,
}


def _config_file() -> Path:
    return data_file("config.json")


class ConfigManager:
    def __init__(self):
        self._path = _config_file()
        self._data: dict = dict(_DEFAULTS)
        self._load()

    def _load(self):
        try:
            if self._path.exists():
                self._data.update(json.loads(self._path.read_text(encoding="utf-8")))
        except Exception:
            pass

    def save(self):
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str):
        return self._data.get(key, _DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value
        self.save()
