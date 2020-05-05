from twisted.internet import reactor
from zope.interface import implementer
from ..ispell import ISpell
from ...headless_vnc import rfb
from ...headless_vnc.headless_vnc import HeadlessVncClient
from ...headless_vnc.vnc_action_helper import MouseButton

@implementer(ISpell)
class StartSurfingSpell(object):

    action_name = "start_surfing_after_20_secs"
    explorer_cmd = 'start-process -FilePath "C:\Program Files\Internet Explorer\iexplore.exe" -ArgumentList "group-ib.com"'

    script = [
        "down", "down", "down", "down",
        "up", "up",
        "search", "type",
        "shift-tab",
        "enter", "enter"
    ]

    # noinspection PyUnresolvedReferences,PyUnusedLocal
    # Entry point to contract.
    def execute(self, vnc_client: HeadlessVncClient, context: object):
        print("Start surfing after 20 secs")

        vnc_client.action_helper.type_text(self.explorer_cmd)
        vnc_client.action_helper.press_key(rfb.KEY_Return)

        reactor.callLater(5, StartSurfingSpell.navigate, vnc_client=vnc_client)

    # Wheel down and navigate to next page
    # noinspection PyUnresolvedReferences
    @staticmethod
    def navigate(vnc_client: HeadlessVncClient, action_index = 0):
        if action_index == len(StartSurfingSpell.script):
            return
        action = StartSurfingSpell.script[action_index]

        def shift_tab(vnc_client: HeadlessVncClient):
            vnc_client.protocol.keyEvent(rfb.KEY_ShiftLeft, down=1)
            vnc_client.action_helper.press_key(rfb.KEY_Tab)
            vnc_client.protocol.keyEvent(rfb.KEY_ShiftLeft, down=0)

        def search(vnc_client: HeadlessVncClient):
            vnc_client.protocol.keyEvent(rfb.KEY_ControlLeft, down=1)
            vnc_client.action_helper.press_key(ord('f'))
            vnc_client.protocol.keyEvent(rfb.KEY_ControlLeft, down=0)

        {
            'down': (lambda:  vnc_client.action_helper.click_pointer(200, 200, MouseButton.WHEEL_DOWN)),
            'up': (lambda:  vnc_client.action_helper.click_pointer(200, 200, MouseButton.WHEEL_UP)),
            'tab': (lambda:  vnc_client.action_helper.press_key(rfb.KEY_Tab)),
            'shift-tab': (lambda:  shift_tab(vnc_client)),
            'enter': (lambda: vnc_client.action_helper.press_key(rfb.KEY_Return)),
            'search': (lambda:  search(vnc_client)),
            'type': (lambda: vnc_client.action_helper.type_text("intelli")),
        }[action]()

        reactor.callLater(1, StartSurfingSpell.navigate,
                          vnc_client=vnc_client, action_index=action_index + 1)
