from functools import wraps

from commands.objects.slotlist import SlotList


class ClientState:
    def __init__(self, size=100):
        self.buffer = []
        self.size = size

    def add_slotlist(self, slotlist: SlotList):
        if (hit := next((x for x in self.buffer
                         if x.guild == slotlist.guild and x.channel == slotlist.channel), None)) is None:

            if len(self.buffer) + 1 > self.size:
                self.buffer.pop(0)
            self.buffer.append(slotlist)
        else:
            self.buffer[self.buffer.index(hit)] = slotlist

    def get_slotlist(self, guild_id: int, channel_id: int):
        return next((x for x in self.buffer if x.guild == guild_id and x.channel == channel_id), None)
