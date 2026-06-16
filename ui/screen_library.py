"""
ui/screen_library.py
Gamebibliotheek voor één console.
Grid met cover art, navigeerbaar via keyboard en controller.
"""

import pygame
import os

from input.controller import (
    ACTION_LEFT, ACTION_RIGHT, ACTION_UP, ACTION_DOWN,
    ACTION_SELECT, ACTION_BACK, ACTION_MENU
)

# ── Kleuren ────────────────────────────────────────────────────────────────────
COLOR_BG        = (10,  10,  18)
COLOR_TILE      = (22,  22,  38)
COLOR_TILE_SEL  = (30,  40,  80)
COLOR_BORDER    = (60,  80, 180)
COLOR_TEXT      = (220, 220, 240)
COLOR_TEXT_DIM  = (100, 100, 130)
COLOR_ACCENT    = (80, 160, 255)
COLOR_OVERLAY   = (0,   0,   0, 160)

# ── Grid instellingen ──────────────────────────────────────────────────────────
COLS        = 5      # Aantal kolommen
COVER_W     = 160
COVER_H     = 200
TILE_PAD    = 16     # Padding binnen tile
TILE_W      = COVER_W + TILE_PAD * 2
TILE_H      = COVER_H + TILE_PAD * 2 + 28   # +28 voor label
GAP_X       = 20
GAP_Y       = 20
TILE_RADIUS = 10
GRID_TOP    = 100    # Y-start van het grid (ruimte voor header)


def _load_cover(path: str) -> pygame.Surface | None:
    if path and os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, (COVER_W, COVER_H))
        except Exception:
            pass
    return None


def _draw_rr(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


class GameGrid:
    """
    Scrollbaar grid van game-tiles.
    Navigatie: links/rechts/omhoog/omlaag.
    """

    def __init__(self, games: list, config_manager, screen_w: int, screen_h: int):
        self.games      = games
        self.cfg        = config_manager
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.selected   = 0
        self._covers    = {}
        self._scroll_y  = 0.0       # Huidige scroll (pixels)
        self._target_y  = 0.0       # Doel scroll
        self._scroll_spd = 10.0

        self._load_covers()
        self._compute_layout()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _load_covers(self):
        for game in self.games:
            path = self.cfg.resolve_path(game.get("cover", ""))
            self._covers[game["id"]] = _load_cover(path)

    def _compute_layout(self):
        """Bereken x/y positie van elke tile op basis van index."""
        total_w = COLS * TILE_W + (COLS - 1) * GAP_X
        self._grid_left = (self.screen_w - total_w) // 2
        self._positions = []
        for i in range(len(self.games)):
            col = i % COLS
            row = i // COLS
            x   = self._grid_left + col * (TILE_W + GAP_X)
            y   = GRID_TOP + row * (TILE_H + GAP_Y)
            self._positions.append((x, y))

    def refresh_covers(self):
        """Herlaad alle covers opnieuw (na scrapen of cover-wijziging)."""
        self._covers = {}
        self._load_covers()

    # ── Navigatie ──────────────────────────────────────────────────────────────

    def move(self, direction: str):
        n = len(self.games)
        if n == 0:
            return
        if direction == ACTION_LEFT  and self.selected % COLS > 0:
            self.selected -= 1
        elif direction == ACTION_RIGHT and self.selected % COLS < COLS - 1 and self.selected + 1 < n:
            self.selected += 1
        elif direction == ACTION_UP   and self.selected - COLS >= 0:
            self.selected -= COLS
        elif direction == ACTION_DOWN and self.selected + COLS < n:
            self.selected += COLS
        self._update_scroll()

    def get_selected_game(self) -> dict | None:
        if not self.games:
            return None
        return self.games[self.selected]

    # ── Scroll ─────────────────────────────────────────────────────────────────

    def _update_scroll(self):
        """Scroll zodat de geselecteerde tile altijd zichtbaar is."""
        if not self._positions:
            return
        _, ty = self._positions[self.selected]
        visible_h = self.screen_h - GRID_TOP - 40
        # Scroll naar beneden als tile onder de rand valt
        if ty - self._target_y + TILE_H > visible_h:
            self._target_y = ty + TILE_H - visible_h
        # Scroll naar boven als tile boven de rand valt
        if ty - self._target_y < 0:
            self._target_y = ty

    def update(self, dt: float):
        diff = self._target_y - self._scroll_y
        self._scroll_y += diff * min(self._scroll_spd * dt, 1.0)

    # ── Tekenen ────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, font_name: pygame.font.Font,
             font_label: pygame.font.Font):
        # Clip-region zodat tiles niet boven de header scrollen
        clip = pygame.Rect(0, GRID_TOP, self.screen_w, self.screen_h - GRID_TOP)
        surface.set_clip(clip)

        for i, game in enumerate(self.games):
            bx, by = self._positions[i]
            draw_y  = int(by - self._scroll_y)

            # Buiten scherm? Overslaan
            if draw_y + TILE_H < GRID_TOP or draw_y > self.screen_h:
                continue

            is_sel  = (i == self.selected)
            rect    = pygame.Rect(bx, draw_y, TILE_W, TILE_H)
            bg      = COLOR_TILE_SEL if is_sel else COLOR_TILE
            _draw_rr(surface, bg, rect, TILE_RADIUS)

            if is_sel:
                pygame.draw.rect(surface, COLOR_BORDER, rect,
                                 width=3, border_radius=TILE_RADIUS)

            # Cover art
            cover = self._covers.get(game["id"])
            cover_rect = pygame.Rect(bx + TILE_PAD, draw_y + TILE_PAD, COVER_W, COVER_H)
            if cover:
                surface.blit(cover, cover_rect)
            else:
                self._draw_cover_placeholder(surface, game, cover_rect, is_sel)

            # Game naam
            name    = game["name"]
            display = name if len(name) <= 18 else name[:16] + "…"
            color   = COLOR_TEXT if is_sel else COLOR_TEXT_DIM
            lbl     = font_label.render(display, True, color)
            lbl_rect = lbl.get_rect(
                centerx=rect.centerx,
                bottom=rect.bottom - 6
            )
            surface.blit(lbl, lbl_rect)

        surface.set_clip(None)

    def _draw_cover_placeholder(self, surface, game, rect, selected):
        """Gekleurde placeholder met afgekorte naam als er geen cover is."""
        h = hash(game["id"]) % 360
        c = pygame.Color(0)
        c.hsva = (h, 55, 55, 100)
        _draw_rr(surface, c, rect, 6)
        abbr = "".join(w[0] for w in game["name"].split()[:3]).upper()
        font = pygame.font.SysFont("arial", 28, bold=True)
        lbl  = font.render(abbr, True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=rect.center))


class LibraryScreen:
    """
    Gamebibliotheek van één console.
    Toont een grid van games met cover art.
    """

    def __init__(self, screen: pygame.Surface, config_manager,
                 input_handler, console: dict, parent_screen):
        self.screen  = screen
        self.cfg     = config_manager
        self.input   = input_handler
        self.console = console
        self.parent  = parent_screen   # Terug naar HomeScreen

        self._font_title = pygame.font.SysFont("arial", 28, bold=True)
        self._font_label = pygame.font.SysFont("arial", 13)
        self._font_hint  = pygame.font.SysFont("arial", 14)
        self._bg         = None

        w, h = screen.get_size()
        self.grid = GameGrid(console.get("games", []), config_manager, w, h)
        self._load_background()

    def refresh_covers(self):
        # Sync de spellenlijst vanuit de actuele console-config
        for c in self.cfg.consoles:
            if c["id"] == self.console["id"]:
                self.console = c
                self.grid.games = c.get("games", [])
                break
        self.grid.refresh_covers()

    def _load_background(self):
        path = self.cfg.resolve_path(self.cfg.settings.get("background_image", ""))
        if path and os.path.exists(path):
            w, h = self.screen.get_size()
            try:
                img = pygame.image.load(path).convert()
                self._bg = pygame.transform.smoothscale(img, (w, h))
            except Exception:
                self._bg = None

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        actions = self.input.consume_actions()

        for action in actions:
            if action in (ACTION_LEFT, ACTION_RIGHT, ACTION_UP, ACTION_DOWN):
                self.grid.move(action)

            elif action == ACTION_SELECT:
                game = self.grid.get_selected_game()
                if game:
                    from ui.screen_game_detail import GameDetailScreen
                    return GameDetailScreen(
                        self.screen, self.cfg, self.input,
                        self.console, game, parent_screen=self
                    )

            elif action == ACTION_BACK:
                return self.parent   # Terug naar hoofdscherm

            elif action == ACTION_MENU:
                from ui.screen_menu import MenuScreen
                return MenuScreen(self.screen, self.cfg, self.input,
                                  parent_screen=self)

        self.grid.update(dt)
        return None

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self):
        w, h = self.screen.get_size()

        if self._bg:
            self.screen.blit(self._bg, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill(COLOR_OVERLAY)
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(COLOR_BG)
            self._draw_bg_pattern()

        # Header
        self._draw_header(w)

        # Geen games?
        if not self.console.get("games"):
            self._draw_empty(w, h)
        else:
            self.grid.draw(self.screen, self._font_title, self._font_label)

        # Hint onderaan
        hints = "← ↑ ↓ → Navigeren   Enter Openen   Esc Terug"
        hint  = self._font_hint.render(hints, True, COLOR_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(centerx=w // 2, bottom=h - 10))

    def _draw_header(self, w: int):
        # Achtergrondstrook
        bar = pygame.Surface((w, 70), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 120))
        self.screen.blit(bar, (0, 0))

        # Terug-pijl + console naam
        back = self._font_title.render("‹", True, COLOR_ACCENT)
        self.screen.blit(back, (20, 20))

        title = self._font_title.render(self.console["name"], True, COLOR_TEXT)
        self.screen.blit(title, (55, 20))

        # Aantal games
        n    = len(self.console.get("games", []))
        sub  = self._font_hint.render(f"{n} game{'s' if n != 1 else ''}", True, COLOR_TEXT_DIM)
        self.screen.blit(sub, (57, 52))

    def _draw_empty(self, w: int, h: int):
        msg  = self._font_title.render("Geen games gevonden", True, COLOR_TEXT_DIM)
        sub  = self._font_hint.render(
            "Voeg games toe in config/consoles.json", True, COLOR_TEXT_DIM)
        self.screen.blit(msg, msg.get_rect(centerx=w // 2, centery=h // 2 - 20))
        self.screen.blit(sub, sub.get_rect(centerx=w // 2, centery=h // 2 + 20))

    def _draw_bg_pattern(self):
        w, h = self.screen.get_size()
        for x in range(0, w, 60):
            pygame.draw.line(self.screen, (20, 20, 35), (x, 0), (x, h))
        for y in range(0, h, 60):
            pygame.draw.line(self.screen, (20, 20, 35), (0, y), (w, y))
