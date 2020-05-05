from zope.interface import Interface
from zope.interface import Attribute
from ..headless_vnc.headless_vnc import HeadlessVncClient


class ISpell(Interface):

    # noinspection PyUnusedName
    action_name = Attribute("Spell action name in the spellbook")

    def execute(vnc_client: HeadlessVncClient, context: object):
        pass
