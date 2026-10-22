"""Store entries that are tools or runtimes, not games.

Store libraries also list launchers and support packages (Steamworks Common
Redistributables, EA Desktop itself...). They are filtered out on import
and removed from libraries saved by older versions.
"""

import re

# Steam app ids of runtimes/tools that show up as "installed games".
_STEAM_TOOL_IDS = {
    "228980",    # Steamworks Common Redistributables
    "1070560",   # Steam Linux Runtime
    "1391110",   # Steam Linux Runtime - Soldier
    "1628350",   # Steam Linux Runtime - Sniper
    "1493710",   # Proton Experimental
    "1826330",   # Proton EasyAntiCheat Runtime
    "1161040",   # Proton BattlEye Runtime
}

_NAME_PATTERNS = [
    r"^steamworks common redistributables$",
    r"^steam linux runtime\b",
    r"^proton\b",
    r"^ea desktop$",
    r"^ea app$",
    r"^origin$",
    r"^ea anti-?cheat\b",
    r"^epic online services\b",
    r"^epic games launcher$",
    r"\bredistributables?\b",
]
_NAME_RE = re.compile("|".join(_NAME_PATTERNS), re.IGNORECASE)


def is_non_game(name: str, steam_app_id: str = "") -> bool:
    if steam_app_id and str(steam_app_id) in _STEAM_TOOL_IDS:
        return True
    return bool(_NAME_RE.search((name or "").strip()))
