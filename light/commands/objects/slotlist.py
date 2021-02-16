import discord
import re
from commands.objects.slot import *
from commands.objects.slotgroup import SlotGroup


async def get_list(channel: discord.TextChannel, user: discord.User):
    """
    Get slotlist from channel
    :param channel: Channel in which the slotlist is
    :param user: Slotlist owner
    :return: discord.Message
    """
    async for msg in channel.history(limit=1000):
        if re.search("Slotliste", msg.content) and msg.author == user:
            return msg

    raise SlotlistNotFound


class SlotlistNotFound(Exception):
    pass


class DuplicateSlot(Exception):
    pass


class SlotNotFound(Exception):
    pass


class SlotList:
    def __init__(self, channel: discord.TextChannel, user: discord.User):
        """
        Creates slotlist
        :param channel: Channel in which slotlist is
        :param user: Slotlist user
        """

        self.guild = channel.guild.id
        self.channel = channel.id

        self.slots = []
        self.reserve = []

        self.struct = []

        self.message = await get_list(channel, user)
        self.content = self.message.content.splitlines(False)

        last = 0
        current_buffer = ""
        title_buffer = []

        for line in self.content:
            if ">Slotlist<" in line:  # TODO: Language
                pass
            elif line and line[0] == '#':
                slot = Slot().from_line(line)
                if not self.struct or current_buffer or title_buffer:
                    self.add_group(SlotGroup(prim=last, title="\n".join(title_buffer), before=current_buffer))
                    last += 1
                    title_buffer = []
                    current_buffer = ""

                slot.group = len(self.struct) - 1

                if slot.desc.strip().replace("**", "") == "Reserve":
                    self.reserve.append(slot)
                else:
                    self.slots.append(slot)

            elif line.strip() == "":
                current_buffer += "\n"
            elif line.strip().replace("**", "") != "Reserve":  # TODO: Language
                title_buffer.append(line.strip())

    def add_slot(self, slot: Slot):
        """
        Adds slot to slotlist
        :param slot: Slot
        :return:
        """
        if next((x for x in self.slots if x.number == slot.number), None) is None:
            raise DuplicateSlot
        else:
            self.slots.append(slot)

    def add_group(self, group: SlotGroup):
        """
        Adds group
        :param group: SlotGroup
        :return:
        """
        self.struct.append(group)

    def slot(self, number: int, user: discord.User):
        if (hit := next((x for x in self.slots if int(x.number) == int(number))), None) is None:
            raise SlotNotFound
        else:
            try:
                self.slots[self.slots.index(hit)].slot_user(user.display_name)
            except SlotTaken:
                raise


    async def write(self, channel=None, edit=True):
        """
        Writes slotlist to channel
        :param channel: channel to write to
        :param edit: if this is a edit
        :return:
        """
        if edit:
            await self.message.edit(str(self))
        else:
            self.message = await channel.send(str(self))

    def __str__(self):
        output = "**Slotlist**\n"  # TODO: Langugage
        for group in self.struct:
            output += str(group) + "\n"
            print(str(group))
            output += "\n".join([str(x) for x in self.slots if x.group == group.prim])
            output += "\n"

        if self.reserve:
            output += "**Reserve**" + "\n"  # TODO: Language
            output += "\n".join([str(x) for x in self.reserve])
            output += "\n"

        return output
