# Portable Emulators Map

Deze map bevat alle emulators voor RetroVault portable USB stick installatie.

## Map Structuur
```
emulators/
├── retroarch/      # RetroArch met cores
├── dolphin/        # Dolphin (GameCube/Wii)
├── cemu/           # Cemu (Wii U)
├── yuzu/           # Yuzu (Nintendo Switch)
├── pcsx2/          # PCSX2 (PlayStation 2)
├── rpcs3/          # RPCS3 (PlayStation 3)
└── ppsspp/         # PPSSPP (PlayStation Portable)
```

## Installatie Instructies

### 1. RetroArch
- Download: https://www.retroarch.com/
- Kopieer de volledige RetroArch map naar `emulators/retroarch/`
- Download cores via RetroArch's Online Updater:
  - `nestopia_libretro.dll` (NES)
  - `snes9x_libretro.dll` (SNES)
  - `mupen64plus_libretro.dll` (N64)
  - `gambatte_libretro.dll` (GB/GBC)
  - `mgba_libretro.dll` (GBA)
  - `desmume_libretro.dll` (NDS)
  - `genesis_plus_gx_libretro.dll` (Mega Drive)
  - `flycast_libretro.dll` (Dreamcast)
  - `mednafen_psx_libretro.dll` (PS1)

### 2. Dolphin
- Download: https://dolphin-emu.org/
- Kopieer `Dolphin.exe` en benodigde bestanden naar `emulators/dolphin/`

### 3. Cemu
- Download: https://cemu.info/
- Kopieer `Cemu.exe` en benodigde bestanden naar `emulators/cemu/`

### 4. Yuzu
- Download: https://yuzu-emu.org/
- Kopieer `yuzu.exe` en benodigde bestanden naar `emulators/yuzu/`

### 5. PCSX2
- Download: https://pcsx2.net/
- Kopieer `pcsx2-qt.exe` en benodigde bestanden naar `emulators/pcsx2/`

### 6. RPCS3
- Download: https://rpcs3.net/
- Kopieer `rpcs3.exe` en benodigde bestanden naar `emulators/rpcs3/`

### 7. PPSSPP
- Download: https://www.ppsspp.org/
- Kopieer `ppsspp.exe` en benodigde bestanden naar `emulators/ppsspp/`

## Gebruik
Na installatie:
1. Start RetroVault
2. Alle emulator paden zijn al geconfigureerd als relatieve paden
3. De hele applicatie is nu portable en werkt vanaf elke USB stick

## Opmerkingen
- Zorg dat alle emulators portable versies zijn (geen installatie nodig)
- RetroArch cores worden automatisch geladen vanuit de `cores/` map
- Configuratie bestanden worden per emulator in hun eigen mappen opgeslagen
