@echo off
title Game Manager - Build
echo ============================================
echo   Game Manager - Generando ejecutable...
echo ============================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ desde https://python.org
    pause
    exit /b 1
)

:: Leer version actual
for /f "tokens=*" %%i in ('python -c "from version import __version__; print(__version__)"') do set APP_VERSION=%%i
echo Version: %APP_VERSION%

:: Instalar dependencias
echo.
echo [1/4] Instalando dependencias...
pip install customtkinter Pillow pyinstaller requests --quiet
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

:: Limpiar build anterior
echo [2/4] Limpiando build anterior...
if exist "dist\GameManager" rmdir /s /q "dist\GameManager"
if exist "build\GameManager" rmdir /s /q "build\GameManager"

:: Crear carpeta data si no existe
if not exist "data" mkdir data

:: Generar ejecutable
echo [3/4] Compilando (puede tardar 1-2 minutos)...
python -m PyInstaller game_manager.spec --noconfirm
if errorlevel 1 (
    echo [ERROR] Fallo al compilar.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Ejecutable listo en:
echo   dist\GameManager\GameManager.exe
echo ============================================

:: Intentar generar instalador con Inno Setup si esta disponible
echo.
echo [4/4] Buscando Inno Setup para generar instalador...

set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if %ISCC%=="" (
    echo [INFO] Inno Setup no encontrado. Solo se genero el ejecutable portable.
    echo        Para crear el instalador .exe, instala Inno Setup desde:
    echo        https://jrsoftware.org/isinfo.php
    echo        y vuelve a ejecutar build.bat
) else (
    echo Generando instalador...
    if not exist "installer_output" mkdir installer_output
    %ISCC% installer.iss
    if errorlevel 1 (
        echo [WARN] Fallo al generar instalador. El ejecutable portable sigue disponible.
    ) else (
        echo.
        echo ============================================
        echo   Instalador listo en:
        echo   installer_output\GameManager_Setup_%APP_VERSION%.exe
        echo ============================================
    )
)

echo.
pause
