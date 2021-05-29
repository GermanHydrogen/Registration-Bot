import datetime as dt
import mysql.connector

from discord.ext import commands
from src.main.objects.notify import EditLocale
from src.main.objects.util import Util, with_cursor

from config.loader import cfg
import asyncio

import discord


class Handler(commands.Cog):
    def __init__(self, client, lang, logger, db):
        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.edit = EditLocale(db)
        self.util = Util(client, db)

    @with_cursor
    async def notify(self, cursor: mysql.connector.MySQLConnection.cursor, event, user_id, delay):
        """
            Calculates datetime for notification
                Args:
                    cursor: Database cursor
                    event: ID of an event
                    user_id: User ID
                    delay: delay in sec.

        """

        await asyncio.sleep(delay)

        user = self.client.get_user(int(user_id))
        if user:
            sql = "SELECT Time FROM Notify WHERE Event = %s AND User = %s"
            cursor.execute(sql, [event, user_id])
            result = cursor.fetchall()

            if not result:
                return

            now = dt.datetime.now()
            delta = (result[0][0] - now).total_seconds()

            if abs(delta) > 1200:
                return

            sql = "SELECT Name, Time FROM Event WHERE ID = %s;"
            cursor.execute(sql, [event])
            result = cursor.fetchone()

            guild = self.client.get_guild(int(cfg['guild']))
            nickname = guild.get_member(int(user_id)).display_name
            try:
                await user.send(self.lang["notify_global"]["noti"].format(nickname, str(result[0]), str(result[1])))
            except discord.errors.Forbidden:
                log = "User: " + str(nickname).ljust(20) + "\t"
                log += "Channel:" + str(event).ljust(20) + "\t"
                log += "Command: " + "Notify: discord.errors.Forbidden".ljust(20) + "\t"
                self.logger.log(log)

    @with_cursor
    @commands.Cog.listener()
    async def on_ready(self, cursor: mysql.connector.MySQLConnection.cursor):
        sql = "SELECT n.User, n.Time, n.Event FROM Notify n, User u \
                WHERE n.User = u.ID AND u.Notify AND n.Enabled AND n.Time >= CURDATE();"
        cursor.execute(sql)
        result = cursor.fetchall()

        for elem in result:
            now = dt.datetime.now()
            delta = (elem[1] - now).total_seconds()
            if delta > 0:
                asyncio.create_task(self.notify(elem[2], elem[0], delta))

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            if (event := self.edit.get_event(after.id)) is not None:
                author = self.util.get_channel_author(after)

                try:
                    date = [int(x) for x in after.name.split("-")[:3]]
                    date = dt.date(*date)
                except ValueError:
                    await author.send(self.lang["update"]["auto"]["date_error"].format(after.name))
                    return

                self.edit.update_notify(after.id, str(event[0]) + " " + str(event[1]), str(date) + " " + str(event[1]))
                if self.edit.update_event(after.id, after.name, date):
                    await author.send(self.lang["update"]["auto"]["success"].format(after.name))
                else:
                    await author.send(self.lang["update"]["auto"]["error"].format(after.name))
                    return

