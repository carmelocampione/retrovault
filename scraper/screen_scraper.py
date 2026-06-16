"""
ui/screen_scraper.py
Scraper overlay – wordt geopend vanuit de game-detailpagina.

Flow:
  1. Scherm toont de gamenaam als zoekterm (aanpasbaar)
  2. Zoekresultaten verschijnen als lijst met naam + jaar
  3. Navigeer met ↑↓, rechts toont cover preview
  4. Enter selecteert → cover wordt gedownload → terug naar detailpagina
"""

import pygame
import os
import urllib.request
import io
import threading

from input.controller import (
    ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT,
    ACTION_SELECT, ACTION_BACK
)

# ── Kleuren ────────────────────────────────────────────────────────────────────
COLOR_BG      = (12,  12,  22)
COLOR_PANEL   = (18,  18,  32)
COLOR_ITEM    = (26,  26,  44)
COLOR_SEL     = (36,  52, 110)
COLOR_BORDER  = (60,  90, 200)
COLOR_TEXT    = (220, 220, 240)
COLOR_DIM     = (100, 100, 130)
COLOR_ACCENT  = (80, 160, 255)
COLOR_OK      = (80, 200, 120)
COLOR_ERR     = (200, 80,  80)

ENTRY_H   = 52
ENTRY_RAD = 6


def _draw_rr(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


class ScraperScreen:
    """
    Scraper overlay.
    Toont zoekresultaten van IGDB voor een game.
    """

    def __init__(self, screen: pygame.Surface, config_manager,
                 input_handler, scraper_service,
                 console: dict, game: dict, parent_screen):
        self.screen   = screen
        self.cfg      = config_manager
        self.input    = input_handler
        self.svc      = scraper_service
        self.console  = console
        self.game     = game
        self.parent   = parent_screen

        self._font       = pygame.font.SysFont("arial", 15)
        self._font_title = pygame.font.SysFont("arial", 20, bold=True)
        self._font_small = pygame.font.SysFont("arial", 13)
        self._font_hint  = pygame.font.SysFont("arial", 13)

        # Zoekterm – standaard de gamenaam
        self._query        = game.get("name", "")
        self._editing      = False   # Is de zoekterm bewerkbaar?
        self._cursor       = len(self._query)

        self._selected     = 0
        self._scroll       = 0
        self._results      = []
        self._search_state = None   # ScrapeResult
        self._save_state   = None   # ScrapeResult

        # Preview afbeelding (geladen in achtergrondthread)
        self._preview_surf  = None
        self._preview_idx   = -1
        self._preview_loading = False

        # Start meteen met zoeken
        self._start_search()

    # ── Zoeken ─────────────────────────────────────────────────────────────────

    def _start_search(self):
        if not self.svc.is_configured():
            return
        self._results      = []
        self._selected     = 0
        self._scroll       = 0
        self._preview_surf = None
        self._preview_idx  = -1
        self._search_state = self.svc.search_async(
            self._query, self.console["id"])

    def _load_preview_async(self, idx: int):
        if idx == self._preview_idx or self._preview_loading:
            return
        if idx >= len(self._results):
            return
        url = self._results[idx].get("cover_url", "")
        if not url:
            self._preview_surf = None
            self._preview_idx  = idx
            return

        self._preview_loading = True
        self._preview_idx     = idx

        def _fetch():
            try:
                with urllib.request.urlopen(url, timeout=8) as resp:
                    data = resp.read()
                img = pygame.image.load(io.BytesIO(data)).convert()
                self._preview_surf = pygame.transform.smoothscale(img, (240, 300))
            except Exception:
                self._preview_surf = None
            finally:
                self._preview_loading = False

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt: float, actions: list = None):
        # Zoekresultaten binnengekomen?
        if self._search_state and self._search_state.done:
            self._results      = self._search_state.results
            self._search_state = None
            self._selected     = 0
            self._scroll       = 0
            self._preview_surf = None
            self._preview_idx  = -1

        # Opslaan klaar?
        if self._save_state and self._save_state.done:
            if not self._save_state.error:
                return self.parent   # Terug, cover is opgeslagen
            self._save_state = None  # Fout – blijf op dit scherm

        if actions is None:
            actions = self.input.consume_actions()

        # Zoekterm bewerken
        if self._editing:
            for event in pygame.event.get([pygame.KEYDOWN]):
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._editing = False
                    self._start_search()
                elif event.key == pygame.K_ESCAPE:
                    self._editing = False
                elif event.key == pygame.K_BACKSPACE and self._cursor > 0:
                    self._query = (self._query[:self._cursor - 1]
                                   + self._query[self._cursor:])
                    self._cursor -= 1
                elif event.key == pygame.K_DELETE:
                    self._query = (self._query[:self._cursor]
                                   + self._query[self._cursor + 1:])
                elif event.key == pygame.K_LEFT and self._cursor > 0:
                    self._cursor -= 1
                elif event.key == pygame.K_RIGHT and self._cursor < len(self._query):
                    self._cursor += 1
                elif event.unicode and event.unicode.isprintable():
                    self._query = (self._query[:self._cursor]
                                   + event.unicode
                                   + self._query[self._cursor:])
                    self._cursor += 1
            return None

        n = len(self._results)
        for action in actions:
            if action == ACTION_BACK:
                return self.parent

            elif action == ACTION_UP and self._selected > 0:
                self._selected -= 1
                self._clamp_scroll()
                self._load_preview_async(self._selected)

            elif action == ACTION_DOWN and self._selected < n - 1:
                self._selected += 1
                self._clamp_scroll()
                self._load_preview_async(self._selected)

            elif action == ACTION_SELECT:
                if n > 0 and self._save_state is None:
                    r = self._results[self._selected]
                    self._save_state = self.svc.save_cover_async(
                        self.console, self.game,
                        r["image_id"], r["name"]
                    )

            elif action == ACTION_LEFT:
                # Focus op zoekbalk
                self._editing = True
                self._cursor  = len(self._query)

        # Laad preview voor geselecteerd item
        if n > 0 and self._preview_idx != self._selected:
            self._load_preview_async(self._selected)

        return None

    def _clamp_scroll(self):
        visible = 8
        if self._selected >= self._scroll + visible:
            self._scroll = self._selected - visible + 1
        if self._selected < self._scroll:
            self._scroll = self._selected

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self):
        w, h = self.screen.get_size()

        # Overlay
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 220))
        self.screen.blit(ov, (0, 0))

        # Paneel
        px, py = 60, 40
        pw, ph = w - 120, h - 80
        _draw_rr(self.screen, COLOR_PANEL, pygame.Rect(px, py, pw, ph), 12)
        pygame.draw.rect(self.screen, COLOR_BORDER,
                         pygame.Rect(px, py, pw, ph), width=2, border_radius=12)

        # Titel
        title = self._font_title.render(
            f"Cover scrapen \u2013 {self.game['name']}", True, COLOR_ACCENT)
        self.screen.blit(title, (px + 16, py + 12))

        # ── Zoekbalk ──────────────────────────────────────────────────────────
        bar_y  = py + 44
        bar_r  = pygame.Rect(px + 12, bar_y, pw - 24, 34)
        _draw_rr(self.screen, (10, 10, 28) if self._editing else COLOR_ITEM, bar_r, 6)
        pygame.draw.rect(self.screen,
                         COLOR_ACCENT if self._editing else COLOR_BORDER,
                         bar_r, width=2 if self._editing else 1, border_radius=6)

        disp = self._query
        show_cur = self._editing and (pygame.time.get_ticks() // 500) % 2 == 0
        render_q = disp[:self._cursor] + ("|" if show_cur else "") + disp[self._cursor:]
        if len(render_q) > 60:
            render_q = "\u2026" + render_q[-59:]
        self.screen.blit(
            self._font.render(render_q, True, COLOR_TEXT),
            (bar_r.x + 10, bar_r.centery - 8))

        if not self._editing:
            hint_lbl = self._font_small.render(
                "\u2190 zoekterm bewerken", True, COLOR_DIM)
            self.screen.blit(hint_lbl, hint_lbl.get_rect(
                midright=(bar_r.right - 8, bar_r.centery)))

        sep_y = bar_y + 44
        pygame.draw.line(self.screen, COLOR_BORDER,
                         (px + 8, sep_y), (px + pw - 8, sep_y))

        # ── Layout: lijst links | preview rechts ──────────────────────────────
        prev_w  = 270
        list_x  = px + 12
        list_y  = sep_y + 10
        list_w  = pw - prev_w - 32
        list_h  = ph - (sep_y - py) - 50
        prev_x  = px + list_w + 24
        prev_y  = sep_y + 10

        # ── Status ────────────────────────────────────────────────────────────
        if not self.svc.is_configured():
            self._draw_not_configured(list_x, list_y, list_w)
        elif self._search_state and self._search_state.loading:
            self._draw_loading(list_x, list_y, list_w)
        elif self._search_state and self._search_state.error:
            self._draw_error(list_x, list_y, self._search_state.error)
        elif not self._results:
            self._draw_no_results(list_x, list_y)
        else:
            self._draw_results(list_x, list_y, list_w, list_h)

        # ── Preview ───────────────────────────────────────────────────────────
        self._draw_preview(prev_x, prev_y)

        # ── Opslaan status ────────────────────────────────────────────────────
        if self._save_state:
            if self._save_state.loading:
                saving = self._font.render(
                    "Cover downloaden en opslaan\u2026", True, COLOR_ACCENT)
                self.screen.blit(saving, saving.get_rect(
                    centerx=px + pw // 2, bottom=py + ph - 28))
            elif self._save_state.error:
                err = self._font.render(
                    f"Fout: {self._save_state.error}", True, COLOR_ERR)
                self.screen.blit(err, err.get_rect(
                    centerx=px + pw // 2, bottom=py + ph - 28))

        # ── Hint ──────────────────────────────────────────────────────────────
        if self._editing:
            hints = "Typ zoekterm   Enter Zoeken   Esc Annuleren"
        else:
            hints = "\u2191 \u2193 Navigeren   Enter Cover kiezen   \u2190 Zoekterm   Esc Terug"
        hint = self._font_hint.render(hints, True, COLOR_DIM)
        self.screen.blit(hint, hint.get_rect(
            centerx=px + pw // 2, bottom=py + ph - 8))

    def _draw_results(self, lx, ly, lw, lh):
        visible = max(1, lh // (ENTRY_H + 6))
        if self._selected >= self._scroll + visible:
            self._scroll = self._selected - visible + 1
        if self._selected < self._scroll:
            self._scroll = self._selected

        clip = pygame.Rect(lx, ly, lw, lh)
        self.screen.set_clip(clip)

        for i in range(self._scroll,
                       min(self._scroll + visible + 1, len(self._results))):
            r   = self._results[i]
            ey  = ly + (i - self._scroll) * (ENTRY_H + 6)
            er  = pygame.Rect(lx, ey, lw - 4, ENTRY_H)
            sel = (i == self._selected)
            _draw_rr(self.screen, COLOR_SEL if sel else COLOR_ITEM, er, ENTRY_RAD)
            if sel:
                pygame.draw.rect(self.screen, COLOR_BORDER, er,
                                 width=2, border_radius=ENTRY_RAD)

            # Naam
            name = r["name"]
            if len(name) > 45:
                name = name[:43] + "\u2026"
            self.screen.blit(
                self._font.render(name, True, COLOR_TEXT if sel else COLOR_DIM),
                (er.x + 10, er.y + 8))

            # Jaar
            if r.get("year"):
                yr = self._font_small.render(r["year"], True, COLOR_ACCENT)
                self.screen.blit(yr, (er.x + 10, er.y + 30))

            # Cover indicator
            if r.get("cover_url"):
                cd = self._font_small.render("\U0001f5bc", True, COLOR_OK)
                self.screen.blit(cd, cd.get_rect(midright=(er.right - 8, er.centery)))

        self.screen.set_clip(None)

        # Scrollbar
        if len(self._results) > visible:
            sb_h = max(20, int(lh * visible / len(self._results)))
            sb_y = ly + int(self._scroll / len(self._results) * lh)
            pygame.draw.rect(self.screen, COLOR_BORDER,
                             pygame.Rect(lx + lw - 6, sb_y, 4, sb_h),
                             border_radius=2)

    def _draw_preview(self, px, py):
        lbl = self._font_small.render("Preview:", True, COLOR_DIM)
        self.screen.blit(lbl, (px, py))
        pr = pygame.Rect(px, py + 22, 240, 300)
        if self._preview_surf:
            self.screen.blit(self._preview_surf, pr)
            pygame.draw.rect(self.screen, COLOR_BORDER, pr,
                             width=1, border_radius=4)
        elif self._preview_loading:
            _draw_rr(self.screen, COLOR_BG if hasattr(self, 'COLOR_BG') else (12,12,22), pr, 4)
            ld = self._font_small.render("Laden\u2026", True, COLOR_DIM)
            self.screen.blit(ld, ld.get_rect(center=pr.center))
        else:
            _draw_rr(self.screen, (10, 10, 20), pr, 4)
            no = self._font_small.render("Geen cover", True, COLOR_DIM)
            self.screen.blit(no, no.get_rect(center=pr.center))

        # Samenvatting onder preview
        if self._results and self._selected < len(self._results):
            summary = self._results[self._selected].get("summary", "")
            if summary:
                words  = summary.split()
                lines, line = [], ""
                for w in words:
                    test = (line + " " + w).strip()
                    if self._font_small.size(test)[0] <= 240:
                        line = test
                    else:
                        lines.append(line)
                        line = w
                        if len(lines) >= 4:
                            break
                if line and len(lines) < 4:
                    lines.append(line)
                sy = pr.bottom + 10
                for l in lines:
                    self.screen.blit(
                        self._font_small.render(l, True, COLOR_DIM), (px, sy))
                    sy += 18

    def _draw_loading(self, lx, ly, lw):
        msg = self._font.render("Zoeken\u2026", True, COLOR_ACCENT)
        self.screen.blit(msg, (lx + 20, ly + 20))

    def _draw_error(self, lx, ly, error):
        msg = self._font.render(f"Fout: {error}", True, COLOR_ERR)
        self.screen.blit(msg, (lx + 20, ly + 20))

    def _draw_no_results(self, lx, ly):
        msg = self._font.render("Geen resultaten gevonden.", True, COLOR_DIM)
        self.screen.blit(msg, (lx + 20, ly + 20))
        tip = self._font_small.render(
            "Pas de zoekterm aan met \u2190", True, COLOR_DIM)
        self.screen.blit(tip, (lx + 20, ly + 44))

    def _draw_not_configured(self, lx, ly, lw):
        lines = [
            "IGDB niet geconfigureerd.",
            "Ga naar Menu \u2192 Instellingen en vul in:",
            "  \u2022 IGDB Client ID",
            "  \u2022 IGDB Client Secret",
        ]
        y = ly + 16
        for line in lines:
            self.screen.blit(self._font.render(line, True, COLOR_ERR), (lx + 16, y))
            y += 26
