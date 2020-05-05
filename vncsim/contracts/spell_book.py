from .ispell import ISpell
from ..headless_vnc.headless_vnc import HeadlessVncClient


class SpellBook:
    spells: dict = {}
    vnc_client: HeadlessVncClient = None

    def __init__(self):
        pass

    def set_vnc_client(self, protocol: HeadlessVncClient):
        self.vnc_client = protocol

    def register_spell(self, spell):
        if not ISpell.providedBy(spell):
            raise Exception("Registered spell is not implements ISpell")
        if spell.action_name not in self.spells:
            self.spells[spell.action_name] = []
        self.spells[spell.action_name].append(spell)

    def execute_spells(self, action_name: str, context: object):
        if self.vnc_client:
            for spell in self.spells[action_name]:
                spell.execute(self.vnc_client, context)
