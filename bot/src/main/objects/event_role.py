import discord
import mysql.connector
from bot.config.loader import cfg
from bot.src.main.objects.util import with_cursor


class EventRole:
    def __init__(self, client, db):
        self.client = client
        self.db = db

    @staticmethod
    async def add_event_role(user: discord.Member, game_name: str) -> None:
        game = cfg['games'][game_name]
        if 'temp_role' in game:
            role = user.guild.get_role(int(game['temp_role']))
            await user.add_roles(role)

    @with_cursor
    async def remove_event_role(self, cursor: mysql.connector.MySQLConnection.cursor, user: discord.Member, game_name: str) -> None:
        game = cfg['games'][game_name]

        if 'temp_role' not in game:
            return

        sql = "SELECT COUNT(*) FROM Event, Slot WHERE " \
              "Event.ID = Slot.Event AND " \
              "Event.Date >= CURDATE() AND " \
              "Event.Type = %s AND " \
              "Slot.User = %s;"

        cursor.execute(sql, [game_name, user.id])
        count = cursor.fetchone()[0]

        if count == 0:
            role = user.guild.get_role(int(game['temp_role']))
            await user.remove_roles(role)

    @with_cursor
    async def manage_event_role(self, cursor: mysql.connector.MySQLConnection.cursor, guild: discord.Guild,
                                game_name: str) -> None:

        sql = "SELECT DISTINCT (Slot.User) FROM Slot, Event WHERE " \
              "Slot.Event = Event.ID AND " \
              "Event.Date = SUBDATE(CURDATE(), 1) AND " \
              "Event.Type = %s AND " \
              "Slot.User regexp '^[0-9]';"

        cursor.execute(sql, [game_name])
        result = cursor.fetchall()

        for user_id in result:
            user = guild.get_member(int(user_id[0]))
            await self.remove_event_role(user, game_name)