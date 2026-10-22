; ============================================================
;  Game Manager — Inno Setup Script
;  Requiere Inno Setup 6.x  https://jrsoftware.org/isinfo.php
;
;  Para compilar: abre este archivo en Inno Setup IDE y
;  presiona Ctrl+F9, o ejecuta:
;    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; ============================================================

#define AppName      "Game Manager"
; Mantener AppVersion igual que version.py
#define AppVersion   "1.1.0"
#define AppPublisher "Souto751"
#define AppURL       "https://github.com/Souto751/game-manager"
#define AppExeName   "GameManager.exe"
#define BuildDir     "dist\GameManager"

[Setup]
AppId={{A3F7B2C1-4E8D-4F2A-9C6B-1D5E3A7F9B2C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Installer output
OutputDir=installer_output
OutputBaseFilename=GameManager_Setup_{#AppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Appearance
WizardStyle=modern
WizardSizePercent=120
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
; Instalacion por usuario (sin admin): {autopf} apunta a %LOCALAPPDATA%\Programs.
; Los datos del usuario viven en %APPDATA%\GameManager y no se tocan al actualizar.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Windows 10+ only
MinVersion=10.0

[Languages]
Name: "spanish";    MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english";    MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Crear icono en el Escritorio";    GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "startmenuicon"; Description: "Crear acceso directo en Menu Inicio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
; Main application (entire PyInstaller output folder)
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
; Desktop
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove user data only if present and user chose to (can add a [Code] section for this)
; Type: filesandordirs; Name: "{userappdata}\GameManager"

[Code]
// Show a "What's new" link after installation finishes
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
    WizardForm.FinishedLabel.Caption :=
      'La instalacion fue exitosa.' + #13#10 + #13#10 +
      'Repositorio: https://github.com/Souto751/game-manager';
end;
