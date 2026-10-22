@echo off
title Game Manager - Build
echo ============================================
echo   Game Manager - Build
echo ============================================
echo.

:: ── Verificar Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ desde https://python.org
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('python -c "from version import __version__; print(__version__)"') do set APP_VERSION=%%i
echo Version: %APP_VERSION%
echo.

:: ── Dependencias ─────────────────────────────────────────────────────────────
echo [1/4] Instalando dependencias...
pip install customtkinter Pillow pystray pyinstaller --quiet
if errorlevel 1 ( echo [ERROR] pip fallo. & pause & exit /b 1 )

:: ── Limpiar ───────────────────────────────────────────────────────────────────
echo [2/4] Limpiando builds anteriores...
if exist "dist\GameManager"  rmdir /s /q "dist\GameManager"
if exist "build\GameManager" rmdir /s /q "build\GameManager"
if not exist "data"          mkdir data

:: ── Compilar aplicacion ───────────────────────────────────────────────────────
echo [3/4] Compilando ejecutable...
python -m PyInstaller game_manager.spec --noconfirm
if errorlevel 1 ( echo [ERROR] PyInstaller fallo. & pause & exit /b 1 )
echo   Ejecutable listo en: dist\GameManager\GameManager.exe
echo.

:: ── Generar instalador ────────────────────────────────────────────────────────
echo [4/4] Generando instalador .exe...
python make_installer.py
if errorlevel 1 ( echo [WARN] No se pudo generar el instalador. & goto :done )

:done
echo.
pause
