"""
ui/screen_home.py
Hoofdscherm met horizontale carrousel van consoles.
Menu en Afsluiten zijn de laatste twee tiles in de carrousel,
zodat ze ook met een controller bereikbaar zijn.
"""

import pygame
import os

from input.controller import (
    ACTION_LEFT, ACTION_RIGHT, ACTION_SELECT,
    ACTION_MENU, ACTION_QUIT
)


# ── Kleuren (retro dark theme) ─────────────────────────────────────────────────
COLOR_BG          = (10,  10,  18)
COLOR_TILE        = (22,  22,  38)
COLOR_TILE_SEL    = (30,  40,  80)
COLOR_BORDER      = (60,  80, 180)
COLOR_TEXT        = (220, 220, 240)
COLOR_TEXT_DIM    = (100, 100, 130)
COLOR_ACCENT      = (80, 160, 255)

# ── Transparante kleuren voor tegels ───────────────────────────────────────────
COLOR_TILE_ALPHA        = (22,  22,  38, 180)  # 70% transparant
COLOR_TILE_SEL_ALPHA    = (30,  40,  80, 220)  # 85% transparant



# ── Tile afmetingen ────────────────────────────────────────────────────────────
TILE_W      = 280
TILE_H      = 240
TILE_GAP    = 30
TILE_RADIUS = 12

# ── Speciale tile-IDs ──────────────────────────────────────────────────────────
TILE_ID_MENU = "__menu__"
TILE_ID_QUIT = "__quit__"


def _load_image_safe(path: str, size: tuple):
    if path and os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except Exception:
            pass
    return None


def _draw_rounded_rect(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


class ConsoleCarousel:
    """
    Horizontale carrousel.
    De laatste twee items zijn altijd de Menu- en Afsluit-tile.
    """

    def __init__(self, consoles: list, config_manager, screen_w: int, screen_h: int):
        self.cfg        = config_manager
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.selected   = 0
        self._icons     = {}
        self._offset_x  = 0.0
        self._target_x  = 0.0
        self._scroll_speed = 12.0

        # Console-tiles + vaste actie-tiles achteraan
        self._console_tiles = consoles
        self.tiles = consoles + [
            {"id": TILE_ID_MENU, "name": "Menu",       "icon": "assets/icons/menu.png"},
            {"id": TILE_ID_QUIT, "name": "Afsluiten",  "icon": "assets/icons/quit.png"},
        ]

        self._load_icons()

    # ── Iconen laden ───────────────────────────────────────────────────────────

    def _load_icons(self):
        # Laad zowel console- als actie-tile iconen
        for tile in self.tiles:
            path = self.cfg.resolve_path(tile.get("icon", ""))
            self._icons[tile["id"]] = _load_image_safe(path, (TILE_W - 40, TILE_H - 80))

    # ── Navigatie ──────────────────────────────────────────────────────────────

    def move_left(self):
        if self.selected > 0:
            self.selected -= 1
            self._update_target()

    def move_right(self):
        if self.selected < len(self.tiles) - 1:
            self.selected += 1
            self._update_target()

    def get_selected(self) -> dict:
        return self.tiles[self.selected]

    def is_action_tile(self) -> bool:
        return self.get_selected()["id"] in (TILE_ID_MENU, TILE_ID_QUIT)

    # ── Scroll ─────────────────────────────────────────────────────────────────

    def _update_target(self):
        center_x = self.screen_w // 2
        self._target_x = center_x - self.selected * (TILE_W + TILE_GAP) - TILE_W // 2

    def update(self, dt: float):
        if self._offset_x == 0.0 and self._target_x == 0.0:
            self._update_target()
            self._offset_x = self._target_x
        diff = self._target_x - self._offset_x
        self._offset_x += diff * min(self._scroll_speed * dt, 1.0)

    # ── Tekenen ────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, carousel_y: int):
        for i, tile in enumerate(self.tiles):
            tile_x = int(self._offset_x + i * (TILE_W + TILE_GAP))

            is_selected = (i == self.selected)
            scale = 1.08 if is_selected else 1.0
            tw = int(TILE_W * scale)
            th = int(TILE_H * scale)
            tx = tile_x - (tw - TILE_W) // 2
            ty = carousel_y - (th - TILE_H) // 2
            rect = pygame.Rect(tx, ty, tw, th)

            if tx + tw < -50 or tx > surface.get_width() + 50:
                continue

            tid = tile["id"]

            self._draw_console_tile(surface, tile, rect, is_selected, scale)

    def _draw_console_tile(self, surface, tile, rect, selected, scale):
        # Geen gekleurde achtergrond meer - alleen iconen en tekst
        # Alleen een selectierand tonen wanneer geselecteerd
        if selected:
            pygame.draw.rect(surface, COLOR_BORDER, rect, width=3,
                             border_radius=TILE_RADIUS)

        icon = self._icons.get(tile["id"])
        if icon:
            iw = int((TILE_W - 40) * scale)
            ih = int((TILE_H - 80) * scale)
            scaled = pygame.transform.smoothscale(icon, (iw, ih))
            surface.blit(scaled, (rect.x + (rect.w - iw) // 2, rect.y + 20))
        else:
            self._draw_placeholder(surface, tile, rect, scale)

        self._draw_label(surface, tile["name"], rect, selected)

    def _draw_placeholder(self, surface, tile, rect, scale):
        # Vaste afkorting voor actie-tiles, anders eerste letters van naam
        fixed = {TILE_ID_MENU: "ME", TILE_ID_QUIT: "AF"}
        abbr  = fixed.get(tile["id"]) or "".join(w[0] for w in tile["name"].split()[:2]).upper()

        h = hash(tile["id"]) % 360
        color = pygame.Color(0)
        color.hsva = (h, 60, 70, 100)
        inner = pygame.Rect(rect.x + 10, rect.y + 20,
                            rect.w - 20, rect.h - 70)
        _draw_rounded_rect(surface, color, inner, 8)
        font = pygame.font.SysFont("arial", int(36 * scale), bold=True)
        lbl  = font.render(abbr, True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=inner.center))

    def _draw_label(self, surface, name, rect, selected, color=None):
        if color is None:
            color = COLOR_TEXT if selected else COLOR_TEXT_DIM
        size = 18 if selected else 16
        font = pygame.font.SysFont("arial", size, bold=selected)
        display = name if len(name) <= 18 else name[:16] + "…"
        lbl = font.render(display, True, color)
        surface.blit(lbl, lbl.get_rect(centerx=rect.centerx,
                                        bottom=rect.bottom - 10))


class HomeScreen:
    """Hoofdscherm van RetroVault 5.0."""

    def __init__(self, screen: pygame.Surface, config_manager, input_handler):
        self.screen = screen
        self.cfg    = config_manager
        self.input  = input_handler
        self._bg    = None
        self._font_title = pygame.font.SysFont("arial", 32, bold=True)
        self._font_hint  = pygame.font.SysFont("arial", 14)

        self._build_carousel()
        self._load_background()

    def _build_carousel(self):
        w, h = self.screen.get_size()
        consoles = self.cfg.get_visible_consoles()
        self.carousel = ConsoleCarousel(consoles, self.cfg, w, h)

    def _load_background(self):
        path = self.cfg.resolve_path(self.cfg.settings.get("background_image", ""))
        print(f"Background path: {path}")
        if path and os.path.exists(path):
            w, h = self.screen.get_size()
            print(f"Screen size: {w}x{h}")
            try:
                img = pygame.image.load(path).convert()
                img_w, img_h = img.get_size()
                print(f"Original image size: {img_w}x{img_h}")
                
                # Bereken schaal om beeldverhouding te behouden en hele scherm te vullen
                scale_w = w / img_w
                scale_h = h / img_h
                scale = max(scale_w, scale_h)  # Gebruik grootste schaal voor full-screen coverage
                print(f"Scale factors: w={scale_w:.2f}, h={scale_h:.2f}, using={scale:.2f}")
                
                # Schaal afbeelding
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                print(f"Scaled image size: {new_w}x{new_h}")
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
                
                # Centreer de afbeelding op het scherm (crop overflow)
                x = (new_w - w) // 2
                y = (new_h - h) // 2
                print(f"Crop offset: x={x}, y={y}")
                self._bg = pygame.Surface((w, h))
                self._bg.blit(scaled_img, (-x, -y))
                print("Background loaded successfully")
            except Exception as e:
                print(f"Error loading background: {e}")
                self._bg = None
        else:
            print("No background image found")

    def reload_background(self, background_path=None):
        """Public method to reload the background (called from menu)."""
        print("Reloading background...")
        if background_path is not None:
            # Update the settings with the new path before reloading
            self.cfg.settings["background_image"] = background_path
            self.cfg.save_settings()
        self._load_background()

    def update(self, dt: float):
        actions = self.input.consume_actions()

        for action in actions:
            if action == ACTION_LEFT:
                self.carousel.move_left()

            elif action == ACTION_RIGHT:
                self.carousel.move_right()

            elif action == ACTION_SELECT:
                tile = self.carousel.get_selected()
                tid  = tile["id"]

                if tid == TILE_ID_QUIT:
                    return "QUIT"

                elif tid == TILE_ID_MENU:
                    from ui.screen_menu import MenuScreen
                    return MenuScreen(self.screen, self.cfg, self.input,
                                      parent_screen=self)

                else:
                    from ui.screen_library import LibraryScreen
                    return LibraryScreen(
                        self.screen, self.cfg, self.input,
                        tile, parent_screen=self
                    )

            # Keyboard-shortcuts blijven werken (handig zonder controller)
            elif action == ACTION_MENU:
                from ui.screen_menu import MenuScreen
                return MenuScreen(self.screen, self.cfg, self.input,
                                  parent_screen=self)

            elif action == ACTION_QUIT:
                return "QUIT"

        self.carousel.update(dt)
        return None

    def draw(self):
        w, h = self.screen.get_size()
        
        # Controleer of schermgrootte is veranderd en laad achtergrond opnieuw indien nodig
        if not hasattr(self, '_last_screen_size'):
            self._last_screen_size = (w, h)
        elif self._last_screen_size != (w, h):
            self._last_screen_size = (w, h)
            print(f"Screen size changed to {w}x{h}, reloading background")
            self._load_background()

        # Achtergrond
        if self._bg:
            self.screen.blit(self._bg, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(COLOR_BG)
            self._draw_bg_pattern()

        # Titel
        title_lbl = self._font_title.render("RetroVault 5.0", True, COLOR_ACCENT)
        self.screen.blit(title_lbl, (30, 20))

        # Carrousel
        carousel_y = h // 2 - TILE_H // 2
        self.carousel.draw(self.screen, carousel_y)

        # Naam van geselecteerde tile onderaan
        sel = self.carousel.get_selected()
        if sel["id"] not in (TILE_ID_MENU, TILE_ID_QUIT):
            name_lbl = self._font_title.render(sel["name"], True, COLOR_TEXT)
            self.screen.blit(name_lbl, name_lbl.get_rect(centerx=w // 2, y=h - 80))

        # Hint
        hints = "← → Navigeren   Enter Selecteren   M Menu   Q Afsluiten"
        hint_lbl = self._font_hint.render(hints, True, COLOR_TEXT_DIM)
        self.screen.blit(hint_lbl, hint_lbl.get_rect(centerx=w // 2, bottom=h - 10))

    def _draw_bg_pattern(self):
        w, h = self.screen.get_size()
        for x in range(0, w, 60):
            pygame.draw.line(self.screen, (20, 20, 35), (x, 0), (x, h))
        for y in range(0, h, 60):
            pygame.draw.line(self.screen, (20, 20, 35), (0, y), (w, y))
