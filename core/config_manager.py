"""App configuration — persists user preferences (theme, language, etc.)."""

import json
import sys
from pathlib import Path

_DEFAULTS = {
    "language": "es",
    "theme": "dark",
}


def _config_file() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent
    p = base / "data" / "config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


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
