import discord
import re
from util import CustomParentException
from commands.objects.slot import *
from commands.objects.slotgroup import SlotGroup

from config.loader import cfg


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

    raise SlotlistNotFound(channel)


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
    def __init__(self, channel=None):
        """
        Raised if a slotlist is not found
        :param channel: Channel in which the slotlist should be
        """
        super().__init__()
        self.message = "Slotlist message was not found!"

        if channel is not None:
            self.author_message = f"The slotlist in guild {channel.guild.name} in channel {channel.name} was not found.\n" \
                                  f"Did you declare it with `>Slotlist<`?"


class SlotlistNumberError(CustomParentException):
    def __init__(self, channel=None):
        """
        Raised if slot has no or a faulty number
        :param channel: Channel in which the error accrued
        """
        super().__init__()
        self.message = "Faulty slotlist number!"

        if channel is not None:
            self.author_message = f"In the slotlist in guild {channel.guild.name} in channel {channel.name} " \
                                  f"a faulty slot number was found!\n" \
                                  f"Please use the format `#[number] [description] - [opt: user]` for your slots 😀"


class DuplicateSlot(CustomParentException):
    def __init__(self, slot_number: str, channel=None):
        """
        Raised when adding a slot but the slotnumber already exstists
        :param slot_number: Number of the slot
        :param channel: Channel in which the error was raised
        """
        super().__init__()
        self.message = f"The slot {slot_number} is a duplicate!"

        if channel is not None:
            self.author_message = f"In the slotlist in guild {channel.guild.name} in channel {channel.name} " \
                                  f"a duplicate slot with number {slot_number} was found.\n" \
                                  f"Please change the slot number, because the the slot number has to be unique!"


class SlotGroupNotFound(CustomParentException):
    def __init__(self, name: str):
        """
        Raised when a slot group is not found.
        :param name: Number of the slot
        """
        super().__init__()
        self.message = f"The slot group {name} doesn't exist!"


class SlotNotFound(CustomParentException):
    def __init__(self, slot_number: str):
        """
        Raised when a slot number is not found.
        :param slot_number: Number of the slot
        """
        super().__init__()
        self.message = f"The slot {slot_number} doesn't exist!"


class UserNotSlotted(CustomParentException):
    def __init__(self, user_name=None):
        """
        Raised when unslotting a user but the user is not in the slotlist
        :param user_name: User name of the user
        """
        super().__init__()
        if user_name is not None:
            self.message = f"{user_name} isn't slotted"
        else:
            self.message = "You arent slotted!"


class SlotList:
    def __init__(self, message: discord.message, author: discord.User):
        """
        The slotlist consists of user defined slot groups which
        contain all regular slots and a reserve slot group which contain
        all reserve slots, which is only displayed if all regular slots are full.

        It is constructed from a message containing a string.

        :param message: Message in which slotlist is
        :param author: Author of the slotlist
        """

        self.message = message
        self.guild = message.guild.id
        self.channel = message.channel.id

        self.author = author

        self.slots = []
        self.reserve = []

        # Slot Groups
        self.struct = []

        self.__build_slotlist(message.content.splitlines(False))

    def __build_reserve(self) -> None:
        amount = int(len(self.slots) * cfg['res_ratio']) + 1
        minim = int(max([int(x.number) for x in self.slots]) / 10 + 1) * 10
        self.reserve = [Slot().from_data(str(minim + index), "Reserve", "") for index in range(amount)]

    def __build_slotlist(self, content: str) -> None:
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
                try:
                    slot = Slot().from_line(line)
                except ValueError:
                    raise SlotlistNumberError(self.message.channel)

                if not self.struct or current_buffer or title_buffer:
                    self.add_group(SlotGroup(prim=last, title="\n".join(title_buffer), before=current_buffer))
                    last += 1
                    title_buffer = []
                    current_buffer = ""

                slot.group = len(self.struct) - 1

                if slot.desc.strip().replace("**", "") == "Reserve":
                    self.reserve.append(slot)
                else:
                    self.__add_slot(slot)

            elif line.strip().replace("\u200b", "") == "":
                current_buffer += "\n"
            elif line.strip().replace("**", "") != "Reserve":
                title_buffer.append(line.strip())

        if len(self.reserve) == 0:
            self.__build_reserve()

    def edit_slot(self, number: str, description: str) -> None:
        """
        Changes the description of an slot
        :param number: Slotnumber
        :param description: New description
        :return: None
        """

        if (slot := next((x for x in self.slots if x.number == number), None)) is None:
            raise SlotNotFound(number)
        else:
            slot.desc = description

    def __add_slot(self, slot: Slot) -> None:
        """
        Adds slot to slotlist
        :param slot: Slot
        :return:
        """
        if next((x for x in self.slots if x.number == slot.number), None) is not None:
            raise DuplicateSlot(slot.number, self.message.channel)
        else:
            self.slots.append(slot)

    def new_slot(self, number: str, group_name: str, description: str) -> None:
        """
        Creates a new slot and adds it to the given group
        :param number:
        :param group_name:
        :param description:
        :return:
        """

        group = self.__get_group(group_name)
        slot = Slot().from_data(number, description, "")
        slot.group = group.prim

        self.__add_slot(slot)


    def remove_slot(self, number: str) -> None:
        """
        Changes the description of an slot
        :param number: Slot number
        :return: None
        """
        if (slot := next((x for x in self.slots if x.number == number), None)) is None:
            raise SlotNotFound(number)
        else:
            self.slots.remove(slot)

    def __get_group(self, name: str) -> SlotGroup:
        print([str(x) for x in self.struct])

        if name.isdigit():
            try:
                return self.struct[int(name)]
            except KeyError:
                pass

        if (group := next((x for x in self.struct if x.title.replace("**", "").replace("\n", " ").strip() == name), None)) is None:
            raise SlotGroupNotFound(name)
        else:
            return group

    def add_group(self, group: SlotGroup) -> None:
        """
        Adds group
        :param group: SlotGroup
        :return:
        """
        self.struct.append(group)

    def slot(self, number: int, user_name: str) -> None:
        """
        Slots a user
        :param number: Slot number
        :param user_name: User which should to be slotted
        :return:
        """
        if (hit := next((x for x in self.slots + self.reserve if int(x.number) == int(number)), 0)) == 0:
            raise SlotNotFound(slot_number=str(number))
        else:
            if (taken := next(((x for x in self.slots + self.reserve if x.user == user_name)), 0)) != 0:
                taken.unslot_user(user_name)

            hit.slot_user(user_name)

    def unslot(self, user_name: str) -> None:
        """
        Unslots a user
        :param user_name: User which should be unslotted
        :return: None
        """
        if (hit := next(((x for x in self.slots if x.user == user_name)), 0)) == 0:
            raise UserNotSlotted
        else:
            hit.unslot_user(user_name)

    def manage_reserve(self) -> None:
        """
        Manage reserve slots.
        Puts user from reserve into free slots,
        and sorts the reserve slots, so its filled from the button up
        :return: None
        """

        # Free slots
        free_slots = [x for x in self.slots if x.user == ""]
        # Filled reserve slots
        filled_reserve = [x for x in self.reserve if x.user != ""]

        #  Puts user from reserve into free slots
        if len(free_slots) != 0 and len(filled_reserve) != 0:
            for index, elem in enumerate(free_slots, start=0):
                try:
                    self.slot(elem.number, filled_reserve[index].user)
                except KeyError:
                    break
        # Sorts the reserve slots, so its filled from button up
        if len(free_slots) < len(filled_reserve):
            for index, elem in enumerate(self.reserve, start=0):
                if elem.user == "":
                    self.reserve.append(self.reserve.pop(index))

    async def write(self, channel=None, edit=True) -> None:
        """
        Writes slotlist to channel
        :param channel: channel to write to
        :param edit: if this is a edit
        :return: None
        """
        self.manage_reserve()

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

        if self.reserve and \
                (len([x for x in self.reserve if x.user != ""]) != 0 or discord.utils.get(self.slots, user="") is None):
            output += "**Reserve**" + "\n"  # TODO: Language
            output += "\n".join([str(x) for x in self.reserve])
            output += "\n"

        return output
