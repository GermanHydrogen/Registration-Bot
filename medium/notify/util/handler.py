from discord.ext import commands
from datetime import datetime
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

            now = datetime.now()
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
            now = datetime.now()
            delta = (elem[1]-now).total_seconds()
            if delta > 0:
                asyncio.create_task(self.notify(elem[2], elem[0], delta))

