# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Game Manager

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

python_dir = Path(sys.executable).parent
dlls_dir   = python_dir / "DLLs"
tcl_dir    = python_dir / "tcl"

binaries = []
for dll in dlls_dir.glob("_tkinter.pyd"):
    binaries.append((str(dll), "."))
for dll in dlls_dir.glob("tcl*.dll"):
    binaries.append((str(dll), "."))
for dll in dlls_dir.glob("tk*.dll"):
    binaries.append((str(dll), "."))
for dll in dlls_dir.glob("zlib*.dll"):
    binaries.append((str(dll), "."))

datas = []
if tcl_dir.exists():
    datas.append((str(tcl_dir), "tcl"))
lib_tkinter = python_dir / "Lib" / "tkinter"
if lib_tkinter.exists():
    datas.append((str(lib_tkinter), "tkinter"))

datas += collect_data_files("customtkinter", include_py_files=False)
# User data is NOT bundled: it lives in %APPDATA%\GameManager (see core/paths.py).
# Include assets (icon)
if Path("assets").exists():
    datas += [("assets", "assets")]

hiddenimports = (
    collect_submodules("customtkinter")
    + collect_submodules("pystray")
    + ["tkinter", "tkinter.ttk", "tkinter.messagebox",
       "tkinter.filedialog", "_tkinter", "PIL._tkinter_finder",
       "urllib.request", "urllib.error", "xml.etree.ElementTree",
       "winreg", "pystray._win32"]
)

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GameManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico" if Path("assets/icon.ico").exists() else None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GameManager",
)
