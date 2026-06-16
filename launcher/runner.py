"""
launcher/runner.py
Start een emulator-proces voor een gegeven game.
Gebouwd voor uitbreiding: later kunnen we logging, pre/post hooks toevoegen.
"""

import subprocess
import os
import shlex
import logging

logger = logging.getLogger("retrovault.launcher")


class GameLauncher:
    """
    Verantwoordelijk voor het opstarten van emulators.
    Alle paden worden relatief aan base_dir opgezet (portabiliteit).
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._process = None  # Huidig actief emulator-proces

    def launch(self, console: dict, game: dict) -> bool:
        """
        Start de emulator voor de gegeven game.

        Args:
            console: Console-dict uit consoles.json
            game:    Game-dict uit consoles.json

        Returns:
            True als het starten gelukt is, False anders.
        """
        cmd_template = console.get("emulator_cmd", "")
        rom_path     = game.get("rom", "")

        if not cmd_template:
            logger.error(f"Geen emulator_cmd voor console: {console['id']}")
            return False

        # Zet relatief pad om naar absoluut
        if not os.path.isabs(rom_path):
            rom_path = os.path.join(self.base_dir, rom_path)

        if not os.path.exists(rom_path):
            logger.warning(f"ROM niet gevonden: {rom_path}")
            # In development: toch proberen (handig voor testen)

        # Bouw het commando: {rom} wordt vervangen door het rom-pad
        # Als {rom} niet in cmd staat, voegen we het aan het einde toe
        if "{rom}" in cmd_template:
            full_cmd = cmd_template.replace("{rom}", rom_path)
        else:
            full_cmd = f'{cmd_template} {rom_path}'

        logger.info(f"Starten: {full_cmd}")

        try:
            # Bouw commando parts handmatig voor Windows
            parts = cmd_template.split()
            parts.append(rom_path)
            
            # Gebruik subprocess met shell=True en absolute paden
            # Converteer relatieve paden naar absolute paden
            absolute_parts = []
            for part in parts:
                if part.endswith('.exe') and not os.path.isabs(part):
                    # Dit is de emulator - maak absoluut pad
                    abs_part = os.path.join(self.base_dir, part)
                    absolute_parts.append(f'"{abs_part}"')
                elif part.endswith('.dll') and not os.path.isabs(part):
                    # Dit is een core - maak absoluut pad
                    abs_part = os.path.join(self.base_dir, part)
                    absolute_parts.append(f'"{abs_part}"')
                else:
                    absolute_parts.append(f'"{part}"')
            
            full_cmd_string = ' '.join(absolute_parts)
            print(f"[LAUNCHER] Command: {full_cmd_string}")
            
            # Controleer of bestanden bestaan
            emulator_path = os.path.join(self.base_dir, parts[0])
            core_path = None
            for part in parts:
                if part.endswith('.dll') and not os.path.isabs(part):
                    core_path = os.path.join(self.base_dir, part)
                    break
            
            print(f"[LAUNCHER] Emulator exists: {os.path.exists(emulator_path)} - {emulator_path}")
            if core_path:
                print(f"[LAUNCHER] Core exists: {os.path.exists(core_path)} - {core_path}")
            print(f"[LAUNCHER] ROM exists: {os.path.exists(rom_path)} - {rom_path}")
            
            # Voeg --fullscreen=false toe voor zichtbaarheid
            if '--fullscreen=false' not in full_cmd_string:
                full_cmd_string += ' --fullscreen=false'
                print(f"[LAUNCHER] Updated Command: {full_cmd_string}")
            
            self._process = subprocess.Popen(
                full_cmd_string,
                cwd=self.base_dir,
                shell=True,
            )
            print(f"[LAUNCHER] Process started with PID: {self._process.pid}")
            
            # Wacht even om te zien of het proces blijft draaien
            import time
            time.sleep(0.5)
            if self._process.poll() is not None:
                print(f"[LAUNCHER] Process exited with code: {self._process.returncode}")
            else:
                print(f"[LAUNCHER] Process is running")
            
            return True
        except FileNotFoundError as e:
            logger.error(f"Emulator niet gevonden: {e}")
            print(f"[LAUNCHER] FOUT: emulator niet gevonden – {e}")
            return False
        except Exception as e:
            logger.error(f"Starten mislukt: {e}")
            print(f"[LAUNCHER] FOUT: {e}")
            return False

    def is_running(self) -> bool:
        """Check of het emulator-proces nog actief is."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def stop(self):
        """Beëindig het actieve emulator-proces (forceer als nodig)."""
        if self._process and self.is_running():
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
