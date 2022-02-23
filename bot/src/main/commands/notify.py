import re
import datetime as dt
import mysql.connector

from discord.ext import commands
from discord.ext.commands import has_role
import asyncio

from src.main.objects.notify import EditLocale

from config.loader import cfg
from src.main.objects.util import with_cursor


class Locale(commands.Cog, name='Local Reminder'):
    def __init__(self, lang, logger, edit: EditLocale):
        self.lang = lang
        self.logger = logger

        self.edit = edit

    @commands.command(name="update",
                      usage="[arg]",
                      help="Updates the meta data (date and time) of the event."
                           "Per default all users which are slotted for the event, are"
                           "messaged the changed time and date. If the arg '--supress' is given,"
                           "this is not the case.",
                      brief="Updates the internal meta data (date and time) of the event.")
    @has_role(cfg["role"])
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def update(self, ctx, args=""):
        def getAllUser():
            sql = "SELECT User FROM Slot WHERE Event = %s  AND User IS NOT NULL;"
            self.cursor.execute(sql, [ctx.message.channel.id])
            return [channel.guild.get_member(int(x[0])) for x in self.cursor.fetchall() if x[0].isnumeric()]

        channel = ctx.message.channel
        time = ""

        if (before := self.edit.get_event(channel.id)) is not None:
            try:
                date = [int(x) for x in channel.name.split("-")[:3]]
                date = dt.date(*date)
            except ValueError:
                await ctx.message.delete()
                await channel.send(ctx.message.author.mention + " " +
                                   self.lang["update"]["command"]["date_error"].format(channel.name),
                                   delete_after=5)
                return

            async for msg in channel.history(limit=10, oldest_first=True):
                if content := re.findall(r"Eventstart:.*$", msg.content.replace("*", ""), re.MULTILINE):
                    if msg.author == ctx.message.author:
                        time = re.sub("[^0-9]", "", content[0])
                        break

            if time == "" or date == "":
                await ctx.message.delete()
                await channel.send(ctx.message.author.mention + " " +
                                   self.lang["update"]["command"]["error"].format(channel.name),
                                   delete_after=5)
                return

            else:
                if not (0 < int(time) < 2400):
                    await channel.send(ctx.message.author.mention + " " +
                                       self.lang["update"]["command"]["time_error"].format(channel.name),
                                       delete_after=5)
                    return

                time = time[:2] + ':' + time[2:] + ":00"
                self.edit.update_notify(channel.id, str(before[0]) + " " + str(before[1]),
                                        str(date) + " " + str(time))
                if self.edit.update_event(channel.id, channel.name, date, time):
                    await channel.send(ctx.message.author.mention + " " +
                                       self.lang["update"]["command"]["success"].format(channel.name),
                                       delete_after=5)

                    if args != "--suppress":
                        for user in getAllUser():
                            await user.send(self.lang["update"]["command"]["broadcast"].format(channel.id, time))

                else:
                    await channel.send(ctx.message.author.mention + " " +
                                       self.lang["update"]["command"]["error"].format(channel.name),
                                       delete_after=5)
        else:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["update"]["command"]["date_error"].format(channel.name),
                               delete_after=5)
            return

        await ctx.message.delete()

    @commands.command(name="toggleReminder",
                      usage="",
                      help="Enables/Disables the reminder for this event. If you want to change this for all event, "
                           "please use toggleReminderGlobal",
                      brief="Enables/Disables the reminder for this event.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def toggleReminder(self, ctx):
        author = ctx.message.author
        channel = ctx.message.channel

        result = self.edit.toggle(channel.id, author.id)

        if result is not None:
            result = ["nicht mehr", "wieder"][result]
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["toggle"]["channel"]["suc"], delete_after=5)
            await author.send(self.lang["notify_local"]["toggle"]["private"].format(result, channel.name))
        else:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_global"]["toggle"]["channel"]["fail"], delete_after=5)

        await ctx.message.delete()

    @commands.command(name="changeTime",
                      usage="[time in h]",
                      help="Changes the time before a event, when you are reminded for the event.",
                      brief="Changes the time before a event, when you are reminded for the event.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def changeTime(self, ctx, time):
        author = ctx.message.author
        channel = ctx.message.channel

        if not time.isdigit():
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["dig"], delete_after=5)
        elif int(time) > 2400:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["large"], delete_after=5)
        elif (time := self.edit.change_time(channel.id, author.id, time)) is not None:

            now = dt.datetime.now()
            delta = (time - now).total_seconds()

            if 86400 > delta > 0:
                asyncio.create_task(self.edit.notify(str(channel.id), str(author.id), delta))

            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["suc"], delete_after=5)
            await author.send(self.lang["notify_local"]["time"]["private"].format(channel.name, str(time)))

        else:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["fail"], delete_after=5)

        await ctx.message.delete()


class Global(commands.Cog, name='Global Reminder'):
    def __init__(self, lang, logger, db):
        self.lang = lang
        self.logger = logger

        self.db = db

    # TODO: Move
    @with_cursor
    def toggle(self, cursor: mysql.connector.MySQLConnection.cursor, user_id: str):
        """
            Toggles notification globally
                Args:
                    cursor: Database cursor
                    user_id: User ID

                Returns:
                    (Bool): Currents notification status if successfull, when not None
        """
        sql = "SELECT Notify FROM User WHERE ID = %s;"
        var = [str(user_id)]
        cursor.execute(sql, var)

        result = cursor.fetchone()

        if not result:
            return None

        sql = "UPDATE User SET Notify = NOT Notify WHERE ID = %s;"

        cursor.execute(sql, var)
        self.db.commit()

        return not result[0]

    @commands.command(name="toggleReminderGlobal",
                      usage="",
                      help="Enables/Disables if you get notified for a event at this guild. If you only want to change"
                           "the reminding option for this event, please use the command toggleReminder.",
                      brief="Enables/Disables if you get notified for a event at this guild.")
    @commands.guild_only()
    async def toggleReminderGlobal(self, ctx):

        author = ctx.message.author
        channel = ctx.message.channel

        result = self.toggle(author.id)

        if result is not None:

            result = ["nicht mehr", "wieder"][result]

            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_global"]["toggle"]["channel"]["suc"], delete_after=5)
            await author.send(self.lang["notify_global"]["toggle"]["private"].format(result))
        else:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_global"]["toggle"]["channel"]["fail"], delete_after=5)

        await ctx.message.delete()
