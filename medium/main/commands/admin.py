import re

from discord.ext import commands
from discord.ext.commands import has_role

from main.util.io import IO
from main.util.util import Util
from main.util.editList import EditList

from config.loader import cfg


class Admin(commands.Cog):
    def __init__(self, client, lang, logger, db, cursor):
        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

        self.io = IO(cfg, client, db, cursor)
        self.util = Util(client, db, cursor)
        self.list = EditList(db, cursor)

    @commands.command(hidden=True, description="Initialize the slotlist")
    @has_role(cfg["role"])
    @commands.guild_only()
    async def create(self, ctx, arg=""):  # makes the slotlist editable for the bot
        channel = ctx.message.channel
        out = []
        time = ""

        async for x in channel.history(limit=1000):
            if re.search("Slotliste", x.content):

                if x.author == ctx.message.author and re.search(">Slotliste<", x.content):
                    out.append(x)
                elif x.author == self.client.user and re.search(re.escape("**Slotliste**"), x.content):
                    out.append(x)
            elif content := re.findall(r"Eventstart:.*$", x.content.replace("*", ""), re.MULTILINE):
                if x.author == ctx.message.author:
                    time = re.sub("[^0-9]", "", content[0])

        if time == "" or len(time) != 4:
            await ctx.message.author.send(self.lang["create"]["error"]["time"]["user"])
        elif out:
            self.io.createEvent(out, ctx.message.author, time, self.client.user, (arg == 'manuel'))
            await self.io.writeEvent(channel, True)

            await ctx.message.author.send(self.lang["create"]["success"]["user"])

            for x in out:
                if x.author != self.client.user:
                    await x.delete()

        else:
            await ctx.message.author.send(self.lang["create"]["error"]["general"]["user"])

        await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [User] Slots an User in a Slot")
    @has_role(cfg["role"])
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def forceSlot(self, ctx):  # [Admin Function] slots an user
        channel = ctx.message.channel

        argv = ctx.message.content.split(" ")

        if not len(argv) >= 2:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["forceSlot"]["error"]["arg_error"]["channel"],
                delete_after=5)
            return

        num = argv[1]
        player = argv[2:]

        if not player:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["forceSlot"]["error"]["missing_target"]["channel"],
                delete_after=5)
            return

        player = " ".join(player)

        player = self.io.get_user_id(player, channel)

        if player is None:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["forceSlot"]["error"]["missing_target"]["channel"],
                delete_after=5)
            return

        if self.list.slotEvent(channel, player, num, force=True):

            await self.io.writeEvent(channel)

            await channel.send(ctx.message.author.mention + " " + self.lang["forceSlot"]["success"]["channel"],
                               delete_after=5)

            try:
                player = ctx.guild.get_member(int(player))
                await player.send(
                    self.lang["forceSlot"]["success"]["target"].format(str(ctx.message.author.display_name),
                                                                       '/'.join(ctx.channel.name.split('-')[:-1])))
            except:
                pass

            log = "User: " + str(ctx.message.author).ljust(20) + "\t"
            log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
            log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
            self.logger.debug(log)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["forceSlot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="[User] Unslots an User or slot")
    @has_role(cfg["role"])
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def forceUnslot(self, ctx):  # [Admin Function] unslots an user or slot
        channel = ctx.message.channel
        args = ctx.message.content.split(" ")[1:]

        if not args:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["forceUnslot"]["error"]["missing_target"]["channel"],
                delete_after=5)
            return

        player = ""
        slot = ""

        if args[0].lower() == '--slot':
            if len(args) == 2:
                slot = args[1]
            else:
                await ctx.message.delete()
                await channel.send(
                    ctx.message.author.mention + " " + self.lang["forceUnslot"]["error"]["missing_slot"]["channel"],
                    delete_after=5)
                return
        else:
            if args[0].lower() == '--user':
                if len(args) > 1:
                    player = " ".join(args[1:])
                else:
                    await ctx.message.delete()
                    await channel.send(
                        ctx.message.author.mention + " " + self.lang["forceUnslot"]["error"]["missing_target"][
                            "channel"],
                        delete_after=5)
                    return
            else:
                player = " ".join(args)

            if not (len(player) == 18 and player[1:].isdigit()):
                buffer = self.io.get_user_id(player, channel)
                if not buffer:
                    await ctx.message.delete()
                    await channel.send(
                        ctx.message.author.mention + " " + self.lang["forceUnslot"]["error"]["general"]["channel"].format(
                            player),
                        delete_after=5)
                    return
                else:
                    player = buffer

        if self.list.unslotEvent(channel, player, slot):
            await self.io.writeEvent(channel)
            await channel.send(
                ctx.message.author.mention + " " + self.lang["forceUnslot"]["success"]["channel"].format(player),
                delete_after=5)
            await ctx.message.delete()

            log = "User: " + str(ctx.message.author).ljust(20) + "\t"
            log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
            log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
            self.logger.debug(log)

            try:
                await player.send(self.lang["forceUnslot"]["success"]["target"].format(channel.name))
            except:
                pass

        else:
            await channel.send(
                ctx.message.author.mention + " " + self.lang["forceUnslot"]["error"]["general"]["channel"].format(
                    player),
                delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [Group] [Description] Adds a Slot to the list")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def addslot(self, ctx):
        channel = ctx.message.channel
        argv = ctx.message.content.split(" ")

        if not len(argv) >= 3:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " + self.lang["addslot"]["error"]["arg_error"]["channel"],
                               delete_after=5)
            return

        slot_num = argv[1]
        group = argv[2]
        desc = " ".join(argv[3:])

        if self.list.addSlot(channel, slot_num, group, desc):
            await self.io.writeEvent(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["addslot"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["addslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [Description] Deletes a Slot from the list")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def delslot(self, ctx, slot_num):
        channel = ctx.message.channel

        if self.list.delSlot(channel, slot_num):
            await self.io.writeEvent(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["delslot"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()

        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["delslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [Description] Edits a Slot")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def editslot(self, ctx):
        channel = ctx.message.channel
        argv = ctx.message.content.split(" ")

        if not len(argv) >= 2:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["editslot"]["error"]["arg_error"]["channel"],
                delete_after=5)
            return

        slot_num = argv[1]
        desc = " ".join(argv[2:])

        if self.list.editSlot(channel, slot_num, desc):
            await self.io.writeEvent(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["editslot"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["editslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [optional name] Adds a group to the list")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def addgroup(self, ctx):
        channel = ctx.message.channel
        argv = ctx.message.content.split(" ")

        if not len(argv) >= 1:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["addgroup"]["error"]["arg_error"]["channel"],
                delete_after=5)
            return

        number = argv[1]
        if len(argv) > 2:
            name = " ".join(argv[2:])
        else:
            name = ""

        if self.list.addGroup(channel, number, name):
            await self.io.writeEvent(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["addgroup"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["addgroup"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="[name/number] Delets a group from the list")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def delgroup(self, ctx):
        channel = ctx.message.channel
        argv = ctx.message.content.split(" ")

        if not len(argv) >= 2:
            await ctx.message.delete()
            await channel.send(
                ctx.message.author.mention + " " + self.lang["delgroup"]["error"]["arg_error"]["channel"],
                delete_after=5)
            return

        if len(argv) > 1:
            name = " ".join(argv[1:])
        else:
            name = ""

        if self.list.delGroup(channel, name):
            await self.io.writeEvent(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["delgroup"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["delgroup"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(hidden=True, description="Sperrt bzw. öffnet die Slotliste")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def toggleLock(self, ctx):
        channel = ctx.message.channel

        result = self.list.toggleLock(channel)
        if result:
            await channel.send(ctx.message.author.mention + " " + self.lang["lock"]["toggle"]["success"],
                               delete_after=5)
            await self.io.writeEvent(channel, True)
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["lock"]["toggle"]["error"],
                               delete_after=5)

        await ctx.message.delete()
