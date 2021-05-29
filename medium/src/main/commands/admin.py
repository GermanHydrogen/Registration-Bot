import re

from discord.ext import commands
from discord.ext.commands import has_role

from src.main.objects.slotlist import IO
from src.main.objects.util import Util
from src.main.objects.slot import EditSlot

from config.loader import cfg


class Admin(commands.Cog, name="Admin Commands"):
    def __init__(self, client, lang, logger, db):
        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db

        self.io = IO(cfg, client, db)
        self.util = Util(client, db)
        self.list = EditSlot(db)

    @commands.command(name="create",
                      usage="",
                      help="Creates an event in the channel from your 'slotlist message'.\n"
                           "This 'slotlist message' has to begin with the string '>Slotliste<'.\n"
                           "Slots have to be declared with the format: #[number] [slot description] - [opt: Username], "
                           "while the number can contain leading zeros, but has to be unique for every event.",
                      brief="Creates an event in the channel.")
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
            self.io.create(out, ctx.message.author, time, self.client.user, (arg == 'manuel'))
            await self.io.write(channel, True)

            await ctx.message.author.send(self.lang["create"]["success"]["user"])

            for x in out:
                if x.author != self.client.user:
                    await x.delete()

        else:
            await ctx.message.author.send(self.lang["create"]["error"]["general"]["user"])

        await ctx.message.delete()

    @commands.command(name="forceSlot",
                      usage="[number] [username]",
                      help="Registers a username for the given slot. The username argument, cam also be used for "
                           "dummy users. At this time the possible dummy users are:\n"
                           "'BLOCKED', 'K.I.A.', 'M.I.A.', 'Auf Nachfrage beim Missionsbauer'.",
                      brief="Registers a user or dummy for a given slot.")
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

        if self.list.slot(channel, player, num, force=True):

            await self.io.write(channel)

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

    @commands.command(name="forceUnslot",
                      usage="[option] [argument]",
                      help="If the option is not specified or '--user' is used, the user given in the argument "
                           "parameter is unsloted."
                           "If the option is set to '--slot', the slot given in the argument is emptied.",
                      brief="Unslots a user or empties a slot.")
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

        if self.list.unslot(channel, player, slot):
            await self.io.write(channel)
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

    @commands.command(name="addSlot",
                      usage="[number] [group] [description]",
                      help="Adds a new slot to a slot-group given by its title or index (counting from 0).\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "If you want to refer to the group by its title and the title contains white-spaces "
                           "you have to use quotation marks around the group argument.\n",
                      brief="Adds a new slot to a slot-group.")
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

        if self.list.add(channel, slot_num, group, desc):
            await self.io.write(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["addslot"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["addslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(name="delSlot",
                      usage="[number]",
                      help="Deletes a slot given by its number.",
                      brief="Deletes a given slot.")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def delslot(self, ctx, slot_num):
        channel = ctx.message.channel

        if self.list.delete(channel, slot_num):
            await self.io.write(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["delslot"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()

        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["delslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(name="editSlot",
                      usage="[number] [description]",
                      help="Edits the description of a slot given by its number.",
                      brief="Edits the description of a given slot.")
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

        if self.list.edit(channel, slot_num, desc):
            await self.io.write(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["editslot"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["editslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(name="addGroup",
                      usage="[index] [title]",
                      help="Adds a new slot-group.\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "The index argument, defines where the slot-group is placed in the order of the existing"
                           "slot-groups (counting from 0).\n"
                           "Slots can be added later with the addSlot command.",
                      brief="Adds a new slot-group.")
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

        if self.list.add_group(channel, number, name):
            await self.io.write(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["addgroup"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["addgroup"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(name="delGroup",
                      usage="[Identifier]",
                      help="Deletes a slot-group identified by its name or index (counting from 0).\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "The index argument, defines where the slot-group is placed in the order of the existing"
                           "slot-groups (counting from 0).\n"
                           "All slots of the slot-group are also deleted.",
                      brief="Deletes a slot-group.")
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

        if self.list.del_group(channel, name):
            await self.io.write(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["delgroup"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["delgroup"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(name="editGroup",
                      usage="[Identifier] [Name]",
                      help="Edit a slot-group title identified by its name or index (counting from 0).\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "The index argument, defines where the slot-group is placed in the order of the existing"
                           "slot-groups (counting from 0).\n"
                           "All slots of the slot-group are also deleted.",
                      brief="Edits the title of a slot-group.")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def editgroup(self, ctx, group, *, title):
        channel = ctx.message.channel

        if self.list.edit_group(channel, group, title):
            await self.io.write(channel, True)

            await channel.send(ctx.message.author.mention + " " + self.lang["editgroup"]["success"]["channel"],
                               delete_after=5)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["editgroup"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command(name="toggleLock",
                      usage="",
                      help="Toggles the lock of the slotlist. If the slotlist is locked, all slot requests are"
                           "rejected, but it is possible to edit the slotlist with admin commands. So"
                           "user still can be slotted through forceSlot etc..",
                      brief="Toggles the lock of the slotlist.")
    @has_role(cfg["role"])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    @commands.guild_only()
    async def toggleLock(self, ctx):
        channel = ctx.message.channel

        result = self.list.toggle_lock(channel)
        if result:
            await channel.send(ctx.message.author.mention + " " + self.lang["lock"]["toggle"]["success"],
                               delete_after=5)
            await self.io.write(channel, True)
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["lock"]["toggle"]["error"],
                               delete_after=5)

        await ctx.message.delete()
