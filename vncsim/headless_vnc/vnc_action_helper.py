from enum import Enum
from .rfb import RFBClient


class MouseButton(Enum):
    LEFT_BUTTON = 1
    MIDDLE_BUTTON = 2
    RIGHT_BUTTON = 4
    WHEEL_UP = 8
    WHEEL_DOWN = 16


class VncActionHelper:
    protocol:RFBClient = None

    def __init__(self):
        pass

    def set_protocol(self, protocol: RFBClient):
        self.protocol = protocol

    def click_pointer(self, x: int, y: int,
                      mouse_button: MouseButton = MouseButton.LEFT_BUTTON):
        if self.protocol:
            self.protocol.pointerEvent(x, y, buttonmask=mouse_button.value)
            self.protocol.pointerEvent(x, y, buttonmask=0)

    # For most ordinary keys, the `keysym` is the same as the corresponding ASCII value.
    # Other common keys are shown in the KEY_ constants inside `rfb.py`
    def press_key(self, keysym: int):
        if self.protocol:
            self.protocol.keyEvent(keysym, down=1)
            self.protocol.keyEvent(keysym, down=0)

    def type_text(self, word: str):
        if self.protocol:
            for c in word:
                self.press_key(ord(c))
