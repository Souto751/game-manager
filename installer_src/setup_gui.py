"""
Game Manager — Self-extracting installer GUI.

Este script es compilado por PyInstaller (--onefile).
El archivo app_files.zip se incluye como data en _MEIPASS.

Funciona con Python stdlib puro:
  tkinter, zipfile, shutil, winreg, subprocess, os, pathlib
"""

import os
import sys
import shutil
import zipfile
import winreg
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# ── Metadata ──────────────────────────────────────────────────────────────────
APP_NAME = "Game Manager"
APP_VERSION = "1.1.0"  # make_installer.py overwrites this with version.py
APP_PUBLISHER = "Souto751"
APP_EXE = "GameManager.exe"
APP_URL = "https://github.com/Souto751/game-manager"
# Per-user install: no administrator rights needed, and the app can update itself.
DEFAULT_INSTALL_DIR = (Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
                       / "Programs" / APP_NAME)
_REG_UNINSTALL = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                  "\\" + APP_PUBLISHER + APP_NAME.replace(" ", ""))
_REG_OWN = "SOFTWARE\\" + APP_PUBLISHER + "\\" + APP_NAME.replace(" ", "")

# ── Locate bundled zip (PyInstaller _MEIPASS) ─────────────────────────────────
def _bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

ZIP_PATH = _bundle_dir() / "app_files.zip"

# ── Tkinter colours ───────────────────────────────────────────────────────────
BG = "#1e1e2e"
SURFACE = "#2a2a3e"
PRIMARY = "#7c4dff"
ON_PRIMARY = "#ffffff"
TEXT = "#e0e0e0"
MUTED = "#888888"
SUCCESS = "#4caf50"
ERROR = "#f44336"


class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Instalar {APP_NAME} {APP_VERSION}")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg=BG)
        try:
            self.iconbitmap(str(_bundle_dir() / "icon.ico"))
        except Exception:
            pass

        self._install_dir = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self._shortcut_desktop = tk.BooleanVar(value=True)
        self._shortcut_startmenu = tk.BooleanVar(value=True)
        self._progress = tk.DoubleVar(value=0)
        self._state = "ready"  # ready | installing | done | error

        self._build_ui()
        self._check_existing_install()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=PRIMARY, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"  {APP_NAME}", font=("Segoe UI", 16, "bold"),
                 bg=PRIMARY, fg=ON_PRIMARY, anchor="w").pack(side="left", padx=16, pady=14)
        tk.Label(header, text=f"v{APP_VERSION}", font=("Segoe UI", 10),
                 bg=PRIMARY, fg="#ccbbff", anchor="e").pack(side="right", padx=16)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # Install path
        tk.Label(body, text="Carpeta de instalación:", font=("Segoe UI", 10),
                 bg=BG, fg=TEXT).pack(anchor="w")
        path_row = tk.Frame(body, bg=BG)
        path_row.pack(fill="x", pady=(4, 12))
        tk.Entry(path_row, textvariable=self._install_dir, font=("Segoe UI", 10),
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=0).pack(side="left", fill="x", expand=True,
                                           ipady=6, ipadx=8)
        tk.Button(path_row, text="...", font=("Segoe UI", 9),
                  bg=SURFACE, fg=TEXT, relief="flat", bd=0, cursor="hand2",
                  command=self._browse).pack(side="left", padx=(6, 0),
                                             ipady=6, ipadx=8)

        # Shortcuts
        tk.Label(body, text="Accesos directos:", font=("Segoe UI", 10),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Checkbutton(body, text="Menú Inicio", variable=self._shortcut_startmenu,
                       font=("Segoe UI", 9), bg=BG, fg=TEXT, selectcolor=SURFACE,
                       activebackground=BG, activeforeground=TEXT,
                       relief="flat").pack(anchor="w", pady=(2, 0))
        tk.Checkbutton(body, text="Escritorio", variable=self._shortcut_desktop,
                       font=("Segoe UI", 9), bg=BG, fg=TEXT, selectcolor=SURFACE,
                       activebackground=BG, activeforeground=TEXT,
                       relief="flat").pack(anchor="w")

        # Progress bar
        tk.Label(body, text="", bg=BG).pack(pady=4)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Purple.Horizontal.TProgressbar",
                        troughcolor=SURFACE, background=PRIMARY,
                        bordercolor=SURFACE, lightcolor=PRIMARY, darkcolor=PRIMARY)
        self._prog_bar = ttk.Progressbar(body, variable=self._progress,
                                         maximum=100, length=460,
                                         style="Purple.Horizontal.TProgressbar")
        self._prog_bar.pack(fill="x")

        self._status_lbl = tk.Label(body, text="", font=("Segoe UI", 9),
                                    bg=BG, fg=MUTED, anchor="w")
        self._status_lbl.pack(anchor="w", pady=(4, 0))

        # Buttons
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

        self._cancel_btn = tk.Button(
            btn_row, text="Cancelar", font=("Segoe UI", 10),
            bg=SURFACE, fg=TEXT, relief="flat", bd=0, cursor="hand2",
            padx=20, pady=8, command=self.destroy)
        self._cancel_btn.pack(side="right", padx=(8, 0))

        self._install_btn = tk.Button(
            btn_row, text="Instalar", font=("Segoe UI", 10, "bold"),
            bg=PRIMARY, fg=ON_PRIMARY, relief="flat", bd=0, cursor="hand2",
            padx=20, pady=8, command=self._start_install)
        self._install_btn.pack(side="right")

    def _browse(self):
        path = filedialog.askdirectory(title="Seleccionar carpeta de instalación",
                                       initialdir=self._install_dir.get())
        if path:
            chosen = Path(path)
            # Always install into our own subfolder, never straight into the chosen one.
            if chosen.name.lower() != APP_NAME.lower():
                chosen = chosen / APP_NAME
            self._install_dir.set(str(chosen))

    def _check_existing_install(self):
        """Reuse the folder of a previous per-user install (upgrade in place)."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_OWN) as key:
                existing = winreg.QueryValueEx(key, "InstallDir")[0]
            if existing and (Path(existing) / APP_EXE).exists():
                self._install_dir.set(existing)
        except OSError:
            pass

    # ── Install ───────────────────────────────────────────────────────────────

    def _start_install(self):
        if self._state == "done":
            self.destroy()
            return
        self._state = "installing"
        self._install_btn.configure(state="disabled")
        self._cancel_btn.configure(state="disabled")
        threading.Thread(target=self._do_install, daemon=True).start()

    def _do_install(self):
        try:
            dest = Path(self._install_dir.get()).expanduser()
            self._set_status("Preparando...")
            self._set_progress(5)

            _check_destination(dest)

            # Upgrade: replace only a previous Game Manager install. User data
            # (library, accounts, covers) lives in %APPDATA% and is never touched.
            if dest.exists() and (dest / APP_EXE).exists():
                self._set_status("Eliminando version anterior...")
                _ensure_not_running(dest / APP_EXE)
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)
            self._set_progress(10)

            # Extract zip
            self._set_status("Extrayendo archivos...")
            with zipfile.ZipFile(ZIP_PATH, "r") as zf:
                members = zf.namelist()
                total = len(members)
                for i, member in enumerate(members):
                    zf.extract(member, dest)
                    self._set_progress(10 + int(70 * (i + 1) / total))

            self._set_progress(80)
            self._set_status("Creando accesos directos...")

            exe_path = dest / APP_EXE

            if self._shortcut_startmenu.get():
                _create_shortcut_ps(
                    target=str(exe_path),
                    lnk_path=_startmenu_path(),
                    description=APP_NAME,
                    working_dir=str(dest),
                )

            if self._shortcut_desktop.get():
                _create_shortcut_ps(
                    target=str(exe_path),
                    lnk_path=_desktop_path(),
                    description=APP_NAME,
                    working_dir=str(dest),
                )

            self._set_progress(90)
            self._set_status("Registrando en el sistema...")
            _register_uninstall(dest, exe_path)

            self._set_progress(100)
            self._state = "done"
            self.after(0, self._show_done)

        except Exception as exc:
            self._state = "error"
            message = str(exc)  # bind now: `exc` is cleared after the except block
            self.after(0, lambda: self._show_error(message))

    def _set_status(self, msg: str):
        self.after(0, lambda: self._status_lbl.configure(text=msg))

    def _set_progress(self, val: float):
        self.after(0, lambda: self._progress.set(val))

    def _show_done(self):
        self._status_lbl.configure(text="Instalación completada.", fg=SUCCESS)
        self._install_btn.configure(
            text="Cerrar", state="normal",
            bg=SUCCESS, command=self.destroy)
        self._cancel_btn.configure(state="normal", text="Cerrar",
                                   command=self.destroy)
        messagebox.showinfo("Listo",
                            f"{APP_NAME} se instaló correctamente.\n\n"
                            f"Ruta: {self._install_dir.get()}")

    def _show_error(self, msg: str):
        self._status_lbl.configure(text=f"Error: {msg}", fg=ERROR)
        self._install_btn.configure(state="normal")
        self._cancel_btn.configure(state="normal")
        messagebox.showerror("Error de instalación", msg)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _startmenu_path() -> str:
    programs = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    programs.mkdir(parents=True, exist_ok=True)
    return str(programs / f"{APP_NAME}.lnk")


def _desktop_path() -> str:
    return str(Path.home() / "Desktop" / f"{APP_NAME}.lnk")


def _create_shortcut_ps(target: str, lnk_path: str, description: str, working_dir: str):
    """Create a .lnk shortcut using PowerShell (no pywin32 needed)."""
    script = (
        f'$s = (New-Object -ComObject WScript.Shell).CreateShortcut("{lnk_path}");'
        f'$s.TargetPath = "{target}";'
        f'$s.WorkingDirectory = "{working_dir}";'
        f'$s.Description = "{description}";'
        f'$s.Save()'
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, timeout=15,
    )


def _check_destination(dest: Path) -> None:
    """Refuse folders that hold other things: the upgrade step deletes the folder."""
    if not dest.exists():
        return
    if not dest.is_dir():
        raise RuntimeError(f"La ruta elegida es un archivo:\n{dest}")
    if (dest / APP_EXE).exists():
        return  # Previous Game Manager install: safe to replace.
    if any(dest.iterdir()):
        raise RuntimeError(
            "La carpeta elegida no esta vacia y no contiene una instalacion de "
            f"{APP_NAME}.\n\nElegi una carpeta vacia o una instalacion anterior.\n{dest}")


def _ensure_not_running(exe: Path) -> None:
    """A running exe is locked on Windows; renaming it is a cheap way to detect that."""
    probe = exe.with_suffix(".exe.check")
    try:
        exe.rename(probe)
        probe.rename(exe)
    except PermissionError:
        raise RuntimeError(
            f"{APP_NAME} esta abierto.\n\nCerralo (tambien desde el icono de la bandeja, "
            "boton derecho > Salir) y volve a intentar.") from None


def _ps_quote(value: str) -> str:
    return value.replace("'", "''")


def _register_uninstall(install_dir: Path, exe_path: Path):
    """Add a per-user entry to Windows "Installed apps" (no admin rights needed).

    Uninstalling removes the program, its shortcuts, the autostart entry and
    these registry keys. User data in %APPDATA%\\GameManager is kept.
    """
    script = "; ".join([
        f"Remove-Item -Recurse -Force -LiteralPath '{_ps_quote(str(install_dir))}' -ErrorAction SilentlyContinue",
        f"Remove-Item -Force -LiteralPath '{_ps_quote(_startmenu_path())}' -ErrorAction SilentlyContinue",
        f"Remove-Item -Force -LiteralPath '{_ps_quote(_desktop_path())}' -ErrorAction SilentlyContinue",
        "Remove-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' "
        "-Name 'GameManager' -ErrorAction SilentlyContinue",
        f"Remove-Item -Recurse -Path 'HKCU:\\{_REG_OWN}' -ErrorAction SilentlyContinue",
        f"Remove-Item -Recurse -Path 'HKCU:\\{_REG_UNINSTALL}' -ErrorAction SilentlyContinue",
    ])
    uninstall_cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{script}"'
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_UNINSTALL) as key:
            winreg.SetValueEx(key, "DisplayName",     0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion",  0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher",       0, winreg.REG_SZ, APP_PUBLISHER)
            winreg.SetValueEx(key, "DisplayIcon",     0, winreg.REG_SZ, str(exe_path))
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            winreg.SetValueEx(key, "URLInfoAbout",    0, winreg.REG_SZ, APP_URL)
            winreg.SetValueEx(key, "NoModify",        0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair",        0, winreg.REG_DWORD, 1)
        # Remember the folder for in-place upgrades.
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_OWN) as own_key:
            winreg.SetValueEx(own_key, "InstallDir", 0, winreg.REG_SZ, str(install_dir))
    except OSError:
        pass  # The app works without the uninstall entry.


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
