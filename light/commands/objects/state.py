import discord

from functools import wraps

from commands.objects.slotlist import SlotList, get_list, get_channel_author, SlotlistNotFound


class ClientState:
    def __init__(self, size=100):
        self.buffer = []
        self.size = size

    def __add_slotlist(self, slotlist: SlotList):
        if len(self.buffer) + 1 > self.size:
            self.buffer.pop(0)
        self.buffer.append(slotlist)

    async def get_slotlist(self, channel: discord.TextChannel, author: discord.User, user: discord.User, delete=False):
        """
        Gets the slotlist from the buffer or constructs a new one
        :param channel: Channel in which the slotlist is
        :param author: Author of the command
        :param user: Bot User
        :param delete: if slotlist should be deleted
        :return:
        """
        channel_id = channel.id
        guild_id = channel.guild.id

        if (hit := next((x for x in self.buffer if x.guild == guild_id and x.channel == channel_id), None)) is not None \
                and not delete:
            return hit
        else:
            message = await get_list(channel, author, user)

            if message is None:
                raise SlotlistNotFound

            if not delete:
                author = await get_channel_author(channel)

            slotlist = SlotList(message, author)
            self.__add_slotlist(slotlist)
            if delete:
                await message.delete()

            return slotlist
