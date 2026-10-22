r"""
make_installer.py — Crea GameManager_Setup.exe sin herramientas externas.

Pasos:
  1. Zipa dist\GameManager\ → temp\app_files.zip
  2. Copia icon.ico al directorio temp\
  3. Compila installer_src\setup_gui.py con PyInstaller --onefile
     incluyendo app_files.zip e icon.ico como archivos embebidos

Uso:
  python make_installer.py
  (o se llama automáticamente desde build.bat)
"""

import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
from version import __version__ as APP_VERSION  # single source of truth
DIST_DIR     = PROJECT_ROOT / "dist" / "GameManager"
INSTALLER_SCRIPT = PROJECT_ROOT / "installer_src" / "setup_gui.py"
ICON_PATH    = PROJECT_ROOT / "assets" / "icon.ico"
TEMP_DIR     = PROJECT_ROOT / "installer_build"
OUTPUT_DIR   = PROJECT_ROOT / "installer_output"
ZIP_NAME     = "app_files.zip"


def _ensure_removable(path: Path, attempts: int = 5, delay: float = 1.0) -> None:
    """Try to delete a previous build output before PyInstaller does.

    PyInstaller's own overwrite (os.remove) fails hard with a raw
    PermissionError/WinError 5 if the old .exe is locked (still running,
    open in Explorer, or held by an antivirus scan). Retrying here gives
    transient locks a chance to clear, and produces a clear error message
    instead of a stack trace if it's still stuck.
    """
    if not path.exists():
        return
    last_err = None
    for _ in range(attempts):
        try:
            path.unlink()
            return
        except PermissionError as e:
            last_err = e
            time.sleep(delay)
    print(f"[ERROR] No se pudo reemplazar {path.name} — el archivo esta bloqueado.")
    print("        Verifica que no este abierto/ejecutandose (Administrador de tareas)")
    print("        ni siendo escaneado por el antivirus, y volve a intentar.")
    raise SystemExit(1) from last_err


def main():
    if not DIST_DIR.exists():
        print("[ERROR] dist\\GameManager\\ no existe.")
        print("        Ejecuta build.bat primero para compilar el ejecutable.")
        sys.exit(1)

    _ensure_removable(OUTPUT_DIR / f"GameManager_Setup_{APP_VERSION}.exe")

    # ── Limpiar ──────────────────────────────────────────────────────────────
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ── Paso 1: Crear zip del ejecutable ─────────────────────────────────────
    zip_path = TEMP_DIR / ZIP_NAME
    print(f"[1/3] Empaquetando {DIST_DIR} → {zip_path.name} ...")

    files = list(DIST_DIR.rglob("*"))
    total = len([f for f in files if f.is_file()])
    count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in files:
            if f.is_file():
                arcname = f.relative_to(DIST_DIR)
                zf.write(f, arcname)
                count += 1
                if count % 50 == 0:
                    print(f"    {count}/{total} archivos...")

    print(f"    {count} archivos empaquetados. ({zip_path.stat().st_size // 1024 // 1024} MB)")

    # ── Paso 2: Copiar icono ──────────────────────────────────────────────────
    icon_arg = []
    if ICON_PATH.exists():
        shutil.copy(ICON_PATH, TEMP_DIR / "icon.ico")
        icon_arg = [f"--add-data={TEMP_DIR / 'icon.ico'};.", f"--icon={ICON_PATH}"]

    # ── Paso 2b: Copia del instalador con la version actual ───────────────────
    src = INSTALLER_SCRIPT.read_text(encoding="utf-8")
    marker = 'APP_VERSION = "'
    start = src.index(marker) + len(marker)
    end = src.index('"', start)
    installer_script = TEMP_DIR / "setup_gui.py"
    installer_script.write_text(src[:start] + APP_VERSION + src[end:], encoding="utf-8")

    # ── Paso 3: Compilar instalador con PyInstaller ───────────────────────────
    setup_name = f"GameManager_Setup_{APP_VERSION}"
    print(f"[2/3] Compilando instalador {setup_name}.exe ...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean",
        f"--name={setup_name}",
        f"--distpath={OUTPUT_DIR}",
        f"--workpath={TEMP_DIR / 'pyibuild'}",
        f"--specpath={TEMP_DIR}",
        f"--add-data={zip_path};.",
    ] + icon_arg + [
        str(installer_script)
    ]

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("[ERROR] PyInstaller falló al compilar el instalador.")
        sys.exit(1)

    # ── Resultado ─────────────────────────────────────────────────────────────
    out_exe = OUTPUT_DIR / f"{setup_name}.exe"
    if out_exe.exists():
        size_mb = out_exe.stat().st_size / 1024 / 1024
        print(f"\n[3/3] Listo!")
        print(f"      {out_exe}")
        print(f"      Tamaño: {size_mb:.1f} MB")
    else:
        print("[WARN] El archivo no se encontró en el destino esperado.")

    # Limpiar temporales
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
