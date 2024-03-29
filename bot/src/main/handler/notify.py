import asyncio
import datetime as dt

from discord.ext import commands

from bot.src.main.objects.notify import EditLocale
from bot.src.main.objects.util import Util


class NotifyHandler(commands.Cog):
    def __init__(self, lang, logger, notify: EditLocale, util: Util):
        self.lang = lang
        self.logger = logger

        self.notify = notify
        self.util = util

    @commands.Cog.listener()
    async def on_ready(self):
        for elem in self.notify.get_all_notify():
            now = dt.datetime.now()
            delta = (elem[1] - now).total_seconds()
            if delta > 0:
                asyncio.create_task(self.notify.notify(elem[2], elem[0], delta))

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            if (event := self.notify.get_event(after.id)) is not None:
                author = self.util.get_channel_author(after)

                try:
                    date = [int(x) for x in after.name.split("-")[:3]]
                    date = dt.date(*date)
                except ValueError:
                    await author.send(self.lang["update"]["auto"]["date_error"].format(after.name))
                    return

                self.notify.update_notify(after.id, str(event[0]) + " " + str(event[1]), str(date) + " " + str(event[1]))
                if self.notify.update_event(after.id, after.name, date):
                    await author.send(self.lang["update"]["auto"]["success"].format(after.name))
                else:
                    await author.send(self.lang["update"]["auto"]["error"].format(after.name))
                    return

