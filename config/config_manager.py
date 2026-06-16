"""
config/config_manager.py
Loads and saves all JSON config files. Single source of truth for app state.
Bevat ook de ROM-scanner: scant roms_path per console en voegt nieuwe games toe.
"""

import json
import os
import re


DEFAULT_SETTINGS = {
    "background_image": "",
    "fullscreen": False,
    "server_url": "",
    "download_path": "downloads/",
    "igdb_client_id": "",
    "igdb_client_secret": ""
}

DEFAULT_CONSOLES = [
    # ── Nintendo ───────────────────────────────────────────────────────────────
    {
        "id": "nes",
        "name": "Nintendo NES",
        "icon": "assets/icons/nes.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/nestopia_libretro.dll",
        "roms_path": "roms/nes/",
        "rom_extensions": [".nes", ".zip"],
        "games": []
    },
    {
        "id": "snes",
        "name": "Super Nintendo",
        "icon": "assets/icons/snes.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/snes9x_libretro.dll",
        "roms_path": "roms/snes/",
        "rom_extensions": [".smc", ".sfc", ".zip"],
        "games": []
    },
    {
        "id": "n64",
        "name": "Nintendo 64",
        "icon": "assets/icons/n64.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/mupen64plus_libretro.dll",
        "roms_path": "roms/n64/",
        "rom_extensions": [".z64", ".n64", ".v64", ".zip"],
        "games": []
    },
    {
        "id": "gamecube",
        "name": "GameCube",
        "icon": "assets/icons/gamecube.png",
        "visible": True,
        "emulator_cmd": "Dolphin.exe -e",
        "roms_path": "roms/gamecube/",
        "rom_extensions": [".iso", ".rvz", ".gcm", ".gcz", ".ciso",".7z"],
        "games": []
    },
    {
        "id": "wii",
        "name": "Nintendo Wii",
        "icon": "assets/icons/wii.png",
        "visible": True,
        "emulator_cmd": "Dolphin.exe -e",
        "roms_path": "roms/wii/",
        "rom_extensions": [".iso", ".rvz", ".wbfs", ".gcz", ".ciso"],
        "games": []
    },
    {
        "id": "wiiu",
        "name": "Nintendo Wii U",
        "icon": "assets/icons/wiiu.png",
        "visible": True,
        "emulator_cmd": "Cemu.exe -g",
        "roms_path": "roms/wiiu/",
        "rom_extensions": [".rpx", ".wud", ".wux", ".iso"],
        "games": []
    },
    {
        "id": "switch",
        "name": "Nintendo Switch",
        "icon": "assets/icons/switch.png",
        "visible": True,
        "emulator_cmd": "yuzu.exe",
        "roms_path": "roms/switch/",
        "rom_extensions": [".nsp", ".xci", ".nca"],
        "games": []
    },
    {
        "id": "gb",
        "name": "Game Boy",
        "icon": "assets/icons/gb.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/gambatte_libretro.dll",
        "roms_path": "roms/gb/",
        "rom_extensions": [".gb", ".zip"],
        "games": []
    },
    {
        "id": "gbc",
        "name": "Game Boy Color",
        "icon": "assets/icons/gbc.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/gambatte_libretro.dll",
        "roms_path": "roms/gbc/",
        "rom_extensions": [".gbc", ".zip"],
        "games": []
    },
    {
        "id": "gba",
        "name": "Game Boy Advance",
        "icon": "assets/icons/gba.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/mgba_libretro.dll",
        "roms_path": "roms/gba/",
        "rom_extensions": [".gba", ".zip"],
        "games": []
    },
    {
        "id": "nds",
        "name": "Nintendo DS",
        "icon": "assets/icons/nds.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/desmume_libretro.dll",
        "roms_path": "roms/nds/",
        "rom_extensions": [".nds", ".zip"],
        "games": []
    },
    # ── Sega ───────────────────────────────────────────────────────────────────
    {
        "id": "megadrive",
        "name": "Sega Mega Drive",
        "icon": "assets/icons/megadrive.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/genesis_plus_gx_libretro.dll",
        "roms_path": "roms/megadrive/",
        "rom_extensions": [".md", ".bin", ".gen", ".zip"],
        "games": []
    },
    {
        "id": "dreamcast",
        "name": "Sega Dreamcast",
        "icon": "assets/icons/dreamcast.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/flycast_libretro.dll",
        "roms_path": "roms/dreamcast/",
        "rom_extensions": [".cdi", ".gdi", ".chd", ".iso"],
        "games": []
    },
    # ── Sony ───────────────────────────────────────────────────────────────────
    {
        "id": "ps1",
        "name": "PlayStation 1",
        "icon": "assets/icons/ps1.png",
        "visible": True,
        "emulator_cmd": "retroarch -L cores/mednafen_psx_libretro.dll",
        "roms_path": "roms/ps1/",
        "rom_extensions": [".bin", ".cue", ".iso", ".pbp", ".chd"],
        "games": []
    },
    {
        "id": "ps2",
        "name": "PlayStation 2",
        "icon": "assets/icons/ps2.png",
        "visible": True,
        "emulator_cmd": "pcsx2-qt.exe",
        "roms_path": "roms/ps2/",
        "rom_extensions": [".iso", ".bin", ".chd", ".cso"],
        "games": []
    },
    {
        "id": "ps3",
        "name": "PlayStation 3",
        "icon": "assets/icons/ps3.png",
        "visible": True,
        "emulator_cmd": "rpcs3.exe",
        "roms_path": "roms/ps3/",
        "rom_extensions": [".pkg", ".iso"],
        "games": []
    },
    {
        "id": "psp",
        "name": "PlayStation Portable",
        "icon": "assets/icons/psp.png",
        "visible": True,
        "emulator_cmd": "ppsspp.exe",
        "roms_path": "roms/psp/",
        "rom_extensions": [".iso", ".cso", ".pbp", ".chd"],
        "games": []
    },
]


def _clean_name(filename: str) -> str:
    """
    Zet bestandsnaam om naar leesbare gamenaam.
      "super_mario_world_(USA)[!].smc"  ->  "Super Mario World"
      "Contra (Europe).nes"             ->  "Contra"
    """
    name = os.path.splitext(filename)[0]
    name = re.sub(r"\s*[\(\[].*?[\)\]]", "", name)   # verwijder (USA), [!], etc.
    name = name.replace("_", " ").replace(".", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name.title()


def _get_wiiu_game_name(full_path: str, filename: str) -> str:
    """
    Extraheer de game naam voor Wii U spellen uit de directory structuur.
    Voor WiiU spellen staat de echte naam in de parent directory.
    """
    # Get the parent directory of the RPX file
    parent_dir = os.path.basename(os.path.dirname(full_path))
    
    # If we're in a code/ subdirectory, get the directory above that
    if parent_dir == "code":
        game_dir = os.path.basename(os.path.dirname(os.path.dirname(full_path)))
    else:
        game_dir = parent_dir
    
    # Extract game name from directory (remove [Game] and ID tags)
    game_name = re.sub(r"\s*\[Game\].*", "", game_dir)
    game_name = re.sub(r"\s*\[\d+\].*", "", game_name)  # remove [0005000010138300] etc.
    game_name = game_name.strip()
    
    return game_name if game_name else _clean_name(filename)


def _make_game_id(console_id: str, filename: str) -> str:
    """Stabiel uniek ID: console_id + genormaliseerde bestandsnaam."""
    base = os.path.splitext(filename)[0].lower()
    base = re.sub(r"[^a-z0-9]", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return f"{console_id}_{base}"


class RomScanner:
    """Scant een map op ROM-bestanden en voegt nieuwe toe aan een console-dict."""

    def scan_console(self, console: dict, base_dir: str) -> tuple:
        """
        Scant roms_path van een console.
        Bestaande games blijven intact (geen duplicaten).
        Geeft (nieuw_toegevoegd, totaal) terug.
        """
        roms_path  = console.get("roms_path", "")
        extensions = set(console.get("rom_extensions", []))
        if not roms_path or not extensions:
            return 0, len(console.get("games", []))

        abs_path = os.path.join(base_dir, roms_path)
        if not os.path.isdir(abs_path):
            return 0, len(console.get("games", []))

        # Index op genormaliseerd rom-pad
        existing = {
            os.path.normpath(g["rom"]): True
            for g in console.get("games", [])
        }

        added = 0
        for root, dirs, files in os.walk(abs_path):
            for filename in sorted(files):
                ext = os.path.splitext(filename)[1].lower()
                if ext not in extensions:
                    continue

                # Get relative path from base roms_path
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, base_dir)
                rel_rom = rel_path.replace("\\", "/")
                norm    = os.path.normpath(rel_rom)

                if norm not in existing:
                    # Use special name extraction for Wii U games
                    if console["id"] == "wiiu":
                        game_name = _get_wiiu_game_name(full_path, filename)
                    else:
                        game_name = _clean_name(filename)
                    
                    console.setdefault("games", []).append({
                        "id":    _make_game_id(console["id"], filename),
                        "name":  game_name,
                        "rom":   rel_rom,
                        "cover": ""
                        # "rom_in_zip": ""  # Optioneel: pad binnen de ZIP als RetroArch
                        #                   # niet automatisch de juiste ROM kiest.
                        #                   # Bijv: "Super Mario Advance (USA).gba"
                    })
                    existing[norm] = True
                    added += 1

        return added, len(console.get("games", []))


class ConfigManager:
    """
    Beheert alle config-bestanden.
    Alle paden zijn relatief aan base_dir (portable!).
    """

    def __init__(self, base_dir: str):
        self.base_dir    = base_dir
        self.config_dir  = os.path.join(base_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)

        self.settings_path = os.path.join(self.config_dir, "settings.json")
        self.consoles_path = os.path.join(self.config_dir, "consoles.json")

        self.settings = self._load_or_create(self.settings_path, DEFAULT_SETTINGS)
        self.consoles = self._load_or_create(self.consoles_path, DEFAULT_CONSOLES)
        self._scanner = RomScanner()

    def _load_or_create(self, path: str, default):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default

    def save_settings(self):
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)

    def save_consoles(self):
        with open(self.consoles_path, "w", encoding="utf-8") as f:
            json.dump(self.consoles, f, indent=2, ensure_ascii=False)

    def get_visible_consoles(self) -> list:
        return [c for c in self.consoles if c.get("visible", True)]

    def resolve_path(self, relative: str) -> str:
        if not relative:
            return ""
        if os.path.isabs(relative):
            return relative
        return os.path.join(self.base_dir, relative)

    # ── ROM-scanner ────────────────────────────────────────────────────────────

    def scan_all_roms(self) -> dict:
        """
        Scant alle consoles bij opstarten.
        Geeft {console_naam: (nieuw, totaal)} terug.
        """
        results = {}
        dirty   = False
        for console in self.consoles:
            added, total = self._scanner.scan_console(console, self.base_dir)
            results[console["name"]] = (added, total)
            if added > 0:
                dirty = True
                print(f"[SCAN] {console['name']}: +{added} ROM(s)  ({total} totaal)")
        if dirty:
            self.save_consoles()
        return results

    def scan_console(self, console: dict) -> tuple:
        """Scant één console (vanuit menu). Slaat op bij nieuwe ROMs."""
        added, total = self._scanner.scan_console(console, self.base_dir)
        if added > 0:
            self.save_consoles()
        return added, total

    def set_roms_path(self, console: dict, new_path: str) -> tuple:
        """Stel een nieuwe roms_path in en scan meteen."""
        try:
            rel = os.path.relpath(new_path, self.base_dir)
        except ValueError:
            rel = new_path
        if not rel.endswith(("/", "\\")):
            rel += "/"
        console["roms_path"] = rel.replace("\\", "/")
        self.save_consoles()
        return self.scan_console(console)
