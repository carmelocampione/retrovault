; RetroVault Installer Script
; Inno Setup 6

#define MyAppName      "RetroVault"
#define MyAppVersion   "5.0"
#define MyAppExeName   "RetroVault.exe"
#define MyAppPublisher "RetroVault"

[Setup]
AppId={{C1E2D3F4-A5B6-4789-90AB-CDEF12345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}

; Standaard installatielocatie (gebruiker kan dit wijzigen)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Uitvoer
OutputDir=installer
OutputBaseFilename=RetroVaultSetup
SetupIconFile=

; Compressie (kleiner installatiebestand)
Compression=lzma2/max
SolidCompression=yes
DiskSpanning=no

; Uiterlijk
WizardStyle=modern
WizardSizePercent=120

; Alleen 64-bit Windows
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Geen beheerdersrechten nodig (werkt ook op USB)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableDirPage=no

[Languages]
Name: "dutch";   MessagesFile: "compiler:Languages\Dutch.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
  Description: "Snelkoppeling aanmaken op het bureaublad"; \
  GroupDescription: "Extra opties:"

[Files]
; ── Hoofdapplicatie (onedir: map met losse bestanden, geen packed exe) ────────
Source: "dist\RetroVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; ── Assets (iconen, achtergronden, covers) ───────────────────────────────────
Source: "assets\icons\*";       DestDir: "{app}\assets\icons";       Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\backgrounds\*"; DestDir: "{app}\assets\backgrounds"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\covers\*";      DestDir: "{app}\assets\covers";      Flags: ignoreversion recursesubdirs createallsubdirs

; ── Config (alleen installeren als het nog niet bestaat, anders bewaart gebruiker zijn config) ──
Source: "config\consoles.json"; DestDir: "{app}\config"; Flags: onlyifdoesntexist

; ── Emulators ─────────────────────────────────────────────────────────────────
Source: "emulators\*"; DestDir: "{app}\emulators"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; ── ROM-mappenstructuur (leeg, klaar voor gebruik) ───────────────────────────
Name: "{app}\roms\nes"
Name: "{app}\roms\snes"
Name: "{app}\roms\n64"
Name: "{app}\roms\gamecube"
Name: "{app}\roms\wii"
Name: "{app}\roms\wiiu"
Name: "{app}\roms\switch"
Name: "{app}\roms\gb"
Name: "{app}\roms\gbc"
Name: "{app}\roms\gba"
Name: "{app}\roms\nds"
Name: "{app}\roms\megadrive"
Name: "{app}\roms\dreamcast"
Name: "{app}\roms\ps1"
Name: "{app}\roms\ps2"
Name: "{app}\roms\ps3"
Name: "{app}\roms\psp"

; ── Config map (RetroVault maakt hier consoles.json aan) ─────────────────────
Name: "{app}\config"


[Icons]
; Startmenu
Name: "{group}\{#MyAppName}";               Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} verwijderen";   Filename: "{uninstallexe}"

; Bureaublad (optioneel, standaard aangevinkt)
Name: "{autodesktop}\{#MyAppName}"; \
  Filename: "{app}\{#MyAppExeName}"; \
  Tasks: desktopicon

[Run]
; Optie om RetroVault direct na installatie te starten
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{#MyAppName} nu starten"; \
  Flags: nowait postinstall skipifsilent
