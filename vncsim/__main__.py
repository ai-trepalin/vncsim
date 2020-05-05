from twisted.internet import reactor
from .contracts.spell_book import SpellBook
from .contracts.spells.after_20_seconds import StartSurfingSpell
from .contracts.spells.dialog_shown import DialogShownSpell
from .headless_vnc import headless_vnc, rfb
from .headless_vnc.screen_buffer import ScreenBuffer
from .interface_hunter import toolbox
from .interface_hunter import detect_boxes, detect_text
from .interface_hunter import dialog_feature
import keyboard
import cv2 as cv


#---- VNCSim CONFIG

host = '10.211.55.3'
port = 5900
# noinspection HardcodedPassword
password = 'password'


#---- GLOBALS
image_index = 0
surfing_timeout = 20

boxes_detector = detect_boxes.DetectBoxes(detect_boxes.DefaultDetectBoxesConfig)
text_detector = detect_text.DetectText(detect_text.DefaultDetectTextConfig)

dialog_detect_text_config = detect_text.DetectTextConfig(
    east_detector_pb_path='./proto/frozen_east_text_detection.pb',
    min_confidence=0.5,
    conv_width=512,
    conv_height=64,
    margin=5,
    scale=2.0,
    tesseract_config='-l eng --oem 1 --psm 7'
)
dialog_text_detector = detect_text.DetectText(dialog_detect_text_config)


#---- SPELLS

spell_book = SpellBook()
dialog_shown_spell = DialogShownSpell()
start_surfing_spell = StartSurfingSpell()
spell_book.register_spell(dialog_shown_spell)
spell_book.register_spell(start_surfing_spell)


#---- HANDLERS

surfing_timeout_handler = None

# noinspection PyUnusedLocal
def reactor_int(self):
    if keyboard.is_pressed('esc'):
        self.stop()
    return 1


# noinspection PyUnusedLocal
def screen_buffer_flush_handler(self, buffer):
    global spell_book, dialog_shown_spell
    global surfing_timeout, surfing_timeout_handler
    global boxes_detector, text_detector, image_index

    print(f"ScreenBuffer flushed because of significant changes.")

    if surfing_timeout_handler and not surfing_timeout_handler.called:
        surfing_timeout_handler.cancel()
    if buffer:
        filename = 'assets/capture_{image_index:04}.png'
        image_index += 1
        cv2_img = toolbox.pil_to_cv2(buffer)

        dialog_detector = dialog_feature.DialogFeature(
            image_data=cv2_img,
            dialog_text_detector=dialog_text_detector,
            dialog_boxes_detector=boxes_detector,
            button_text_detector=text_detector,
            button_boxes_detector=boxes_detector
        )

        dialogs = dialog_detector.dialogs()
        # cv.imwrite(filename, cv2_img)
        # print(f"Screen saved to {filename} due to significant changes.")

        #
        # Call spells for dialogs
        #
        if len(dialogs) > 0:
            spell_book.execute_spells(dialog_shown_spell.action_name, dialogs)

        # noinspection PyUnresolvedReferences
        surfing_timeout_handler = reactor.callLater(
            surfing_timeout,
            spell_book.execute_spells,
            action_name=start_surfing_spell.action_name,
            context=None
        )


# noinspection PyUnusedLocal
def connection_made_handler(self):
    global spell_book
    print("Connected to VNC successfully.")
    spell_book.set_vnc_client(self.remoteframebuffer)
    self.remoteframebuffer.action_helper.type_text("echo \"VNCSim connected. Welcome!\"")
    self.remoteframebuffer.action_helper.press_key(rfb.KEY_Return)
    self.remoteframebuffer.action_helper.type_text("echo \"SpellBook discovered!\"")
    self.remoteframebuffer.action_helper.press_key(rfb.KEY_Return)


#---- ENTRY POINT

print((
    "\033[32mWelcome to VNCSimulator!\033[m\n\n"
    "Press 'ESC' for finish.\n"
    "Connecting to VNC-server..."
))

screen_buffer = ScreenBuffer(screen_buffer_flush_handler)
headless_vnc.connect(host, port, password,
                     reactor_int,
                     connection_made_handler,
                     screen_buffer.vnc_update_rectangle_handler)
