import datetime as dt

from discord.ext import commands
from src.notify.util.editLocale import EditLocale
from src.main.objects.util import Util

from config.loader import cfg
import asyncio

import discord


class Handler(commands.Cog):
    def __init__(self, client, lang, logger, db, cursor):
        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor
        self.edit = EditLocale(db, cursor)
        self.util = Util(client, db, cursor)

    async def notify(self, event, user_id, delay):
        """
            Calculates datetime for notification
                Args:
                    event(string): ID of an event
                    user_id(string): User ID
                    delay(int): delay in sec.

        """

        await asyncio.sleep(delay)

        user = self.client.get_user(int(user_id))
        if user:
            sql = "SELECT Time FROM Notify WHERE Event = %s AND User = %s"
            self.cursor.execute(sql, [event, user_id])
            result = self.cursor.fetchall()

            if not result:
                return

            now = dt.datetime.now()
            delta = (result[0][0] - now).total_seconds()

            if abs(delta) > 1200:
                return

            sql = "SELECT Name, Time FROM Event WHERE ID = %s;"
            self.cursor.execute(sql, [event])
            result = self.cursor.fetchone()

            guild = self.client.get_guild(int(cfg['guild']))
            nickname = guild.get_member(int(user_id)).display_name
            try:
                await user.send(self.lang["notify_global"]["noti"].format(nickname, str(result[0]), str(result[1])))
            except discord.errors.Forbidden:
                log = "User: " + str(nickname).ljust(20) + "\t"
                log += "Channel:" + str(event).ljust(20) + "\t"
                log += "Command: " + "Notify: discord.errors.Forbidden".ljust(20) + "\t"
                self.logger.log(log)

    @commands.Cog.listener()
    async def on_ready(self):
        sql = "SELECT n.User, n.Time, n.Event FROM Notify n, User u \
                WHERE n.User = u.ID AND u.Notify AND n.Enabled AND n.Time >= CURDATE();"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()

        for elem in result:
            now = dt.datetime.now()
            delta = (elem[1] - now).total_seconds()
            if delta > 0:
                asyncio.create_task(self.notify(elem[2], elem[0], delta))

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            if (event := self.edit.getEvent(after.id)) is not None:
                author = self.util.get_channel_author(after)

                try:
                    date = [int(x) for x in after.name.split("-")[:3]]
                    date = dt.date(*date)
                except ValueError:
                    await author.send(self.lang["update"]["auto"]["date_error"].format(after.name))
                    return

                self.edit.updateNotify(after.id, str(event[0]) + " " + str(event[1]), str(date) + " " + str(event[1]))
                if self.edit.updateEvent(after.id, after.name, date):
                    await author.send(self.lang["update"]["auto"]["success"].format(after.name))
                else:
                    await author.send(self.lang["update"]["auto"]["error"].format(after.name))
                    return

