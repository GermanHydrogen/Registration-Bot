import inspect

import discord.ext
import mysql.connector

from functools import lru_cache
from discord import utils as dutil

from config.loader import cfg


def with_cursor(func):
    def inner(*args, **kwargs):
        obj = args[0]
        with obj.db.cursor() as cursor:
            return func(obj, cursor, *args[1:], **kwargs)

    async def async_inner(*args, **kwargs):
        obj = args[0]
        with obj.db.cursor() as cursor:
            return await func(obj, cursor, *args[1:], **kwargs)

    if inspect.iscoroutinefunction(func):
        return async_inner
    else:
        return inner


class Util:
    def __init__(self, client, db):
        self.client = client
        self.db = db

        self.guild = None

    @with_cursor
    def get_channel_author(self, cursor: mysql.connector.MySQLConnection.cursor,
                           channel: discord.TextChannel) -> discord.Member:
        """
        Gets the author of the channel
        Args:
            cursor: Database cursor
            channel: Server Channel

        Returns:
            Discord Member

        """
        sql = "SELECT Author FROM Event WHERE ID = %s;"
        cursor.execute(sql, [channel.id])

        result = cursor.fetchone()

        if result:
            return channel.guild.get_member(int(result[0]))
        else:
            return None

    @with_cursor
    def get_event_date(self, cursor: mysql.connector.MySQLConnection.cursor, channel_id: str) -> str:
        """
        Gets the date of an event
        Args:
            cursor: Database cursor
            channel_id (string): Server Channel

        Returns:
            Date

        """

        sql = "SELECT Date FROM Event WHERE ID = %s;"
        cursor.execute(sql, [str(channel_id)])
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    @with_cursor
    def get_event_id(self, cursor: mysql.connector.MySQLConnection.cursor, name: str):
        """
        Gets the id of an event
        Args:
            cursor: Database cursor
            name: Eventname (e.g. 2020-02-13-arma3)

        Returns:
            (string): id

        """

        sql = "SELECT ID FROM Event WHERE Name = %s;"
        cursor.execute(sql, [str(name)])
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None

    @with_cursor
    def get_slots(self, cursor: mysql.connector.MySQLConnection.cursor, channel_id: str, intersection: str = '') -> []:
        """
        Gets all taken slots of the channel
        If intersection is given, K.I.A (marked in the intersection channel) are removed
        Args:
            cursor: Database cursor
            channel_id: Server Channel
            intersection: Server Channel to intersect with
        Returns:
            [(user, slot-number, description)]

           """
        if intersection == '':
            sql = "SELECT User, Number, Description FROM Slot WHERE Event = %s AND Description != %s AND User IS NOT NULL;"
            cursor.execute(sql, [str(channel_id), 'Reserve'])
        else:
            sql = "SELECT User, Number, Description FROM Slot s1 WHERE Event = %s AND Description != %s AND User IS NOT NULL AND User regexp '^[0-9]'" \
                  "AND NOT EXISTS(SELECT * FROM Slot s2 WHERE Event = %s AND s1.Number = s2.Number AND s2.User = 'A00000000000000000');"
            cursor.execute(sql, [str(channel_id), 'Reserve', str(intersection)])

        return cursor.fetchall()

    @with_cursor
    def get_slot_description(self, cursor: mysql.connector.MySQLConnection.cursor, event, user) -> str:
        """
        Gets all taken slots of the channel
        Args:
            cursor: Database cursor
            event: Server Channel/ Event id
            user: User ID

        Returns:
            '#[num] [description]'
        """

        sql = "SELECT Number, Description FROM Slot WHERE Event = %s AND User = %s"
        cursor.execute(sql, [str(event), str(user)])

        result = cursor.fetchone()

        if result:
            return '#' + str(result[0]) + " " + str(result[1])
        else:
            return None

    @lru_cache(maxsize=None)
    def get_emoji(self, name=None, dict_name=None) -> discord.Emoji:
        """
        Loads a emoji from config and gets the corresponding emoji object
        Args:
            name: Emoji name (opt)
            dict_name: Emoji name in config (opt)

        Returns:
            Emoji
        """
        if name is None and dict_name is not None:
            if dict_name in cfg['marks'].keys():
                name = cfg['marks'][dict_name]
            else:
                return None

        if not self.guild:
            self.guild = self.client.get_guild(int(cfg['guild']))

        return dutil.get(self.guild.emojis, name=name)


class CustomHelp(discord.ext.commands.DefaultHelpCommand):
    def __init__(self):
        super(CustomHelp, self).__init__()

    async def send_pages(self) -> None:
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(page)
        try:
            await self.context.message.delete()
        except discord.Forbidden:
            pass

    def get_destination(self):
        return self.context.author