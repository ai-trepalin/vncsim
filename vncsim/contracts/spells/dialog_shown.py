from twisted.internet import reactor
from zope.interface import implementer
from collections import Iterable
from ..ispell import ISpell
from ...headless_vnc import rfb
from ...headless_vnc.headless_vnc import HeadlessVncClient

@implementer(ISpell)
class DialogShownSpell(object):

    action_name = "dialog_shown"

    def normalize_title(self, title: str) -> str:
        return ''.join(c.lower() for c in title if not c.isspace())

    # noinspection PyUnresolvedReferences
    def execute(self, vnc_client: HeadlessVncClient, context: object):
        print("Dialog shown")

        # noinspection PyTypeChecker
        dialogs: Iterable = context

        click_x = None
        click_y = None
        dialog_title = None

        for (dialog_title, (dx1, dy1, _, _), buttons) in dialogs:
            dialog_title = self.normalize_title(dialog_title)
            for (button_title, (bx1, by1, bx2, by2)) in buttons:
                button_title = self.normalize_title(button_title)
                if (dialog_title.find('account') != -1 and button_title == 'no') \
                        or (button_title == 'ok' or button_title == 'yes'):
                    click_x = dx1 + (bx1 + bx2) // 2
                    click_y = dy1 + (by1 + by2) // 2
                    print(f"Click to {click_x}:{click_y}")
                    break
            if click_x:
                break

        for (dialog_title, (_, _, _, _), buttons) in dialogs:
            dialog_title += dialog_title
        dialog_title = self.normalize_title(dialog_title)

        if click_x:
            vnc_client.action_helper.click_pointer(click_x, click_y)
            reactor.callLater(1, self.say, dialog_title=dialog_title, vnc_client=vnc_client)

    # noinspection PyUnresolvedReferences,PyMethodMayBeStatic
    def say(self, dialog_title, vnc_client):
        if dialog_title.find('disconnect') != -1:
            vnc_client.action_helper.type_text('echo "Ok, bye-bye!"')
            vnc_client.action_helper.press_key(rfb.KEY_Return)
            reactor.callLater(1, self.exit)
        else:
            vnc_client.action_helper.type_text('echo "Dialog closed"')
            vnc_client.action_helper.press_key(rfb.KEY_Return)

    # noinspection PyUnresolvedReferences
    @staticmethod
    def exit():
        reactor.removeAll()
        reactor.iterate()
        reactor.stop()
