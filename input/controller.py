"""
input/controller.py
Uniforme input-abstractie voor keyboard én gamepad.
Elke "actie" is een string – schermen hoeven niet te weten of het keyboard of controller is.
"""

import pygame


# ── Actie-constanten (gebruik deze overal in de UI) ────────────────────────────
ACTION_LEFT    = "left"
ACTION_RIGHT   = "right"
ACTION_UP      = "up"
ACTION_DOWN    = "down"
ACTION_SELECT  = "select"
ACTION_BACK    = "back"
ACTION_MENU    = "menu"
ACTION_QUIT    = "quit"

# ── Keyboard mapping ───────────────────────────────────────────────────────────
KEY_MAP = {
    pygame.K_LEFT:      ACTION_LEFT,
    pygame.K_RIGHT:     ACTION_RIGHT,
    pygame.K_UP:        ACTION_UP,
    pygame.K_DOWN:      ACTION_DOWN,
    pygame.K_RETURN:    ACTION_SELECT,
    pygame.K_KP_ENTER:  ACTION_SELECT,
    pygame.K_SPACE:     ACTION_SELECT,
    pygame.K_ESCAPE:    ACTION_BACK,
    pygame.K_BACKSPACE: ACTION_BACK,
    pygame.K_m:         ACTION_MENU,
    pygame.K_F1:        ACTION_MENU,
    pygame.K_q:         ACTION_QUIT,
}

# ── Gamepad button mapping (generiek / Xbox-layout) ────────────────────────────
# Button indices variëren per controller, maar dit is de meest gebruikelijke mapping
BUTTON_MAP = {
    0: ACTION_SELECT,   # A / Cross
    1: ACTION_BACK,     # B / Circle
    7: ACTION_MENU,     # Start
    6: ACTION_QUIT,     # Select/Back (optioneel)
}

# D-pad hat mapping  (hat value → actie)
HAT_MAP = {
    (-1,  0): ACTION_LEFT,
    ( 1,  0): ACTION_RIGHT,
    ( 0,  1): ACTION_UP,
    ( 0, -1): ACTION_DOWN,
}

# Analoge stick – drempel
AXIS_THRESHOLD = 0.5


class InputHandler:
    """
    Verwerkt pygame-events en biedt een eenvoudige actie-queue.
    Gebruik `consume_actions()` in elke scherm-update.
    """

    def __init__(self):
        self._actions: list[str] = []
        # Voor analoge stick: debounce zodat één beweging niet 60x per seconde vuurt
        self._axis_moved = {"left": False, "right": False, "up": False, "down": False}

    def process_events(self, events: list):
        """Verwerk alle pygame-events van dit frame."""
        for event in events:

            # Keyboard
            if event.type == pygame.KEYDOWN:
                action = KEY_MAP.get(event.key)
                if action:
                    self._actions.append(action)

            # Gamepad buttons
            elif event.type == pygame.JOYBUTTONDOWN:
                action = BUTTON_MAP.get(event.button)
                if action:
                    self._actions.append(action)

            # D-pad (hat)
            elif event.type == pygame.JOYHATMOTION:
                action = HAT_MAP.get(event.value)
                if action:
                    self._actions.append(action)

            # Analoge stick (axis 0 = links/rechts, axis 1 = omhoog/omlaag)
            elif event.type == pygame.JOYAXISMOTION:
                self._handle_axis(event.axis, event.value)

    def _handle_axis(self, axis: int, value: float):
        """Vertaalt analoge stickbeweging naar directie-acties met debounce."""
        if axis == 0:  # Links/rechts
            if value < -AXIS_THRESHOLD and not self._axis_moved["left"]:
                self._actions.append(ACTION_LEFT)
                self._axis_moved["left"]  = True
                self._axis_moved["right"] = False
            elif value > AXIS_THRESHOLD and not self._axis_moved["right"]:
                self._actions.append(ACTION_RIGHT)
                self._axis_moved["right"] = True
                self._axis_moved["left"]  = False
            elif abs(value) < AXIS_THRESHOLD:
                self._axis_moved["left"]  = False
                self._axis_moved["right"] = False

        elif axis == 1:  # Omhoog/omlaag
            if value < -AXIS_THRESHOLD and not self._axis_moved["up"]:
                self._actions.append(ACTION_UP)
                self._axis_moved["up"]   = True
                self._axis_moved["down"] = False
            elif value > AXIS_THRESHOLD and not self._axis_moved["down"]:
                self._actions.append(ACTION_DOWN)
                self._axis_moved["down"] = True
                self._axis_moved["up"]   = False
            elif abs(value) < AXIS_THRESHOLD:
                self._axis_moved["up"]   = False
                self._axis_moved["down"] = False

    def consume_actions(self) -> list[str]:
        """
        Geeft alle acties van dit frame terug en wist de queue.
        Roep dit aan in het begin van elke screen.update().
        """
        actions = self._actions.copy()
        self._actions.clear()
        return actions
