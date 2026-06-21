"""
ui/screen_menu.py
Menu-scherm met verticale tabs links, inhoud rechts.

Tabs:
  1. Consoles      – checkbox zichtbaar/verborgen + volgorde aanpassen
  2. Instellingen  – achtergrond, volledig scherm
  3. Scraper       – placeholder (toekomst)
  4. Server        – placeholder (toekomst)

Besturing:
  Tab-kolom actief:
    ↑ / ↓          Wissel van tab
    → / Enter       Ga naar inhoud van de tab

  Inhoud actief:
    ↑ / ↓          Navigeer door items
    Enter          Toggle checkbox (Consoles-tab)
    L / R bumper   (controller: LB/RB) = item omhoog/omlaag schuiven
    PgUp / PgDn    Item omhoog / omlaag schuiven (keyboard)
    ←  / Esc       Terug naar tab-kolom
    Esc (in tab)   Sluit menu
"""

import pygame
import os

from input.controller import (
    ACTION_LEFT, ACTION_RIGHT, ACTION_UP, ACTION_DOWN,
    ACTION_SELECT, ACTION_BACK, ACTION_MENU
)

# ── Kleuren ────────────────────────────────────────────────────────────────────
COLOR_BG          = (10,  10,  18)
COLOR_PANEL       = (18,  18,  32)
COLOR_TAB         = (22,  22,  40)
COLOR_TAB_SEL     = (32,  42,  85)
COLOR_TAB_ACTIVE  = (40,  60, 130)
COLOR_CONTENT     = (15,  15,  28)
COLOR_ITEM        = (22,  22,  38)
COLOR_ITEM_SEL    = (30,  45,  90)
COLOR_BORDER      = (55,  75, 170)
COLOR_TEXT        = (220, 220, 240)
COLOR_TEXT_DIM    = (100, 100, 130)
COLOR_ACCENT      = (80, 160, 255)
COLOR_CHECK_ON    = (80, 200, 120)
COLOR_CHECK_OFF   = (80,  80, 100)
COLOR_PLACEHOLDER = (40,  40,  60)
COLOR_ERR         = (200, 80,  80)

TAB_W       = 200
ITEM_H      = 52
ITEM_RADIUS = 8
TAB_RADIUS  = 8

# Extra controller-acties voor volgorde aanpassen
# We hergebruiken ACTION_MENU als "move-up" en een nieuwe constante voor "move-down"
# maar eigenlijk mappen we op joystick-shoulder via JOYBUTTON events.
# Voor keyboard: PageUp / PageDown
ACTION_MOVE_UP   = "move_item_up"
ACTION_MOVE_DOWN = "move_item_down"

TABS = [
    {"id": "consoles",     "label": "🎮  Consoles"},
    {"id": "emulators",    "label": "🕹️  Emulators"},
    {"id": "instellingen", "label": "⚙️   Instellingen"},
    {"id": "scraper",      "label": "🔍  Scraper"},
    {"id": "server",       "label": "☁️   Server"},
]

# Instellingen-items
SETTINGS_ITEMS = [
    {"id": "background_image", "label": "Achtergrond",
     "type": "path", "hint": "Relatief pad naar .jpg / .png"},
    {"id": "refresh_background", "label": "Vernieuw achtergrond",
     "type": "action", "hint": "Herlaad de achtergrondafbeelding"},
    {"id": "igdb_client_id", "label": "IGDB Client ID",
     "type": "text", "hint": "IGDB application client ID"},
    {"id": "igdb_client_secret", "label": "IGDB Client Secret",
     "type": "text", "hint": "IGDB application client secret"},
    {"id": "server_url", "label": "Server URL",
     "type": "text", "hint": "HTTP/HTTPS URL van de server"},
]


# ── Bekende emulators per console-ID ──────────────────────────────────────────
EMULATOR_PRESETS = {
    "nes":       [("RetroArch – Nestopia",     "retroarch -L cores/nestopia_libretro.dll"),
                  ("RetroArch – FCEUmm",       "retroarch -L cores/fceumm_libretro.dll")],
    "snes":      [("RetroArch – Snes9x",       "retroarch -L cores/snes9x_libretro.dll"),
                  ("RetroArch – bsnes",        "retroarch -L cores/bsnes_libretro.dll")],
    "n64":       [("RetroArch – Mupen64Plus",  "retroarch -L cores/mupen64plus_next_libretro.dll"),
                  ("RetroArch – ParaLLEl",     "retroarch -L cores/parallel_n64_libretro.dll")],
    "gamecube":  [("Dolphin",                  "Dolphin.exe -e"),
                  ("RetroArch – Dolphin",      "retroarch -L cores/dolphin_libretro.dll")],
    "wii":       [("Dolphin",                  "Dolphin.exe -e")],
    "wiiu":      [("Cemu",                     "Cemu.exe -f -g")],
    "switch":    [("Yuzu",                     "yuzu.exe"),
                  ("Ryujinx",                  "Ryujinx.exe")],
    "gb":        [("RetroArch – Gambatte",     "retroarch -L cores/gambatte_libretro.dll"),
                  ("RetroArch – SameBoy",      "retroarch -L cores/sameboy_libretro.dll")],
    "gbc":       [("RetroArch – Gambatte",     "retroarch -L cores/gambatte_libretro.dll"),
                  ("RetroArch – SameBoy",      "retroarch -L cores/sameboy_libretro.dll")],
    "gba":       [("RetroArch – mGBA",         "retroarch -L cores/mgba_libretro.dll"),
                  ("RetroArch – VBA-M",        "retroarch -L cores/vbam_libretro.dll")],
    "nds":       [("RetroArch – DeSmuME",      "retroarch -L cores/desmume_libretro.dll"),
                  ("RetroArch – melonDS",      "retroarch -L cores/melonds_libretro.dll"),
                  ("melonDS standalone",       "melonDS.exe")],
    "megadrive": [("RetroArch – Genesis+GX",   "retroarch -L cores/genesis_plus_gx_libretro.dll"),
                  ("RetroArch – BlastEm",      "retroarch -L cores/blastem_libretro.dll")],
    "dreamcast": [("RetroArch – Flycast",      "retroarch -L cores/flycast_libretro.dll"),
                  ("Flycast standalone",       "flycast.exe")],
    "ps1":       [("RetroArch – Beetle PSX",   "retroarch -L cores/mednafen_psx_libretro.dll"),
                  ("RetroArch – PCSX ReARMed", "retroarch -L cores/pcsx_rearmed_libretro.dll"),
                  ("DuckStation",              "duckstation-qt.exe")],
    "ps2":       [("PCSX2",                    "pcsx2-qt.exe"),
                  ("RetroArch – PCSX2",        "retroarch -L cores/pcsx2_libretro.dll")],
    "ps3":       [("RPCS3",                    "rpcs3.exe")],
    "psp":       [("PPSSPP",                   "ppsspp.exe"),
                  ("RetroArch – PPSSPP",       "retroarch -L cores/ppsspp_libretro.dll")],
}


def _draw_rr(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# ── Achtergrond-picker ────────────────────────────────────────────────────────
# Eenvoudige overlay: toont alleen afbeeldingen uit assets/backgrounds/.
# Input loopt via InputHandler (zelfde systeem als de rest van de UI).

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

COLOR_FB_BG      = (12,  12,  22)
COLOR_FB_PANEL   = (20,  20,  36)
COLOR_FB_ITEM    = (26,  26,  44)
COLOR_FB_SEL     = (36,  52, 110)
COLOR_FB_BORDER  = (60,  90, 200)
COLOR_FB_FILE    = (200, 200, 220)
COLOR_FB_DIM     = (90,   90, 120)

ENTRY_H   = 44
ENTRY_RAD = 6


class BackgroundPicker:
    """
    Toont alle afbeeldingen in assets/backgrounds/ als scrollbare lijst.
    Rechts: live preview van de geselecteerde afbeelding.
    Input via de InputHandler (geen eigen event.get()).

    Geeft terug via update(actions):
      None      - nog bezig
      "CANCEL"  - Esc / terug
      str       - relatief pad van de gekozen afbeelding
    """

    def __init__(self, screen: pygame.Surface, base_dir: str):
        self.screen   = screen
        self.base_dir = base_dir
        self._font      = pygame.font.SysFont("arial", 15)
        self._font_hint = pygame.font.SysFont("arial", 13)
        self._selected  = 0
        self._scroll    = 0
        self._preview   = None
        self._preview_idx = -1
        self._entries   = self._scan()

    def _scan(self) -> list:
        """Zoek alle afbeeldingen in assets/backgrounds/."""
        folder = os.path.join(self.base_dir, "assets", "backgrounds")
        entries = []
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                ext = os.path.splitext(name)[1].lower()
                if ext in IMAGE_EXTS:
                    full = os.path.join(folder, name)
                    entries.append({"name": name, "path": full})
        return entries

    def _load_preview(self, idx: int):
        if idx == self._preview_idx:
            return
        self._preview_idx = idx
        if not self._entries:
            self._preview = None
            return
        try:
            img = pygame.image.load(self._entries[idx]["path"]).convert()
            self._preview = pygame.transform.smoothscale(img, (320, 180))
        except Exception:
            self._preview = None

    def _make_relative(self, path: str) -> str:
        try:
            return os.path.relpath(path, self.base_dir)
        except ValueError:
            return path

    # ── Update – ontvangt al verwerkte acties van MenuScreen ──────────────────

    def update(self, actions: list):
        """
        Verwerk acties. Geeft None, "CANCEL" of een pad-string terug.
        """
        from input.controller import ACTION_UP, ACTION_DOWN, ACTION_SELECT, ACTION_BACK
        n = len(self._entries)

        for action in actions:
            if action in (ACTION_BACK,):
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
        visible = 10  # ruime schatting; wordt in draw verfijnd
        if self._selected >= self._scroll + visible:
            self._scroll = self._selected - visible + 1
        if self._selected < self._scroll:
            self._scroll = self._selected

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        w, h = self.screen.get_size()

        # Donkere overlay
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        self.screen.blit(ov, (0, 0))

        # Paneel
        px, py = 80, 50
        pw, ph = w - 160, h - 100
        panel  = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.screen, COLOR_FB_PANEL, panel, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_FB_BORDER, panel, width=2, border_radius=12)

        # Titel
        title = self._font.render("Kies achtergrondafbeelding", True, (80, 160, 255))
        self.screen.blit(title, (px + 16, py + 14))

        # Map-label
        folder = os.path.join("assets", "backgrounds")
        flbl = self._font_hint.render(folder, True, COLOR_FB_DIM)
        self.screen.blit(flbl, (px + 16, py + 34))

        sep_y = py + 54
        pygame.draw.line(self.screen, COLOR_FB_BORDER,
                         (px + 8, sep_y), (px + pw - 8, sep_y))

        # Layout: lijst links | preview rechts
        prev_w  = 340
        list_x  = px + 12
        list_y  = sep_y + 10
        list_w  = pw - prev_w - 32
        list_h  = ph - 72
        prev_x  = px + list_w + 24
        prev_y  = sep_y + 10

        # ── Lijst ─────────────────────────────────────────────────────────────
        visible = max(1, list_h // (ENTRY_H + 6))
        # Herbereken scroll nu we de echte hoogte weten
        if self._selected >= self._scroll + visible:
            self._scroll = self._selected - visible + 1
        if self._selected < self._scroll:
            self._scroll = self._selected

        clip = pygame.Rect(list_x, list_y, list_w, list_h)
        self.screen.set_clip(clip)

        if not self._entries:
            msg = self._font.render(
                "Geen afbeeldingen in assets/backgrounds/", True, COLOR_FB_DIM)
            self.screen.blit(msg, (list_x + 10, list_y + 20))
        else:
            for i in range(self._scroll, min(self._scroll + visible + 1, len(self._entries))):
                ey  = list_y + (i - self._scroll) * (ENTRY_H + 6)
                er  = pygame.Rect(list_x, ey, list_w - 4, ENTRY_H)
                sel = (i == self._selected)
                pygame.draw.rect(self.screen,
                                 COLOR_FB_SEL if sel else COLOR_FB_ITEM,
                                 er, border_radius=ENTRY_RAD)
                if sel:
                    pygame.draw.rect(self.screen, COLOR_FB_BORDER, er,
                                     width=2, border_radius=ENTRY_RAD)
                name = self._entries[i]["name"]
                lbl  = self._font.render(name, True, COLOR_FB_FILE)
                self.screen.blit(lbl, lbl.get_rect(midleft=(er.x + 12, er.centery)))

        self.screen.set_clip(None)

        # Scrollbar
        if len(self._entries) > visible:
            sb_total = list_h
            sb_h = max(20, int(sb_total * visible / len(self._entries)))
            sb_y = list_y + int(self._scroll / len(self._entries) * sb_total)
            pygame.draw.rect(self.screen, COLOR_FB_BORDER,
                             pygame.Rect(list_x + list_w - 6, sb_y, 4, sb_h),
                             border_radius=2)

        # ── Preview ───────────────────────────────────────────────────────────
        plbl = self._font_hint.render("Preview:", True, COLOR_FB_DIM)
        self.screen.blit(plbl, (prev_x, prev_y))
        pr = pygame.Rect(prev_x, prev_y + 22, 320, 180)
        if self._preview:
            self.screen.blit(self._preview, pr)
            pygame.draw.rect(self.screen, COLOR_FB_BORDER, pr,
                             width=1, border_radius=4)
        else:
            pygame.draw.rect(self.screen, COLOR_FB_BG, pr, border_radius=4)
            no = self._font_hint.render("Geen preview", True, COLOR_FB_DIM)
            self.screen.blit(no, no.get_rect(center=pr.center))

        # ── Hint ──────────────────────────────────────────────────────────────
        hint = self._font_hint.render(
            "↑ ↓ Navigeren   Enter Selecteren   Esc Annuleren",
            True, COLOR_FB_DIM)
        self.screen.blit(hint, hint.get_rect(
            centerx=px + pw // 2, bottom=py + ph - 8))



# ══════════════════════════════════════════════════════════════════════════════
# EmuPicker – kies of stel een emulator in voor een console
# ══════════════════════════════════════════════════════════════════════════════

class EmuPicker:
    """
    Overlay om een emulator te kiezen of in te stellen.
    - Bovenste sectie: lijst van bekende presets
    - Onderste sectie: vrij tekstveld voor eigen commando

    Input via InputHandler actions.
    Geeft terug:
      None      – nog bezig
      "CANCEL"  – Esc
      str       – gekozen/getypte emulator_cmd
    """

    def __init__(self, screen: pygame.Surface, base_dir: str,
                 console_name: str, presets: list,
                 current_cmd: str, console_idx: int):
        self.screen       = screen
        self.base_dir     = base_dir
        self.console_name = console_name
        self.presets      = presets   # [(label, cmd), ...]
        self.console_idx  = console_idx
        self.current_cmd  = current_cmd

        self._font       = pygame.font.SysFont("arial", 15)
        self._font_small = pygame.font.SysFont("arial", 13)
        self._font_hint  = pygame.font.SysFont("arial", 13)

        # Navigatie: "presets" of "custom"
        self._section   = "presets" if presets else "custom"
        self._sel_idx   = 0   # geselecteerde preset

        # Tekstveld voor eigen commando
        self._custom_cmd    = current_cmd
        self._cursor        = len(current_cmd)
        self._editing       = (not presets)   # direct typen als geen presets

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, actions: list):
        from input.controller import ACTION_UP, ACTION_DOWN, ACTION_SELECT, ACTION_BACK, ACTION_LEFT, ACTION_RIGHT

        # Tekstveld actief: onderschep raw keyboard events
        if self._editing:
            for event in pygame.event.get([pygame.KEYDOWN]):
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    cmd = self._custom_cmd.strip()
                    return cmd if cmd else "CANCEL"
                elif event.key == pygame.K_ESCAPE:
                    self._editing = False
                    if not self.presets:
                        return "CANCEL"
                elif event.key == pygame.K_BACKSPACE and self._cursor > 0:
                    self._custom_cmd = (self._custom_cmd[:self._cursor - 1]
                                        + self._custom_cmd[self._cursor:])
                    self._cursor -= 1
                elif event.key == pygame.K_DELETE:
                    self._custom_cmd = (self._custom_cmd[:self._cursor]
                                        + self._custom_cmd[self._cursor + 1:])
                elif event.key == pygame.K_LEFT and self._cursor > 0:
                    self._cursor -= 1
                elif event.key == pygame.K_RIGHT and self._cursor < len(self._custom_cmd):
                    self._cursor += 1
                elif event.key == pygame.K_HOME:
                    self._cursor = 0
                elif event.key == pygame.K_END:
                    self._cursor = len(self._custom_cmd)
                elif event.unicode and event.unicode.isprintable():
                    self._custom_cmd = (self._custom_cmd[:self._cursor]
                                        + event.unicode
                                        + self._custom_cmd[self._cursor:])
                    self._cursor += 1
            return None

        for action in actions:
            if action == ACTION_BACK:
                return "CANCEL"

            elif action == ACTION_UP:
                if self._section == "presets" and self._sel_idx > 0:
                    self._sel_idx -= 1
                elif self._section == "custom" and self.presets:
                    self._section = "presets"
                    self._sel_idx = len(self.presets) - 1

            elif action == ACTION_DOWN:
                if self._section == "presets":
                    if self._sel_idx < len(self.presets) - 1:
                        self._sel_idx += 1
                    else:
                        self._section = "custom"
                # custom: al onderaan

            elif action == ACTION_SELECT:
                if self._section == "presets":
                    return self.presets[self._sel_idx][1]
                elif self._section == "custom":
                    # Start typen
                    self._editing = True

        return None

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self):
        w, h = self.screen.get_size()

        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 215))
        self.screen.blit(ov, (0, 0))

        px, py = 120, 60
        pw, ph = w - 240, h - 120
        pygame.draw.rect(self.screen, (18, 18, 32),
                         pygame.Rect(px, py, pw, ph), border_radius=12)
        pygame.draw.rect(self.screen, (55, 75, 170),
                         pygame.Rect(px, py, pw, ph), width=2, border_radius=12)

        # Titel
        title = self._font.render(
            f"Emulator instellen – {self.console_name}", True, (80, 160, 255))
        self.screen.blit(title, (px + 16, py + 14))

        sep_y = py + 44
        pygame.draw.line(self.screen, (55, 75, 170),
                         (px + 8, sep_y), (px + pw - 8, sep_y))

        y = sep_y + 14

        # ── Bekende emulators ──────────────────────────────────────────────────
        if self.presets:
            hdr = self._font_small.render("Bekende emulators:", True, (100, 100, 130))
            self.screen.blit(hdr, (px + 16, y))
            y += 22

            for i, (label, cmd) in enumerate(self.presets):
                er  = pygame.Rect(px + 12, y, pw - 24, 42)
                sel = (self._section == "presets" and i == self._sel_idx)
                pygame.draw.rect(self.screen,
                                 (36, 52, 110) if sel else (22, 22, 38),
                                 er, border_radius=6)
                if sel:
                    pygame.draw.rect(self.screen, (55, 75, 170), er,
                                     width=2, border_radius=6)
                    # Vinkje als dit de huidige is
                if cmd == self.current_cmd:
                    ck = self._font_small.render("✓", True, (80, 200, 120))
                    self.screen.blit(ck, (er.x + 8, er.y + 6))

                self.screen.blit(
                    self._font.render(label, True, (220, 220, 240) if sel else (160, 160, 180)),
                    (er.x + 28, er.y + 6))
                self.screen.blit(
                    self._font_small.render(cmd, True, (80, 160, 255) if sel else (70, 70, 100)),
                    (er.x + 28, er.y + 24))
                y += 50

            y += 8
            pygame.draw.line(self.screen, (40, 40, 60),
                             (px + 12, y), (px + pw - 12, y))
            y += 12

        # ── Eigen commando ─────────────────────────────────────────────────────
        hdr2 = self._font_small.render("Eigen commando:", True, (100, 100, 130))
        self.screen.blit(hdr2, (px + 16, y))
        y += 22

        fr = pygame.Rect(px + 12, y, pw - 24, 36)
        is_custom_sel = (self._section == "custom")
        pygame.draw.rect(self.screen,
                         (30, 30, 50) if not self._editing else (10, 10, 28),
                         fr, border_radius=6)
        pygame.draw.rect(self.screen,
                         (80, 160, 255) if self._editing else
                         ((55, 75, 170) if is_custom_sel else (40, 40, 60)),
                         fr, width=2 if (self._editing or is_custom_sel) else 1,
                         border_radius=6)

        # Toon commando met cursor
        disp = self._custom_cmd
        cur  = self._cursor
        show_cur = self._editing and (pygame.time.get_ticks() // 500) % 2 == 0
        render_text = disp[:cur] + ("|" if show_cur else " ") + disp[cur:]
        max_chars = 70
        if len(render_text) > max_chars:
            render_text = "…" + render_text[-(max_chars - 1):]
        self.screen.blit(
            self._font_small.render(render_text, True,
                                     (220, 220, 240) if self._editing else (120, 120, 150)),
            (fr.x + 8, fr.centery - 7))

        if not self._editing and is_custom_sel:
            enter_lbl = self._font_small.render("Enter om te typen", True, (80, 160, 255))
            self.screen.blit(enter_lbl, enter_lbl.get_rect(midright=(fr.right - 8, fr.centery)))

        y += 46

        # Huidige instelling
        if self.current_cmd:
            cur_lbl = self._font_small.render(
                f"Huidige instelling:  {self.current_cmd[:60]}", True, (70, 70, 100))
            self.screen.blit(cur_lbl, (px + 16, y))

        # Hint
        if self._editing:
            hints = "Typ commando   Enter Opslaan   Esc Annuleren"
        else:
            hints = "↑ ↓ Navigeren   Enter Selecteren   Esc Sluiten"
        hint = self._font_hint.render(hints, True, (80, 80, 110))
        self.screen.blit(hint, hint.get_rect(
            centerx=px + pw // 2, bottom=py + ph - 8))


class TextEditor:
    """
    Eenvoudige teksteditor overlay voor het bewerken van settings.
    """

    def __init__(self, screen: pygame.Surface, label: str, initial_text: str = ""):
        self.screen = screen
        self.label = label
        self.text = initial_text
        self.cursor = len(initial_text)

        self._font = pygame.font.SysFont("arial", 16)
        self._font_hint = pygame.font.SysFont("arial", 13)

    def update(self, events: list):
        """Verwerk keyboard events. Geeft terug: None, 'SAVE', of 'CANCEL'."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return "SAVE"
                elif event.key == pygame.K_ESCAPE:
                    return "CANCEL"
                elif event.key == pygame.K_BACKSPACE and self.cursor > 0:
                    self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                    self.cursor -= 1
                elif event.key == pygame.K_DELETE:
                    self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
                elif event.key == pygame.K_LEFT and self.cursor > 0:
                    self.cursor -= 1
                elif event.key == pygame.K_RIGHT and self.cursor < len(self.text):
                    self.cursor += 1
                elif event.key == pygame.K_HOME:
                    self.cursor = 0
                elif event.key == pygame.K_END:
                    self.cursor = len(self.text)
                elif event.unicode and event.unicode.isprintable():
                    self.text = self.text[:self.cursor] + event.unicode + self.text[self.cursor:]
                    self.cursor += 1
        return None

    def draw(self):
        w, h = self.screen.get_size()

        # Overlay
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 220))
        self.screen.blit(ov, (0, 0))

        # Paneel
        px, py = 200, 200
        pw, ph = w - 400, 200
        pygame.draw.rect(self.screen, (18, 18, 32), pygame.Rect(px, py, pw, ph), border_radius=12)
        pygame.draw.rect(self.screen, (55, 75, 170), pygame.Rect(px, py, pw, ph), width=2, border_radius=12)

        # Titel
        title = self._font.render(self.label, True, (80, 160, 255))
        self.screen.blit(title, (px + 16, py + 16))

        # Tekstveld
        field_y = py + 50
        field_h = 40
        field_r = pygame.Rect(px + 16, field_y, pw - 32, field_h)
        pygame.draw.rect(self.screen, (10, 10, 28), field_r, border_radius=6)
        pygame.draw.rect(self.screen, (80, 160, 255), field_r, width=2, border_radius=6)

        # Toon tekst met cursor
        show_cur = (pygame.time.get_ticks() // 500) % 2 == 0
        render_text = self.text[:self.cursor] + ("|" if show_cur else " ") + self.text[self.cursor:]
        max_chars = 60
        if len(render_text) > max_chars:
            render_text = "…" + render_text[-(max_chars - 1):]
        self.screen.blit(self._font.render(render_text, True, (220, 220, 240)), (field_r.x + 10, field_r.centery - 8))

        # Hint
        hint = self._font_hint.render("Typ tekst   Enter Opslaan   Esc Annuleren", True, (100, 100, 130))
        self.screen.blit(hint, hint.get_rect(centerx=px + pw // 2, bottom=py + ph - 12))


class MenuScreen:
    """
    Menu-overlay.
    parent_screen: het scherm waarnaartoe we teruggaan bij sluiten.
    """

    def __init__(self, screen: pygame.Surface, config_manager,
                 input_handler, parent_screen):
        self.screen  = screen
        self.cfg     = config_manager
        self.input   = input_handler
        self.parent  = parent_screen

        self._font_tab    = pygame.font.SysFont("arial", 16, bold=True)
        self._font_title  = pygame.font.SysFont("arial", 22, bold=True)
        self._font_item   = pygame.font.SysFont("arial", 15)
        self._font_hint   = pygame.font.SysFont("arial", 13)
        self._font_ph     = pygame.font.SysFont("arial", 14)

        self._tab_idx      = 0      # Geselecteerde tab
        self._focus        = "tabs" # "tabs" of "content"
        self._item_idx     = 0      # Geselecteerde rij in content
        self._scroll_y     = 0      # Scroll-offset in content
        self._dirty        = False  # Zijn er onopgeslagen wijzigingen?

        # Werk op een kopie van de console-lijst zodat we pas opslaan bij sluiten
        import copy
        self._consoles = copy.deepcopy(self.cfg.consoles)

        # Instellingen – werk op een kopie van settings dict
        self._settings   = copy.deepcopy(self.cfg.settings)
        self._bg_preview = None   # Geladen preview-afbeelding
        self._picker: "BackgroundPicker | None" = None
        self._emu_picker: "EmuPicker | None" = None
        self._text_editor: "TextEditor | None" = None
        self._scan_messages: dict = {}
        self._scan_timer:    dict = {}

        # Scraper-service initialiseren
        from scraper.scraper_service import ScraperService
        self._scraper_svc = ScraperService(self.cfg)

        self._load_bg_preview()

    def needs_raw_input(self) -> bool:
        """Geeft True terug als dit scherm directe keyboard input nodig heeft."""
        return self._text_editor is not None

    # ── Input verwerken ────────────────────────────────────────────────────────

    def update(self, dt: float, events: list = None):
        # TextEditor actief?
        if self._text_editor is not None:
            if events is None:
                events = pygame.event.get()
            print(f"[MenuScreen] TextEditor actief, {len(events)} events doorgegeven")
            result = self._text_editor.update(events)
            print(f"[MenuScreen] TextEditor result: {result}, tekst: '{self._text_editor.text}'")
            if result == "SAVE":
                self._settings[self._text_editor.setting_id] = self._text_editor.text
                self._dirty = True
                setting_id = self._text_editor.setting_id
                self._text_editor = None
                # Herlaad scraper credentials als IGDB settings gewijzigd
                if setting_id in ("igdb_client_id", "igdb_client_secret"):
                    self._scraper_svc.reload_credentials()
            elif result == "CANCEL":
                self._text_editor = None
            return None

        # Picker actief? Geef acties door via InputHandler (geen eigen event.get()).
        if self._picker is not None:
            actions = self.input.consume_actions()
            result  = self._picker.update(actions)
            if result == "CANCEL":
                self._picker = None
            elif result is not None:
                self._settings["background_image"] = result
                self._dirty = True
                self._load_bg_preview()
                self._picker = None
            return None

        # EmuPicker actief?
        if self._emu_picker is not None:
            actions = self.input.consume_actions()
            result  = self._emu_picker.update(actions)
            if result == "CANCEL":
                self._emu_picker = None
            elif result is not None:
                # Sla het gekozen emulator commando op
                self._consoles[self._item_idx]["emulator_cmd"] = result
                self._dirty = True
                self._emu_picker = None
            return None

        # Voeg PageUp/PageDn toe aan de input-handler als extra acties
        raw_actions = self.input.consume_actions()
        actions = self._enrich_actions(raw_actions)

        for action in actions:
            if self._focus == "tabs":
                result = self._handle_tabs(action)
            else:
                result = self._handle_content(action)

            if result == "CLOSE":
                self._save_if_dirty()
                return self.parent

        return None

    def _enrich_actions(self, actions: list) -> list:
        """
        Voeg controller shoulder-buttons en PageUp/PageDn toe als
        move_item_up / move_item_down acties.
        We pollen hier de pygame-event queue niet opnieuw;
        in plaats daarvan checken we de keyboard-state.
        """
        keys = pygame.key.get_pressed()
        if keys[pygame.K_PAGEUP]:
            if ACTION_MOVE_UP not in actions:
                actions.append(ACTION_MOVE_UP)
        if keys[pygame.K_PAGEDOWN]:
            if ACTION_MOVE_DOWN not in actions:
                actions.append(ACTION_MOVE_DOWN)
        if keys[pygame.K_s]:
            if "scan" not in actions:
                actions.append("scan")
        return actions

    def _handle_tabs(self, action: str):
        if action == ACTION_UP and self._tab_idx > 0:
            self._tab_idx -= 1
            self._item_idx = 0
            self._scroll_y = 0
        elif action == ACTION_DOWN and self._tab_idx < len(TABS) - 1:
            self._tab_idx += 1
            self._item_idx = 0
            self._scroll_y = 0
        elif action in (ACTION_RIGHT, ACTION_SELECT):
            self._focus    = "content"
            self._item_idx = 0
            self._scroll_y = 0
        elif action in (ACTION_BACK, ACTION_MENU):
            return "CLOSE"

    def _handle_content(self, action: str):
        tab = TABS[self._tab_idx]["id"]

        if action in (ACTION_LEFT, ACTION_BACK):
            self._focus = "tabs"
            return

        if tab == "consoles":
            n = len(self._consoles)
            if action == ACTION_UP and self._item_idx > 0:
                self._item_idx -= 1
            elif action == ACTION_DOWN and self._item_idx < n - 1:
                self._item_idx += 1
            elif action == ACTION_SELECT:
                self._toggle_visible(self._item_idx)
            elif action == ACTION_MOVE_UP:
                self._move_console(self._item_idx, -1)
            elif action == ACTION_MOVE_DOWN:
                self._move_console(self._item_idx, +1)

        elif tab == "emulators":
            self._handle_emulators(action)

        elif tab == "instellingen":
            self._handle_settings(action)

        elif tab == "scraper":
            self._handle_scraper(action)

        elif tab == "server":
            self._handle_server(action)

        self._clamp_scroll()

        # Verwijder scan-berichten na 3 seconden
        now = pygame.time.get_ticks()
        for idx in list(self._scan_timer.keys()):
            if now - self._scan_timer[idx] > 3000:
                self._scan_messages.pop(idx, None)
                self._scan_timer.pop(idx, None)

    # ── Console-acties ─────────────────────────────────────────────────────────

    def _toggle_visible(self, idx: int):
        self._consoles[idx]["visible"] = not self._consoles[idx].get("visible", True)
        self._dirty = True

    def _move_console(self, idx: int, direction: int):
        new_idx = idx + direction
        n = len(self._consoles)
        if 0 <= new_idx < n:
            self._consoles[idx], self._consoles[new_idx] = (
                self._consoles[new_idx], self._consoles[idx]
            )
            self._item_idx = new_idx
            self._dirty = True

    def _handle_settings(self, action: str):
        n    = len(SETTINGS_ITEMS)
        item = SETTINGS_ITEMS[self._item_idx]

        if action == ACTION_UP and self._item_idx > 0:
            self._item_idx -= 1
        elif action == ACTION_DOWN and self._item_idx < n - 1:
            self._item_idx += 1
        elif action == ACTION_SELECT:
            if item["type"] == "bool":
                self._settings[item["id"]] = not self._settings.get(item["id"], False)
                self._dirty = True
            elif item["type"] == "path":
                # Open bestandsbrowser, start in huidige map of base_dir
                start = self._settings.get(item["id"], "")
                if start:
                    start_dir = os.path.dirname(self.cfg.resolve_path(start))
                else:
                    start_dir = self.cfg.base_dir
                if not os.path.isdir(start_dir):
                    start_dir = self.cfg.base_dir
                self._picker = BackgroundPicker(
                    self.screen, self.cfg.base_dir
                )
            elif item["type"] == "text":
                # Open teksteditor overlay
                self._text_editor = TextEditor(
                    self.screen,
                    item["label"],
                    str(self._settings.get(item["id"], ""))
                )
                self._text_editor.setting_id = item["id"]
            elif item["type"] == "action":
                # Voer de actie uit
                if item["id"] == "refresh_background":
                    # Herlaad de achtergrond op het parent scherm
                    if hasattr(self.parent, 'reload_background'):
                        bg_path = self._settings.get("background_image")
                        print(f"[Menu] Refreshing background with path: {bg_path}")
                        # Sla eerst de huidige settings op zodat de nieuwe achtergrond wordt gebruikt
                        self.cfg.settings = self._settings
                        self.cfg.save_settings()
                        print(f"[Menu] Settings saved")
                        # Herlaad met de nieuwe achtergrond
                        self.parent.reload_background(bg_path)
                        print(f"[Menu] Background reloaded")
                        # Update ook de preview in het menu
                        self._load_bg_preview()

    def _handle_emulators(self, action: str):
        n = len(self._consoles)

        if action == ACTION_UP and self._item_idx > 0:
            self._item_idx -= 1
        elif action == ACTION_DOWN and self._item_idx < n - 1:
            self._item_idx += 1
        elif action == ACTION_SELECT:
            # Open emulator picker voor geselecteerde console
            console = self._consoles[self._item_idx]
            console_id = console.get("id", "")
            console_name = console["name"]
            current_cmd = console.get("emulator_cmd", "")

            # Haal presets op voor deze console
            presets = EMULATOR_PRESETS.get(console_id, [])

            self._emu_picker = EmuPicker(
                self.screen, self.cfg.base_dir, console_name, presets, current_cmd, self._item_idx
            )

    def _handle_scraper(self, action: str):
        # Scraper-tab toont alleen informatie, geen interactieve items
        # Alleen terug naar tabs ondersteunen
        if action in (ACTION_LEFT, ACTION_BACK):
            self._focus = "tabs"

    def _handle_server(self, action: str):
        # Server-tab heeft 2 items: URL input (0) en Open knop (1)
        n_items = 2

        if action == ACTION_UP and self._item_idx > 0:
            self._item_idx -= 1
        elif action == ACTION_DOWN and self._item_idx < n_items - 1:
            self._item_idx += 1
        elif action == ACTION_SELECT:
            if self._item_idx == 0:
                # URL input: open teksteditor
                self._text_editor = TextEditor(
                    self.screen,
                    "Server URL",
                    str(self._settings.get("server_url", ""))
                )
                self._text_editor.setting_id = "server_url"
            elif self._item_idx == 1:
                # Open knop: open URL in browser
                url = self._settings.get("server_url", "")
                if url:
                    import webbrowser
                    webbrowser.open(url)

    def _load_bg_preview(self):
        """Laad achtergrond-preview op basis van huidig settings-pad."""
        path = self._settings.get("background_image", "")
        if path:
            abs_path = self.cfg.resolve_path(path)
            if abs_path and __import__("os").path.exists(abs_path):
                try:
                    img = __import__("pygame").image.load(abs_path).convert()
                    self._bg_preview = __import__("pygame").transform.smoothscale(img, (320, 180))
                    return
                except Exception:
                    pass
        self._bg_preview = None

    def _clamp_scroll(self):
        """Scroll content mee zodat geselecteerd item zichtbaar blijft."""
        w, h   = self.screen.get_size()
        area_h = h - 120  # beschikbare hoogte in content-panel

        # Gebruik verschillende item hoogtes en spacing voor verschillende tabs
        tab = TABS[self._tab_idx]["id"]
        if tab == "consoles":
            item_h = 82   # De werkelijke hoogte in _draw_consoles_tab
            spacing = 8    # Spacing in _draw_consoles_tab
        elif tab == "emulators":
            item_h = 60   # De werkelijke hoogte in _draw_emulators_tab
            spacing = 8    # Spacing in _draw_emulators_tab
        elif tab == "instellingen":
            item_h = ITEM_H  # Hoogte in _draw_instellingen_tab
            spacing = 10     # Spacing in _draw_instellingen_tab
        elif tab == "scraper":
            # Scraper-tab heeft geen scroll (alleen tekst)
            return
        elif tab == "server":
            # Server-tab heeft geen scroll (vaste items)
            return
        else:
            item_h = ITEM_H  # Standaard hoogte voor andere tabs
            spacing = 8       # Standaard spacing

        item_y = self._item_idx * (item_h + spacing)
        if item_y - self._scroll_y + item_h > area_h:
            self._scroll_y = item_y + item_h - area_h
        if item_y < self._scroll_y:
            self._scroll_y = item_y

    # ── Opslaan ────────────────────────────────────────────────────────────────

    def _save_if_dirty(self):
        if self._dirty:
            self.cfg.consoles = self._consoles
            self.cfg.save_consoles()
            self.cfg.settings = self._settings
            self.cfg.save_settings()
            # Herlaad de achtergrond op het parent scherm als deze is gewijzigd
            if hasattr(self.parent, 'reload_background'):
                self.parent.reload_background()
            self._dirty = False

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self):
        w, h = self.screen.get_size()

        # TextEditor bovenop alles
        if self._text_editor is not None:
            self._text_editor.draw()
            return

        # EmuPicker bovenop alles
        if self._emu_picker is not None:
            self._emu_picker.draw()
            return

        # Picker tekent zichzelf bovenop alles
        if self._picker is not None:
            self._picker.draw()
            return

        # Semi-transparante overlay over het vorige scherm
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Menu-paneel (niet volledig fullscreen – laat wat context zien)
        panel_x = 60
        panel_y = 40
        panel_w = w - 120
        panel_h = h - 80
        panel   = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        _draw_rr(self.screen, COLOR_PANEL, panel, 14)
        pygame.draw.rect(self.screen, COLOR_BORDER, panel, width=2, border_radius=14)

        # Titel
        title = self._font_title.render("Menu", True, COLOR_ACCENT)
        self.screen.blit(title, (panel_x + 20, panel_y + 16))

        # Scheidingslijn onder titel
        sep_y = panel_y + 50
        pygame.draw.line(self.screen, COLOR_BORDER,
                         (panel_x + 10, sep_y), (panel_x + panel_w - 10, sep_y))

        # Tab-kolom links
        tab_area = pygame.Rect(panel_x + 10, sep_y + 10,
                               TAB_W, panel_h - 70)
        self._draw_tabs(tab_area)

        # Content rechts
        content_x = panel_x + TAB_W + 20
        content_y = sep_y + 10
        content_w = panel_w - TAB_W - 30
        content_h = panel_h - 70
        content_area = pygame.Rect(content_x, content_y, content_w, content_h)
        self._draw_content(content_area)

        # Hint onderaan
        if self._focus == "tabs":
            hints = "↑ ↓ Tab wisselen   → / Enter Inhoud   Esc Sluiten"
        else:
            tab = TABS[self._tab_idx]["id"]
            if tab == "consoles":
                hints = "↑ ↓ Navigeren   Enter Zichtbaar aan/uit   PgUp/PgDn Volgorde   S Scan   ← Tabs"
            elif tab == "emulators":
                hints = "↑ ↓ Navigeren   Enter Emulator instellen   ← Tabs"
            elif tab == "instellingen":
                hints = "↑ ↓ Navigeren   Enter Selecteren / Toggle   ← Tabs"
            elif tab == "scraper":
                hints = "← Terug naar tabs   Esc Sluiten"
            elif tab == "server":
                hints = "↑ ↓ Navigeren   Enter Selecteren / Bewerken / Openen   ← Tabs"
            else:
                hints = "← Terug naar tabs   Esc Sluiten"
        hint = self._font_hint.render(hints, True, COLOR_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(
            centerx=panel_x + panel_w // 2,
            bottom=panel_y + panel_h - 8
        ))

    def _draw_tabs(self, area: pygame.Rect):
        for i, tab in enumerate(TABS):
            ty     = area.y + i * (48 + 8)
            rect   = pygame.Rect(area.x, ty, TAB_W - 10, 48)
            is_sel = (i == self._tab_idx)
            is_active = is_sel and self._focus == "content"

            if is_active:
                bg = COLOR_TAB_ACTIVE
            elif is_sel:
                bg = COLOR_TAB_SEL
            else:
                bg = COLOR_TAB

            _draw_rr(self.screen, bg, rect, TAB_RADIUS)

            if is_sel:
                pygame.draw.rect(self.screen, COLOR_BORDER, rect,
                                 width=2, border_radius=TAB_RADIUS)

            lbl = self._font_tab.render(tab["label"], True,
                                        COLOR_TEXT if is_sel else COLOR_TEXT_DIM)
            self.screen.blit(lbl, lbl.get_rect(
                midleft=(rect.x + 14, rect.centery)
            ))

    def _draw_content(self, area: pygame.Rect):
        tab = TABS[self._tab_idx]["id"]
        _draw_rr(self.screen, COLOR_CONTENT, area, 10)

        if tab == "consoles":
            self._draw_consoles_tab(area)
        elif tab == "emulators":
            self._draw_emulators_tab(area)
        elif tab == "instellingen":
            self._draw_instellingen_tab(area)
        elif tab == "scraper":
            self._draw_scraper_tab(area)
        elif tab == "server":
            self._draw_server_tab(area)

    # ── Consoles-tab ───────────────────────────────────────────────────────────

    def _draw_consoles_tab(self, area: pygame.Rect):
        self.screen.set_clip(area)
        pad_x   = area.x + 12
        start_y = area.y + 10
        item_h  = 82   # ruimte voor naam, roms_path, emulator + knoppen

        for i, console in enumerate(self._consoles):
            iy     = start_y + i * (item_h + 8) - int(self._scroll_y)
            item_r = pygame.Rect(pad_x, iy, area.w - 24, item_h)

            if iy + item_h < area.y or iy > area.y + area.h:
                continue

            is_sel = (i == self._item_idx and self._focus == "content")
            _draw_rr(self.screen, COLOR_ITEM_SEL if is_sel else COLOR_ITEM, item_r, ITEM_RADIUS)
            if is_sel:
                pygame.draw.rect(self.screen, COLOR_BORDER, item_r,
                                 width=2, border_radius=ITEM_RADIUS)

            # Checkbox
            visible = console.get("visible", True)
            chk_r   = pygame.Rect(item_r.x + 12, item_r.y + 10, 22, 22)
            _draw_rr(self.screen, COLOR_CHECK_ON if visible else COLOR_CHECK_OFF, chk_r, 5)
            if visible:
                chk_lbl = self._font_item.render("✓", True, (255, 255, 255))
                self.screen.blit(chk_lbl, chk_lbl.get_rect(center=chk_r.center))

            # Console naam
            name_lbl = self._font_item.render(
                console["name"], True, COLOR_TEXT if visible else COLOR_TEXT_DIM)
            self.screen.blit(name_lbl, (chk_r.right + 10, item_r.y + 8))

            # Aantal games rechts
            n_games = len(console.get("games", []))
            cnt_lbl = self._font_hint.render(
                f"{n_games} game(s)", True, COLOR_ACCENT if n_games > 0 else COLOR_TEXT_DIM)
            self.screen.blit(cnt_lbl, cnt_lbl.get_rect(midright=(item_r.right - 14, item_r.y + 20)))

            # ROM-map (tweede rij)
            roms_path = console.get("roms_path", "(niet ingesteld)")
            if len(roms_path) > 32:
                roms_path = "…" + roms_path[-31:]
            self.screen.blit(
                self._font_hint.render(f"ROMs: {roms_path}", True, COLOR_TEXT_DIM),
                (chk_r.right + 10, item_r.y + 32))

            # Emulator (derde rij)
            emu_cmd = console.get("emulator_cmd", "")
            emu_short = emu_cmd.split()[0] if emu_cmd else "(niet ingesteld)"
            if len(emu_short) > 32:
                emu_short = "…" + emu_short[-31:]
            self.screen.blit(
                self._font_hint.render(f"Emu:  {emu_short}", True,
                                        COLOR_ACCENT if emu_cmd else COLOR_TEXT_DIM),
                (chk_r.right + 10, item_r.y + 50))

            # Knoppen rechts (alleen als geselecteerd)
            if is_sel:
                scan_r = pygame.Rect(item_r.right - 224, item_r.y + 48, 96, 24)
                _draw_rr(self.screen, COLOR_TAB_ACTIVE, scan_r, 5)
                pygame.draw.rect(self.screen, COLOR_BORDER, scan_r, width=1, border_radius=5)
                self.screen.blit(
                    self._font_hint.render("Scan [S]", True, COLOR_TEXT),
                    self._font_hint.render("Scan [S]", True, COLOR_TEXT).get_rect(center=scan_r.center))

                emu_r = pygame.Rect(item_r.right - 118, item_r.y + 48, 104, 24)
                _draw_rr(self.screen, (50, 35, 80), emu_r, 5)
                pygame.draw.rect(self.screen, COLOR_BORDER, emu_r, width=1, border_radius=5)
                self.screen.blit(
                    self._font_hint.render("Emulator [E]", True, COLOR_TEXT),
                    self._font_hint.render("Emulator [E]", True, COLOR_TEXT).get_rect(center=emu_r.center))

            # Scan-resultaat bericht
            scan_msg = self._scan_messages.get(i, "")
            if scan_msg:
                msg_lbl = self._font_hint.render(scan_msg, True, COLOR_CHECK_ON)
                self.screen.blit(msg_lbl, msg_lbl.get_rect(midright=(item_r.right - 14, item_r.bottom - 8)))

        self.screen.set_clip(None)

        # Scrollbar
        total_h = len(self._consoles) * (item_h + 8)
        if total_h > area.h:
            bar_h = max(30, int(area.h * area.h / total_h))
            bar_y = area.y + int(self._scroll_y / max(total_h - area.h, 1) * (area.h - bar_h))
            _draw_rr(self.screen, COLOR_BORDER, pygame.Rect(area.right - 8, bar_y, 5, bar_h), 3)

    # ── Emulators-tab ───────────────────────────────────────────────────────────

    def _draw_emulators_tab(self, area: pygame.Rect):
        self.screen.set_clip(area)
        pad_x   = area.x + 12
        start_y = area.y + 10
        item_h  = 60   # ruimte voor console naam + emulator info

        for i, console in enumerate(self._consoles):
            iy     = start_y + i * (item_h + 8) - int(self._scroll_y)
            item_r = pygame.Rect(pad_x, iy, area.w - 24, item_h)

            if iy + item_h < area.y or iy > area.y + area.h:
                continue

            is_sel = (i == self._item_idx and self._focus == "content")
            _draw_rr(self.screen, COLOR_ITEM_SEL if is_sel else COLOR_ITEM, item_r, ITEM_RADIUS)
            if is_sel:
                pygame.draw.rect(self.screen, COLOR_BORDER, item_r,
                                 width=2, border_radius=ITEM_RADIUS)

            # Console naam
            name_lbl = self._font_item.render(console["name"], True, COLOR_TEXT)
            self.screen.blit(name_lbl, (item_r.x + 12, item_r.y + 8))

            # Huidige emulator
            emu_cmd = console.get("emulator_cmd", "")
            if emu_cmd:
                emu_short = emu_cmd.split()[0] if emu_cmd else "(niet ingesteld)"
                if len(emu_short) > 40:
                    emu_short = "…" + emu_short[-39:]
                emu_lbl = self._font_hint.render(f"Emulator: {emu_short}", True, COLOR_TEXT_DIM)
                self.screen.blit(emu_lbl, (item_r.x + 12, item_r.y + 32))
            else:
                no_emu_lbl = self._font_hint.render("Emulator: (niet ingesteld)", True, COLOR_ACCENT)
                self.screen.blit(no_emu_lbl, (item_r.x + 12, item_r.y + 32))

            # Configuratie knop
            if is_sel:
                cfg_r = pygame.Rect(item_r.right - 100, item_r.y + 18, 80, 24)
                _draw_rr(self.screen, (50, 35, 80), cfg_r, 5)
                pygame.draw.rect(self.screen, COLOR_BORDER, cfg_r, width=1, border_radius=5)
                self.screen.blit(
                    self._font_hint.render("Configureren", True, COLOR_TEXT),
                    self._font_hint.render("Configureren", True, COLOR_TEXT).get_rect(center=cfg_r.center))

        self.screen.set_clip(None)

    # ── Instellingen-tab ──────────────────────────────────────────────────────────

    def _draw_instellingen_tab(self, area: pygame.Rect):
        pad_x   = area.x + 16
        pad_y   = area.y + 16
        item_w  = area.w - 32

        for i, item in enumerate(SETTINGS_ITEMS):
            iy     = pad_y + i * (ITEM_H + 10)
            rect   = pygame.Rect(pad_x, iy, item_w, ITEM_H)
            is_sel = (i == self._item_idx and self._focus == "content")

            bg = COLOR_ITEM_SEL if is_sel else COLOR_ITEM
            _draw_rr(self.screen, bg, rect, ITEM_RADIUS)
            if is_sel:
                pygame.draw.rect(self.screen, COLOR_BORDER, rect,
                                 width=2, border_radius=ITEM_RADIUS)

            # Label links
            lbl = self._font_item.render(item["label"], True,
                                          COLOR_TEXT if is_sel else COLOR_TEXT_DIM)
            self.screen.blit(lbl, lbl.get_rect(midleft=(rect.x + 14, rect.centery)))

            # Waarde / control rechts
            val = self._settings.get(item["id"])

            if item["type"] == "bool":
                # Toggle-switch
                sw_w, sw_h = 48, 24
                sw_r = pygame.Rect(rect.right - sw_w - 12,
                                   rect.centery - sw_h // 2, sw_w, sw_h)
                sw_bg = COLOR_CHECK_ON if val else COLOR_CHECK_OFF
                _draw_rr(self.screen, sw_bg, sw_r, sw_h // 2)
                knob_x = sw_r.right - sw_h // 2 - 2 if val else sw_r.x + sw_h // 2 + 2
                pygame.draw.circle(self.screen, (255, 255, 255),
                                   (knob_x, sw_r.centery), sw_h // 2 - 3)

            elif item["type"] == "path":
                # Toon huidig pad (afgekort) + "Bladeren"-knop
                display_val = str(val) if val else "(niet ingesteld)"
                if len(display_val) > 32:
                    display_val = "…" + display_val[-31:]
                v_surf = self._font_hint.render(display_val, True,
                                                 COLOR_ACCENT if val else COLOR_TEXT_DIM)
                self.screen.blit(v_surf, v_surf.get_rect(
                    midleft=(rect.x + 160, rect.centery)))
                # Bladeren-label rechts
                if is_sel:
                    browse_lbl = self._font_hint.render("[ Bladeren → Enter ]", True, COLOR_ACCENT)
                    self.screen.blit(browse_lbl, browse_lbl.get_rect(
                        midright=(rect.right - 10, rect.centery)))

            elif item["type"] == "text":
                # Toon huidige waarde
                display_val = str(val) if val else "(niet ingesteld)"
                if len(display_val) > 40:
                    display_val = "…" + display_val[-39:]
                v_surf = self._font_hint.render(display_val, True,
                                                 COLOR_ACCENT if val else COLOR_TEXT_DIM)
                self.screen.blit(v_surf, v_surf.get_rect(
                    midleft=(rect.x + 160, rect.centery)))
                if is_sel:
                    edit_lbl = self._font_hint.render("[ Enter om te bewerken ]", True, COLOR_ACCENT)
                    self.screen.blit(edit_lbl, edit_lbl.get_rect(
                        midright=(rect.right - 10, rect.centery)))

            elif item["type"] == "action":
                # Toon een actie-knop
                if is_sel:
                    btn_lbl = self._font_hint.render("[ Enter om uit te voeren ]", True, COLOR_ACCENT)
                    self.screen.blit(btn_lbl, btn_lbl.get_rect(
                        midright=(rect.right - 10, rect.centery)))
                else:
                    hint_lbl = self._font_hint.render("Actie", True, COLOR_TEXT_DIM)
                    self.screen.blit(hint_lbl, hint_lbl.get_rect(
                        midleft=(rect.x + 160, rect.centery)))

        # Preview achtergrond
        prev_y = pad_y + len(SETTINGS_ITEMS) * (ITEM_H + 10) + 16
        self._draw_bg_preview_section(area, pad_x, prev_y, item_w)

    def _draw_bg_preview_section(self, area: pygame.Rect,
                                  x: int, y: int, w: int):
        """Toon een live preview van de achtergrondafbeelding."""
        lbl = self._font_hint.render("Preview achtergrond:", True, COLOR_TEXT_DIM)
        self.screen.blit(lbl, (x, y))
        y += 22

        prev_w, prev_h = 320, 180
        prev_r = pygame.Rect(x, y, prev_w, prev_h)

        if self._bg_preview:
            self.screen.blit(self._bg_preview, prev_r)
            pygame.draw.rect(self.screen, COLOR_BORDER, prev_r, width=1, border_radius=4)
        else:
            _draw_rr(self.screen, COLOR_PLACEHOLDER, prev_r, 4)
            no_lbl = self._font_hint.render("Geen afbeelding", True, COLOR_TEXT_DIM)
            self.screen.blit(no_lbl, no_lbl.get_rect(center=prev_r.center))

    # ── Scraper-tab ─────────────────────────────────────────────────────────────

    def _draw_scraper_tab(self, area: pygame.Rect):
        pad_x = area.x + 20
        pad_y = area.y + 20
        y = pad_y

        # Titel
        title = self._font_title.render("🔍 Cover Scraper (IGDB)", True, COLOR_ACCENT)
        self.screen.blit(title, (pad_x, y))
        y += 36

        # Status
        is_configured = self._scraper_svc.is_configured()
        if is_configured:
            status_text = "✓ IGDB geconfigureerd"
            status_color = COLOR_CHECK_ON
        else:
            status_text = "✗ IGDB niet geconfigureerd"
            status_color = COLOR_ERR

        status = self._font_item.render(status_text, True, status_color)
        self.screen.blit(status, (pad_x, y))
        y += 32

        # Instructies
        if not is_configured:
            instructions = [
                "Om de scraper te gebruiken, moet je eerst IGDB credentials instellen:",
                "",
                "1. Ga naar https://api.igdb.com/signup",
                "2. Maak een applicatie aan",
                "3. Kopieer de Client ID en Client Secret",
                "4. Ga naar het tabblad 'Instellingen' hierboven",
                "5. Vul de IGDB Client ID en Secret in",
                "",
                "Na configuratie kun je covers scrapen vanuit de game-detailpagina."
            ]
            for line in instructions:
                if line:
                    lbl = self._font_hint.render(line, True, COLOR_TEXT_DIM)
                    self.screen.blit(lbl, (pad_x, y))
                    y += 22
                else:
                    y += 12
        else:
            instructions = [
                "De scraper is geconfigureerd en klaar voor gebruik.",
                "",
                "Gebruik de scraper vanuit de game-detailpagina:",
                "1. Navigeer naar een game",
                "2. Druk op de scraper-knop",
                "3. Zoek naar de juiste game in IGDB",
                "4. Selecteer een cover om op te slaan",
                "",
                "De cover wordt opgeslagen in assets/covers/<console>/"
            ]
            for line in instructions:
                if line:
                    lbl = self._font_hint.render(line, True, COLOR_TEXT_DIM)
                    self.screen.blit(lbl, (pad_x, y))
                    y += 22
                else:
                    y += 12

    # ── Server-tab ───────────────────────────────────────────────────────────────

    def _draw_server_tab(self, area: pygame.Rect):
        pad_x = area.x + 20
        pad_y = area.y + 20
        y = pad_y

        # Titel
        title = self._font_title.render("☁️  Server", True, COLOR_ACCENT)
        self.screen.blit(title, (pad_x, y))
        y += 36

        # Server URL item
        item_h = ITEM_H
        item_w = area.w - 40
        rect = pygame.Rect(pad_x, y, item_w, item_h)
        is_sel = (self._item_idx == 0 and self._focus == "content")

        bg = COLOR_ITEM_SEL if is_sel else COLOR_ITEM
        _draw_rr(self.screen, bg, rect, ITEM_RADIUS)
        if is_sel:
            pygame.draw.rect(self.screen, COLOR_BORDER, rect, width=2, border_radius=ITEM_RADIUS)

        # Label
        lbl = self._font_item.render("Server URL", True, COLOR_TEXT if is_sel else COLOR_TEXT_DIM)
        self.screen.blit(lbl, lbl.get_rect(midleft=(rect.x + 14, rect.centery)))

        # Waarde
        url = self._settings.get("server_url", "")
        display_val = url if url else "(niet ingesteld)"
        if len(display_val) > 40:
            display_val = "…" + display_val[-39:]
        v_surf = self._font_hint.render(display_val, True, COLOR_ACCENT if url else COLOR_TEXT_DIM)
        self.screen.blit(v_surf, v_surf.get_rect(midleft=(rect.x + 160, rect.centery)))

        if is_sel:
            edit_lbl = self._font_hint.render("[ Enter om te bewerken ]", True, COLOR_ACCENT)
            self.screen.blit(edit_lbl, edit_lbl.get_rect(midright=(rect.right - 10, rect.centery)))

        y += item_h + 16

        # Open URL knop
        btn_h = 44
        btn_w = 200
        btn_rect = pygame.Rect(pad_x, y, btn_w, btn_h)
        is_btn_sel = (self._item_idx == 1 and self._focus == "content")

        btn_bg = COLOR_TAB_ACTIVE if is_btn_sel else COLOR_TAB
        _draw_rr(self.screen, btn_bg, btn_rect, 8)
        if is_btn_sel:
            pygame.draw.rect(self.screen, COLOR_BORDER, btn_rect, width=2, border_radius=8)

        btn_lbl = self._font_item.render("🌐  Openen in browser", True, COLOR_TEXT)
        self.screen.blit(btn_lbl, btn_lbl.get_rect(center=btn_rect.center))

        if not url:
            hint = self._font_hint.render("(Stel eerst een URL in)", True, COLOR_TEXT_DIM)
            self.screen.blit(hint, hint.get_rect(midleft=(btn_rect.right + 16, btn_rect.centery)))

    # ── Placeholder tabs ───────────────────────────────────────────────────────

    def _draw_placeholder_tab(self, area: pygame.Rect, title: str,
                               subtitle: str, features: list):
        cx = area.centerx
        y  = area.y + 30

        # Badge "Binnenkort"
        badge_r = pygame.Rect(0, 0, 120, 28)
        badge_r.centerx = cx
        badge_r.y = y
        _draw_rr(self.screen, COLOR_PLACEHOLDER, badge_r, 14)
        badge_lbl = self._font_hint.render("Binnenkort beschikbaar", True, COLOR_TEXT_DIM)
        self.screen.blit(badge_lbl, badge_lbl.get_rect(center=badge_r.center))
        y += 44

        # Titel
        t_lbl = self._font_title.render(title, True, COLOR_TEXT)
        self.screen.blit(t_lbl, t_lbl.get_rect(centerx=cx, y=y))
        y += 36

        # Subtitel
        s_lbl = self._font_ph.render(subtitle, True, COLOR_TEXT_DIM)
        self.screen.blit(s_lbl, s_lbl.get_rect(centerx=cx, y=y))
        y += 36

        # Feature-lijst
        for feat in features:
            f_lbl = self._font_ph.render(feat, True, COLOR_TEXT_DIM)
            self.screen.blit(f_lbl, f_lbl.get_rect(centerx=cx, y=y))
            y += 26
