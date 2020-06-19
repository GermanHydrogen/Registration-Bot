from discord.ext import commands

from notify.util.editLocale import EditLocale


class Locale(commands.Cog):
    def __init__(self, client, lang, logger, db, cursor):

        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

        self.edit = EditLocale(db, cursor)

    @commands.command(hidden=False, description="toggles if you recieve a notification before an event")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def toggleNotify(self, ctx):
        author = ctx.message.author
        channel = ctx.message.channel

        result = self.edit.toggle(channel.id, author.id)

        if result:
            result = ["nicht mehr", "wieder"][result]
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["toggle"]["channel"]["suc"], delete_after=5)
            await author.send(self.lang["notify_local"]["toggle"]["private"].format(result, channel.name))
        else:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_global"]["toggle"]["channel"]["fail"], delete_after=5)

        await ctx.message.delete()

    @commands.command(hidden=False, description="[time in h] sets time you want to be notified before an event")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def changeTime(self, ctx, time):
        author = ctx.message.author
        channel = ctx.message.channel

        if not time.isdigit():
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["dig"], delete_after=5)
        elif self.edit.changeTime(channel.id, author.id, time):
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["suc"], delete_after=5)
            await author.send(self.lang["notify_local"]["time"]["private"].format(channel.name, int(time)))
        else:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_local"]["time"]["channel"]["fail"], delete_after=5)

        await ctx.message.delete()
