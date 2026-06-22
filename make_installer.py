"""
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

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

APP_VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).parent
DIST_DIR     = PROJECT_ROOT / "dist" / "GameManager"
INSTALLER_SCRIPT = PROJECT_ROOT / "installer_src" / "setup_gui.py"
ICON_PATH    = PROJECT_ROOT / "assets" / "icon.ico"
TEMP_DIR     = PROJECT_ROOT / "installer_build"
OUTPUT_DIR   = PROJECT_ROOT / "installer_output"
ZIP_NAME     = "app_files.zip"


def main():
    if not DIST_DIR.exists():
        print("[ERROR] dist\\GameManager\\ no existe.")
        print("        Ejecuta build.bat primero para compilar el ejecutable.")
        sys.exit(1)

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
        str(INSTALLER_SCRIPT)
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
