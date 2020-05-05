import datetime
from discord.ext import commands

from main.util.io import IO
from main.util.util import Util
from main.util.editList import EditList

from config.loader import cfg


class User(commands.Cog):

    def __init__(self, client, lang, logger, db, cursor):

        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

        self.io = IO(cfg, db, cursor)
        self.util = Util(db, cursor)
        self.list = EditList(db, cursor)

    @commands.command(hidden=False, description="[number] slots the author of the message in the slot")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def slot(self, ctx, num=""):
        channel = ctx.message.channel
        channel_author = self.util.get_channel_author(channel)

        game = (channel.name.split("-"))[-1]
        author = ctx.message.author
        backup = ctx.guild.get_member(cfg['backup'])

        if game in cfg["games"].keys() and not (
                cfg["games"][game]["role"] in [x.name for x in ctx.message.author.roles]):

            # Instructor-Message
            instructor = []
            for elem in cfg["games"][game]["instructor"].replace(" ", "").split(","):
                buffer = ctx.guild.get_member(int(elem))
                if buffer:
                    instructor.append(buffer)
                    await buffer.send(
                        self.lang["slot"]["new_user"]["instructor"].format(author, author.display_name, channel.name,
                                                                           num))

            if not instructor:
                instructor.append(ctx.guild.get_member(cfg['backup']))
                await instructor[0].send(
                    self.lang["slot"]["new_user"]["instructor"].format(author, author.display_name, channel.name, num))

            # User-Message
            await author.send(
                self.lang["slot"]["new_user"]["user"].format(cfg["games"][game]["name"],
                                                             instructor[0].display_name,
                                                             cfg["games"][game]["name"]).replace('\\n', '\n'))
            # Channel-Message
            await channel_author.send(
                self.lang["slot"]["new_user"]["channel"].format(author, author.display_name, channel.name, num))
            # Assign-Rule
            await author.add_roles(
                [x for x in ctx.guild.roles if x.name == cfg["games"][game]["beginner-role"]][0])

        elif num:

            if self.list.slotEvent(channel, author.id, num, user_displayname=author.display_name):
                await self.io.writeEvent(channel)

                await author.send(
                    self.lang["slot"]["slot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
                try:
                    await channel_author.send(
                        self.lang["slot"]["slot"]["success"]["channel_author"].format(author,
                                                                                      ctx.message.author.display_name,
                                                                                      channel.name, num))
                    await backup.send(self.lang["slot"]["slot"]["success"]["channel_author"].format(author,
                                                                                                    ctx.message.author.display_name,
                                                                                                    channel.name, num))
                except:
                    pass

                log = "User: " + str(ctx.message.author).ljust(20) + "\t"
                log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
                log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
                self.logger.debug(log)

            else:
                await channel.send(author.mention + " " + self.lang["slot"]["slot"]["error"]["general"]["channel"],
                                   delete_after=5)

        else:
            await channel.send(
                ctx.message.author.mention + " " + self.lang["slot"]["slot"]["error"]["number_missing"]["channel"],
                delete_after=5)

        await ctx.message.delete()

    @commands.command(hidden=False, description="unslot the author of the message")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def unslot(self, ctx):
        channel = ctx.message.channel

        channel_author = self.util.get_channel_author(channel)

        backup = ctx.guild.get_member(cfg['backup'])
        index = self.list.unslotEvent(channel, ctx.message.author.id)
        if index:
            await self.io.writeEvent(channel)
            await ctx.message.author.send(
                self.lang["unslot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
            if str(datetime.date.today()) == "-".join(channel.name.split("-")[:-1]):
                try:
                    await channel_author.send(
                        self.lang["unslot"]["success"]["channel_author_date"].format(ctx.message.author,
                                                                                     ctx.message.author.display_name,
                                                                                     channel.name, index))
                    await backup.send(self.lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                              ctx.message.author.display_name,
                                                                                              channel.name, index))
                except:
                    pass
            else:

                try:
                    await channel_author.send(
                        self.lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                ctx.message.author.display_name,
                                                                                channel.name,
                                                                                index))
                    await backup.send(self.lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                              ctx.message.author.display_name,
                                                                                              channel.name, index))

                except:
                    pass

            log = "User: " + str(ctx.message.author).ljust(20) + "\t"
            log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
            log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
            self.logger.debug(log)

            await ctx.message.delete()
        else:
            await channel.send(ctx.message.author.mention + " " + self.lang["unslot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()

    @commands.command()
    async def help(self, ctx):
        output = "My commands are:\n```yaml\n"

        for element in self.client.commands:
            if element != help and not element.hidden:
                output += f"{element}:".ljust(20) + f"{element.description}\n"

        if cfg['role'] in [x.name for x in ctx.message.author.roles]:
            output += "\n#Admin Commands:\n"
            for element in self.client.commands:
                if element != help and element.hidden:
                    output += f"{element}:".ljust(20) + f"{element.description}\n"

        output += "```"

        await ctx.message.author.send(output)
        await ctx.message.delete()
