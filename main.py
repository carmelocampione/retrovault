"""
RetroVault 5.0 - Main Entry Point
"""

import pygame
import sys
import os

# Wanneer de app als PyInstaller-exe draait, staat BASE_DIR bij de exe.
# In development staat BASE_DIR bij main.py.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config.config_manager import ConfigManager
from input.controller import InputHandler
from ui.screen_home import HomeScreen

# ── Constants ──────────────────────────────────────────────────────────────────
WINDOW_TITLE = "RetroVault 5.0"
TARGET_FPS   = 60


# Global variables for fullscreen toggle
is_fullscreen = True

def main():
    global is_fullscreen
    pygame.init()
    pygame.joystick.init()

    # Detect connected controllers
    joysticks = {}

    def _init_joystick(index: int):
        js = pygame.joystick.Joystick(index)
        js.init()
        joysticks[js.get_instance_id()] = js
        print(f"[INPUT] Controller gevonden: {js.get_name()}")
        print(f"[INPUT]   Assen: {js.get_numaxes()}  "
              f"Knoppen: {js.get_numbuttons()}  "
              f"Hats: {js.get_numhats()}")

    for i in range(pygame.joystick.get_count()):
        _init_joystick(i)

    if not joysticks:
        print("[INPUT] Geen controller gevonden – alleen toetsenbord actief.")

    # Window setup – start in fullscreen mode
    # Use the best available display mode to avoid black bars
    modes = pygame.display.list_modes()
    if modes:
        screen = pygame.display.set_mode(modes[0], pygame.FULLSCREEN)
    else:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption(WINDOW_TITLE)

    clock          = pygame.time.Clock()
    config_manager = ConfigManager(BASE_DIR)
    input_handler  = InputHandler()

    # Scan alle ROM-mappen bij opstarten (voegt nieuwe ROMs toe, raakt bestaande niet aan)
    config_manager.scan_all_roms()

    # Active screen – start on HomeScreen
    active_screen = HomeScreen(screen, config_manager, input_handler)

    # ── Main loop ──────────────────────────────────────────────────────────────
    running = True
    while running:
        dt     = clock.tick(TARGET_FPS) / 1000.0  # delta time in seconds
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.JOYDEVICEADDED:
                _init_joystick(event.device_index)
            elif event.type == pygame.JOYDEVICEREMOVED:
                joysticks.pop(event.instance_id, None)
                print(f"[INPUT] Controller losgekoppeld (id={event.instance_id})")

        # Feed events to input handler (alleen als scherm geen raw input nodig heeft)
        needs_raw = hasattr(active_screen, 'needs_raw_input') and active_screen.needs_raw_input()
        if not needs_raw:
            input_handler.process_events(events)

        # Update + draw active screen
        if needs_raw:
            next_screen = active_screen.update(dt, events)
        else:
            next_screen = active_screen.update(dt)
        if next_screen == "QUIT":
            running = False
        elif next_screen is not None:
            active_screen = next_screen
            # Als we terugkeren naar HomeScreen, herbouw de carrousel
            # zodat menu-wijzigingen (volgorde, zichtbaarheid) meteen zichtbaar zijn
            if hasattr(active_screen, "_build_carousel"):
                active_screen._build_carousel()
            # Als we terugkeren naar LibraryScreen, herlaad covers
            # zodat nieuw gescrapete artwork direct zichtbaar is
            if hasattr(active_screen, "refresh_covers"):
                active_screen.refresh_covers()

        active_screen.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
