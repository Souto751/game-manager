"""Windows autostart management (HKCU Run registry key).

Lets the app register/unregister itself to launch automatically when the
user logs into Windows. Safe to import on non-Windows systems — every
function degrades to a no-op (returns False) if `winreg` isn't available.
"""

import sys
from pathlib import Path

_VALUE_NAME = "GameManager"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _command() -> str:
    """Command line used to launch the app on Windows startup."""
    if getattr(sys, "frozen", False):
        # Packaged .exe (PyInstaller) — launch it directly.
        return f'"{sys.executable}"'

    # Dev mode: run through pythonw.exe (no console window) if available.
    exe = Path(sys.executable)
    pythonw = exe.parent / "pythonw.exe"
    interpreter = pythonw if pythonw.exists() else exe
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{interpreter}" "{main_py}"'


def is_enabled() -> bool:
    """Return True if the Run key currently points at this app."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
        return True
    except Exception:
        return False


def enable() -> bool:
    """Add (or refresh) the Run key entry. Returns True on success."""
    try:
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _command())
        return True
    except Exception:
        return False


def disable() -> bool:
    """Remove the Run key entry. Returns True on success (or if already absent)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _VALUE_NAME)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False
