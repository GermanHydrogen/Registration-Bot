import discord
import re
from util import CustomParentException
from commands.objects.slot import *
from commands.objects.slotgroup import SlotGroup


async def get_list(channel: discord.TextChannel, author: discord.User, user: discord.User):
    """
    Get slotlist from channel
    :param channel: Channel in which the slotlist is
    :param author: Slotlist owner
    :param user: Bot user
    :return: discord.Message
    """
    async for msg in channel.history(limit=1000):
        if (re.search(">Slotlist<", msg.content) and msg.author == author) \
                or (re.search(re.escape("**Slotlist**"), msg.content) and msg.author == user):
            return msg

    raise SlotlistNotFound


async def get_channel_author(channel: discord.TextChannel):
    """
    Gets the channel author aka
    the user which has written the first message in the channel
    :param channel: Discord channel
    :return: Author
    """
    message = await channel.history(limit=1, oldest_first=True).flatten()
    if message is None:
        return None
    else:
        return message[0].author


class SlotlistNotFound(CustomParentException):
    """ Raised if a slotlist is not found

    Attributes:
        channel: Channel in which the slotlist should be
        author: Author of the slotlist
    """

    def __init__(self, channel=None, author=None):
        super().__init__()
        self.message = "Slotlist message was not found!"

        if channel is not None and author is not None:
            self.author_message = f"The slotlist in guild {channel.guild.name} in channel {channel.name} was not found." \
                                  f"Did you declare it with `>Slotlist<`?"
            self.author = author


class DuplicateSlot(CustomParentException):
    """Raised when adding a slot but the slotnumber already exstists

    Attributes:
        slot_number: Number of the slot
    """

    def __init__(self, slot_number: str):
        super().__init__()
        self.message = f"The slot {slot_number} already exists!"


class SlotNotFound(CustomParentException):
    """ Raised when a slot number is not found.

    Attributes:
        slot_number: Number of the slot
    """

    def __init__(self, slot_number: str):
        super().__init__()
        self.message = f"The slot {slot_number} doesn't exist!"


class UserNotSlotted(CustomParentException):
    """ Raised when unslotting a user but the user is not in the slotlist

    Attributes:
        user_name: User name of the user
    """

    def __init__(self, user_name=None):
        super().__init__()
        if user_name is not None:
            self.message = f"{user_name} isn't slotted"
        else:
            self.message = "You arent slotted!"


class SlotList:
    def __init__(self, message: discord.message, author: discord.User):
        """
        Creates slotlist
        :param message: Message in which slotlist is
        :param author: Author of the slotlist
        """

        self.message = message
        self.guild = message.guild.id
        self.channel = message.channel.id

        self.author = author

        self.slots = []
        self.reserve = []

        self.struct = []

        self.__build_slotlist(message.content.splitlines(False))

    def __build_slotlist(self, content: str):
        """
        Constructs the slotlist
        :param content: slotlist string
        :return:
        """
        last = 0
        current_buffer = ""
        title_buffer = []

        for line in content:
            if "Slotlist" in line:  # TODO: Language
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
        """
        Slots a user
        :param number: Slot number
        :param user: User which should to be slotted
        :return:
        """
        if (hit := next((x for x in self.slots if int(x.number) == int(number)), 0)) == 0:
            raise SlotNotFound(slot_number=str(number))
        else:
            if (taken := next(((x for x in self.slots if x.user == user.display_name)), 0)) != 0:
                taken.unslot_user(user.display_name)

            hit.slot_user(user.display_name)

    def unslot(self, user: discord.User):
        """
        Unslots a user
        :param user: User which should be unslotted
        :return:
        """
        if (hit := next(((x for x in self.slots if x.user == user.display_name)), 0)) == 0:
            raise UserNotSlotted
        else:
            hit.unslot_user(user.display_name)

    async def write(self, channel=None, edit=True):
        """
        Writes slotlist to channel
        :param channel: channel to write to
        :param edit: if this is a edit
        :return:
        """
        if edit:
            await self.message.edit(content=str(self))
        else:
            self.message = await channel.send(str(self))

    def __str__(self):
        output = "**Slotlist**\n"  # TODO: Langugage
        for group in self.struct:
            output += str(group) + "\n"
            output += "\n".join([str(x) for x in self.slots if x.group == group.prim])
            output += "\n"

        if self.reserve:
            output += "**Reserve**" + "\n"  # TODO: Language
            output += "\n".join([str(x) for x in self.reserve])
            output += "\n"

        return output
