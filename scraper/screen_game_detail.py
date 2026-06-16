"""
ui/screen_game_detail.py
Detailpagina voor één game.
- Links: grote cover art
- Rechts: naam, console, Spelen-knop, Cover wijzigen-knop
- Cover wijzigen: opent CoverPicker overlay
"""

import pygame
import os

from input.controller import (
    ACTION_SELECT, ACTION_BACK, ACTION_UP, ACTION_DOWN
)
from launcher.runner import GameLauncher

# ── Kleuren ────────────────────────────────────────────────────────────────────
COLOR_BG        = (10,  10,  18)
COLOR_TEXT      = (220, 220, 240)
COLOR_TEXT_DIM  = (100, 100, 130)
COLOR_ACCENT    = (80, 160, 255)
COLOR_BTN       = (30,  45, 100)
COLOR_BTN_SEL   = (50,  80, 180)
COLOR_BTN_BRD   = (80, 120, 255)
COLOR_BTN2      = (28,  40,  70)
COLOR_BTN2_SEL  = (38,  55,  95)
COLOR_OVERLAY   = (0,   0,   0, 160)

# ── Picker kleuren ─────────────────────────────────────────────────────────────
COLOR_PK_BG     = (12,  12,  22)
COLOR_PK_PANEL  = (20,  20,  36)
COLOR_PK_ITEM   = (26,  26,  44)
COLOR_PK_SEL    = (36,  52, 110)
COLOR_PK_BORDER = (60,  90, 200)
COLOR_PK_FILE   = (200, 200, 220)
COLOR_PK_DIM    = (90,  90, 120)

COVER_W   = 300
COVER_H   = 380
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
ENTRY_H   = 44
ENTRY_RAD = 6

# ── Knoppen op de detailpagina ─────────────────────────────────────────────────
BTN_PLAY   = 0
BTN_COVER  = 1
BTN_SCRAPE = 2


def _load_cover(path: str, w: int = COVER_W, h: int = COVER_H):
    if path and os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, (w, h))
        except Exception:
            pass
    return None


def _draw_rr(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# ══════════════════════════════════════════════════════════════════════════════
# CoverPicker – overlay om een cover te kiezen uit assets/covers/<console_id>/
# ══════════════════════════════════════════════════════════════════════════════

class CoverPicker:
    """
    Toont afbeeldingen uit assets/covers/<console_id>/ als scrollbare lijst
    met live preview. Input via InputHandler (geen eigen event.get()).

    Geeft terug via update(actions):
      None      – nog bezig
      "CANCEL"  – Esc / terug
      str       – relatief pad van de gekozen afbeelding
    """

    def __init__(self, screen: pygame.Surface, base_dir: str, console_id: str):
        self.screen     = screen
        self.base_dir   = base_dir
        self.console_id = console_id
        self._font      = pygame.font.SysFont("arial", 15)
        self._font_hint = pygame.font.SysFont("arial", 13)
        self._selected  = 0
        self._scroll    = 0
        self._preview   = None
        self._preview_idx = -1
        self._entries   = self._scan()

    def _scan(self) -> list:
        """Zoek alle afbeeldingen in assets/covers/<console_id>/"""
        folder = os.path.join(self.base_dir, "assets", "covers", self.console_id)
        entries = []
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                ext = os.path.splitext(name)[1].lower()
                if ext in IMAGE_EXTS:
                    entries.append({
                        "name": name,
                        "path": os.path.join(folder, name)
                    })
        return entries

    def _load_preview(self, idx: int):
        if idx == self._preview_idx or not self._entries:
            return
        self._preview_idx = idx
        try:
            img = pygame.image.load(self._entries[idx]["path"]).convert()
            self._preview = pygame.transform.smoothscale(img, (240, 300))
        except Exception:
            self._preview = None

    def _make_relative(self, path: str) -> str:
        try:
            return os.path.relpath(path, self.base_dir).replace("\\", "/")
        except ValueError:
            return path

    def update(self, actions: list):
        n = len(self._entries)
        for action in actions:
            if action == ACTION_BACK:
                return "CANCEL"
            elif action == ACTION_UP and self._selected > 0:
                self._selected -= 1
                self._clamp_scroll()
            elif action == ACTION_DOWN and self._selected < n - 1:
                self._selected += 1
                self._clamp_scroll()
            elif action == ACTION_SELECT and n > 0:
                return self._make_relative(self._entries[self._selected]["path"])
        if self._entries:
            self._load_preview(self._selected)
        return None

    def _clamp_scroll(self):
        visible = 10
        if self._selected >= self._scroll + visible:
            self._scroll = self._selected - visible + 1
        if self._selected < self._scroll:
            self._scroll = self._selected

    def draw(self):
        w, h = self.screen.get_size()

        # Donkere overlay
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 215))
        self.screen.blit(ov, (0, 0))

        # Paneel
        px, py = 80, 40
        pw, ph = w - 160, h - 80
        pygame.draw.rect(self.screen, COLOR_PK_PANEL,
                         pygame.Rect(px, py, pw, ph), border_radius=12)
        pygame.draw.rect(self.screen, COLOR_PK_BORDER,
                         pygame.Rect(px, py, pw, ph), width=2, border_radius=12)

        # Titel
        title = self._font.render("Kies cover art", True, COLOR_ACCENT)
        self.screen.blit(title, (px + 16, py + 14))

        folder = os.path.join("assets", "covers", self.console_id)
        flbl = self._font_hint.render(folder, True, COLOR_PK_DIM)
        self.screen.blit(flbl, (px + 16, py + 34))

        sep_y = py + 54
        pygame.draw.line(self.screen, COLOR_PK_BORDER,
                         (px + 8, sep_y), (px + pw - 8, sep_y))

        # Layout: lijst links | preview rechts
        prev_w = 280
        list_x = px + 12
        list_y = sep_y + 10
        list_w = pw - prev_w - 40
        list_h = ph - 72
        prev_x = px + list_w + 28
        prev_y = sep_y + 10

        # ── Lijst ─────────────────────────────────────────────────────────────
        visible = max(1, list_h // (ENTRY_H + 6))
        if self._selected >= self._scroll + visible:
            self._scroll = self._selected - visible + 1
        if self._selected < self._scroll:
            self._scroll = self._selected

        clip = pygame.Rect(list_x, list_y, list_w, list_h)
        self.screen.set_clip(clip)

        if not self._entries:
            msg = self._font.render(
                f"Geen afbeeldingen in {folder}", True, COLOR_PK_DIM)
            self.screen.blit(msg, (list_x + 10, list_y + 20))
            tip = self._font_hint.render(
                "Zet .jpg/.png bestanden in die map", True, COLOR_PK_DIM)
            self.screen.blit(tip, (list_x + 10, list_y + 46))
        else:
            for i in range(self._scroll,
                           min(self._scroll + visible + 1, len(self._entries))):
                ey  = list_y + (i - self._scroll) * (ENTRY_H + 6)
                er  = pygame.Rect(list_x, ey, list_w - 4, ENTRY_H)
                sel = (i == self._selected)
                pygame.draw.rect(self.screen,
                                 COLOR_PK_SEL if sel else COLOR_PK_ITEM,
                                 er, border_radius=ENTRY_RAD)
                if sel:
                    pygame.draw.rect(self.screen, COLOR_PK_BORDER, er,
                                     width=2, border_radius=ENTRY_RAD)
                lbl = self._font.render(
                    self._entries[i]["name"], True, COLOR_PK_FILE)
                self.screen.blit(lbl, lbl.get_rect(
                    midleft=(er.x + 12, er.centery)))

        self.screen.set_clip(None)

        # Scrollbar
        if len(self._entries) > visible:
            sb_h = max(20, int(list_h * visible / len(self._entries)))
            sb_y = list_y + int(
                self._scroll / len(self._entries) * list_h)
            pygame.draw.rect(self.screen, COLOR_PK_BORDER,
                             pygame.Rect(list_x + list_w - 6,
                                         sb_y, 4, sb_h),
                             border_radius=2)

        # ── Preview ───────────────────────────────────────────────────────────
        plbl = self._font_hint.render("Preview:", True, COLOR_PK_DIM)
        self.screen.blit(plbl, (prev_x, prev_y))
        pr = pygame.Rect(prev_x, prev_y + 22, 240, 300)
        if self._preview:
            self.screen.blit(self._preview, pr)
            pygame.draw.rect(self.screen, COLOR_PK_BORDER, pr,
                             width=1, border_radius=4)
        else:
            pygame.draw.rect(self.screen, COLOR_PK_BG, pr,
                             border_radius=4)
            no = self._font_hint.render("Geen preview", True, COLOR_PK_DIM)
            self.screen.blit(no, no.get_rect(center=pr.center))

        # ── Hint ──────────────────────────────────────────────────────────────
        hint = self._font_hint.render(
            "\u2191 \u2193 Navigeren   Enter Selecteren   Esc Annuleren",
            True, COLOR_PK_DIM)
        self.screen.blit(hint, hint.get_rect(
            centerx=px + pw // 2, bottom=py + ph - 8))


# ══════════════════════════════════════════════════════════════════════════════
# GameDetailScreen
# ══════════════════════════════════════════════════════════════════════════════

class GameDetailScreen:
    """
    Detailpagina voor een game.
    Links: grote cover art.
    Rechts: naam, console, Spelen-knop, Cover wijzigen-knop.
    """

    def __init__(self, screen: pygame.Surface, config_manager,
                 input_handler, console: dict, game: dict, parent_screen):
        self.screen   = screen
        self.cfg      = config_manager
        self.input    = input_handler
        self.console  = console
        self.game     = game
        self.parent   = parent_screen
        self.launcher = GameLauncher(config_manager.base_dir)

        self._font_title  = pygame.font.SysFont("arial", 36, bold=True)
        self._font_sub    = pygame.font.SysFont("arial", 18)
        self._font_btn    = pygame.font.SysFont("arial", 20, bold=True)
        self._font_hint   = pygame.font.SysFont("arial", 14)
        self._bg          = None
        self._cover       = None
        self._launch_error = ""

        # Welke knop is geselecteerd: BTN_PLAY of BTN_COVER
        self._btn_focus   = BTN_PLAY

        # Cover picker overlay
        self._picker: CoverPicker | None = None

        self._reload_cover()
        self._load_background()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _reload_cover(self):
        path = self.cfg.resolve_path(self.game.get("cover", ""))
        self._cover = _load_cover(path)

    def _load_background(self):
        path = self.cfg.resolve_path(
            self.cfg.settings.get("background_image", ""))
        if path and os.path.exists(path):
            w, h = self.screen.get_size()
            try:
                img = pygame.image.load(path).convert()
                self._bg = pygame.transform.smoothscale(img, (w, h))
            except Exception:
                self._bg = None

    def _save_cover(self, rel_path: str):
        """Sla het nieuwe cover-pad op in cfg.consoles en schrijf weg."""
        self.game["cover"] = rel_path
        # Zoek de game in cfg.consoles en update
        for c in self.cfg.consoles:
            if c["id"] == self.console["id"]:
                for g in c.get("games", []):
                    if g["id"] == self.game["id"]:
                        g["cover"] = rel_path
                        break
        self.cfg.save_consoles()
        self._reload_cover()

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        actions = self.input.consume_actions()

        # Picker actief? Geef acties door.
        if self._picker is not None:
            result = self._picker.update(actions)
            if result == "CANCEL":
                self._picker = None
            elif result is not None:
                self._save_cover(result)
                self._picker = None
            return None

        for action in actions:
            if action == ACTION_BACK:
                return self.parent

            elif action in (ACTION_UP, ACTION_DOWN):
                # Schakel tussen Spelen en Cover wijzigen
                self._btn_focus = BTN_COVER if self._btn_focus == BTN_PLAY else BTN_PLAY

            elif action == ACTION_SELECT:
                if self._btn_focus == BTN_PLAY:
                    self._launch_game()
                elif self._btn_focus == BTN_COVER:
                    self._picker = CoverPicker(
                        self.screen,
                        self.cfg.base_dir,
                        self.console["id"]
                    )

        return None

    def _launch_game(self):
        ok = self.launcher.launch(self.console, self.game)
        self._launch_error = (
            "" if ok
            else "Kon emulator niet starten \u2013 check emulator_cmd in consoles.json"
        )

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self):
        # Picker tekent zichzelf bovenop alles
        if self._picker is not None:
            # Teken eerst de achtergrond
            self._draw_base()
            self._picker.draw()
            return

        self._draw_base()

    def _draw_base(self):
        w, h = self.screen.get_size()

        # Achtergrond
        if self._bg:
            self.screen.blit(self._bg, (0, 0))
            ov = pygame.Surface((w, h), pygame.SRCALPHA)
            ov.fill(COLOR_OVERLAY)
            self.screen.blit(ov, (0, 0))
        else:
            self.screen.fill(COLOR_BG)
            self._draw_bg_pattern()

        cover_x = w // 2 - COVER_W - 40
        info_x  = w // 2 + 40
        mid_y   = h // 2

        # ── Cover links ────────────────────────────────────────────────────────
        cover_rect = pygame.Rect(cover_x, mid_y - COVER_H // 2, COVER_W, COVER_H)
        if self._cover:
            shadow = cover_rect.inflate(8, 8).move(4, 4)
            _draw_rr(self.screen, (0, 0, 0), shadow, 10)
            self.screen.blit(self._cover, cover_rect)
            pygame.draw.rect(self.screen, COLOR_BTN_BRD,
                             cover_rect, width=2, border_radius=8)
        else:
            self._draw_cover_placeholder(cover_rect)

        # ── Info rechts ────────────────────────────────────────────────────────
        info_y = mid_y - 140

        # Console naam
        con_lbl = self._font_sub.render(self.console["name"], True, COLOR_ACCENT)
        self.screen.blit(con_lbl, (info_x, info_y))
        info_y += 34

        # Game naam
        info_y = self._draw_wrapped_title(info_x, info_y, w - info_x - 40)
        info_y += 36

        # ── Knop: Spelen ───────────────────────────────────────────────────────
        play_sel  = (self._btn_focus == BTN_PLAY)
        play_rect = pygame.Rect(info_x, info_y, 240, 52)
        _draw_rr(self.screen,
                 COLOR_BTN_SEL if play_sel else COLOR_BTN,
                 play_rect, 10)
        pygame.draw.rect(self.screen, COLOR_BTN_BRD,
                         play_rect, width=2 if play_sel else 1,
                         border_radius=10)
        play_lbl = self._font_btn.render("\u25b6  Spelen", True, COLOR_TEXT)
        self.screen.blit(play_lbl, play_lbl.get_rect(center=play_rect.center))
        info_y += 64

        # ── Knop: Cover wijzigen ───────────────────────────────────────────────
        cov_sel  = (self._btn_focus == BTN_COVER)
        cov_rect = pygame.Rect(info_x, info_y, 240, 44)
        _draw_rr(self.screen,
                 COLOR_BTN2_SEL if cov_sel else COLOR_BTN2,
                 cov_rect, 10)
        pygame.draw.rect(self.screen, COLOR_BTN_BRD,
                         cov_rect, width=2 if cov_sel else 1,
                         border_radius=10)
        cov_lbl = self._font_sub.render("\U0001f5bc  Cover wijzigen", True,
                                         COLOR_TEXT if cov_sel else COLOR_TEXT_DIM)
        self.screen.blit(cov_lbl, cov_lbl.get_rect(center=cov_rect.center))
        info_y += 58

        # ── Knop: Scraper ──────────────────────────────────────────────────────
        scr_sel  = (self._btn_focus == BTN_SCRAPE)
        scr_rect = pygame.Rect(info_x, info_y, 240, 44)
        _draw_rr(self.screen,
                 COLOR_BTN2_SEL if scr_sel else COLOR_BTN2, scr_rect, 10)
        pygame.draw.rect(self.screen, COLOR_BTN_BRD,
                         scr_rect, width=2 if scr_sel else 1, border_radius=10)
        scr_lbl = self._font_sub.render("\U0001f50d  Cover scrapen", True,
                                         COLOR_TEXT if scr_sel else COLOR_TEXT_DIM)
        self.screen.blit(scr_lbl, scr_lbl.get_rect(center=scr_rect.center))
        info_y += 58

        # Foutmelding
        if self._launch_error:
            err = self._font_hint.render(self._launch_error, True, (220, 80, 80))
            self.screen.blit(err, (info_x, info_y))

        # Terug
        back_lbl = self._font_sub.render("\u2039  Terug", True, COLOR_ACCENT)
        self.screen.blit(back_lbl, (24, 20))

        # Hint
        hints = "\u2191 \u2193 Knop wisselen   Enter Bevestigen   Esc Terug"
        hint  = self._font_hint.render(hints, True, COLOR_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(centerx=w // 2, bottom=h - 10))

    def _draw_wrapped_title(self, x, y, max_w) -> int:
        words = self.game["name"].split()
        lines, line = [], ""
        for word in words:
            test = (line + " " + word).strip()
            if self._font_title.size(test)[0] <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        for l in lines:
            surf = self._font_title.render(l, True, COLOR_TEXT)
            self.screen.blit(surf, (x, y))
            y += self._font_title.get_height() + 4
        return y

    def _draw_cover_placeholder(self, rect):
        h = hash(self.game["id"]) % 360
        c = pygame.Color(0)
        c.hsva = (h, 55, 50, 100)
        _draw_rr(self.screen, c, rect, 8)
        abbr = "".join(w[0] for w in self.game["name"].split()[:3]).upper()
        font = pygame.font.SysFont("arial", 64, bold=True)
        lbl  = font.render(abbr, True, (255, 255, 255))
        self.screen.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_bg_pattern(self):
        w, h = self.screen.get_size()
        for x in range(0, w, 60):
            pygame.draw.line(self.screen, (20, 20, 35), (x, 0), (x, h))
        for y in range(0, h, 60):
            pygame.draw.line(self.screen, (20, 20, 35), (0, y), (w, y))
