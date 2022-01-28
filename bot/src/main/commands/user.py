import asyncio
import datetime

import discord.ext.commands
from discord.ext import commands

from src.main.objects.slotlist import IO
from src.main.objects.util import Util
from src.main.objects.slot import EditSlot, SlotTaken, InvalidSlot, SlotlistLocked
from src.main.objects.mark import Mark

from config.loader import cfg


class User(commands.Cog, name='User Commands'):

    def __init__(self, lang, logger, io: IO, util: Util, edit_slot: EditSlot, mark: Mark):
        self.lang = lang
        self.logger = logger

        self.io = io
        self.util = util
        self.list = edit_slot
        self.mark = mark

        self.mutex = asyncio.Lock()

    @commands.command(name="slot",
                      usage="[Number]",
                      help="Registers the caller for the event in the desired slot, which is given by its number. ",
                      brief="Register for a event.")
    @commands.guild_only()
    async def slot(self, ctx, number: str):
        channel = ctx.message.channel
        channel_author = self.util.get_channel_author(channel)

        game = (channel.name.split("-"))[-1]
        author = ctx.message.author
        backup = ctx.guild.get_member(cfg['backup'])
        await ctx.message.delete()

        await self.mutex.acquire()

        if game in cfg["games"].keys() and not (
                cfg["games"][game]["role"] in [x.id for x in ctx.message.author.roles]):

            # Instructor-Message
            instructor = []
            for elem in cfg["games"][game]["instructor"]:
                buffer = ctx.guild.get_member(int(elem))
                if buffer:
                    instructor.append(buffer)
                    await buffer.send(
                        self.lang["slot"]["new_user"]["instructor"].format(author, author.display_name, channel.name,
                                                                           number))

            if not instructor:
                instructor.append(ctx.guild.get_member(cfg['backup']))
                await instructor[0].send(
                    self.lang["slot"]["new_user"]["instructor"].format(author, author.display_name, channel.name,
                                                                       number))

            # User-Message
            if "welcome-msg" in cfg['games'][game].keys() and cfg['games'][game]['welcome-msg'] != "":
                await author.send(
                    cfg['games'][game]['welcome-msg'].format(cfg["games"][game]["name"],
                                                             " oder ".join([x.display_name for x in instructor]),
                                                             cfg["games"][game]["name"]).replace('\\n', '\n'))
            # Assign-Rule
            await author.add_roles(ctx.guild.get_role(cfg["games"][game]["beginner-role"]))

            if "strict" in cfg["games"][game].keys() and cfg["games"][game]["strict"]:
                # Channel-Message
                await channel_author.send(
                    self.lang["slot"]["new_user"]["channel"].format(author, author.display_name, channel.name, number))

                await ctx.message.delete()
                return

        try:
            self.list.slot(channel, author.id, number, user_displayname=author.display_name)
            await self.io.write(channel)
        except SlotTaken:
            await channel.send(author.mention + " " + self.lang["slot"]["slot"]["error"]["taken"]["channel"],
                               delete_after=5)
            return
        except InvalidSlot:
            await channel.send(author.mention + " " + self.lang["slot"]["slot"]["error"]["invalid"]["channel"],
                               delete_after=5)
            return
        except SlotlistLocked:
            await channel.send(author.mention + " " + self.lang["slot"]["slot"]["error"]["locked"]["channel"],
                               delete_after=5)
            return
        finally:
            self.mutex.release()

        await author.send(
            self.lang["slot"]["slot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
        try:
            await channel_author.send(
                self.lang["slot"]["slot"]["success"]["channel_author"].format(author,
                                                                              ctx.message.author.display_name,
                                                                              channel.name, number))
            await backup.send(self.lang["slot"]["slot"]["success"]["channel_author"].format(author,
                                                                                            ctx.message.author.display_name,
                                                                                            channel.name, number))
        except AttributeError:
            pass

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        self.logger.debug(log)

    @commands.command(name="unslot",
                      usage="",
                      help="Withdraws the caller from the event.",
                      brief="Withdraw from the event.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def unslot(self, ctx):
        channel = ctx.message.channel

        channel_author = self.util.get_channel_author(channel)

        backup = ctx.guild.get_member(cfg['backup'])
        try:
            index = self.list.unslot(channel, ctx.message.author.id)
        except InvalidSlot:
            await channel.send(ctx.message.author.mention + " " + self.lang["unslot"]["error"]["general"]["channel"],
                               delete_after=5)
            return
        finally:
            await ctx.message.delete()

        await self.io.write(channel)
        await ctx.message.author.send(
            self.lang["unslot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
        modifier = ["", "__"][int(str(datetime.date.today()) == "-".join(channel.name.split("-")[:-1]))]

        try:
            await channel_author.send(
                self.lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                        ctx.message.author.display_name,
                                                                        channel.name, index, modifier, modifier))
            await backup.send(self.lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                      ctx.message.author.display_name,
                                                                                      channel.name, index))
        except AttributeError:
            pass

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        self.logger.debug(log)

    @commands.command(name="mark",
                      usage="[marker type]",
                      help="Adds a marker to the user which is displayed in the slotlist behind the users name.",
                      brief="Adds a marker to the username in the slotlist.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def mark(self, ctx):
        channel = ctx.message.channel
        user = ctx.message.author

        args = ctx.message.content.split(" ")[1:]
        if len(args) == 0:
            await channel.send(
                ctx.message.author.mention + " " + self.lang["mark"]["error"]["args"],
                delete_after=5)
            await ctx.message.delete()
            return

        emoji_name = " ".join(args)
        if emoji_name in cfg['marks'].keys():
            if self.mark.add_mark(user.id, channel.id, emoji_name):
                await self.io.write(channel)
                await channel.send(
                    ctx.message.author.mention + " " + self.lang["mark"]["suc"],
                    delete_after=5)
            else:
                await channel.send(
                    ctx.message.author.mention + " " + self.lang["mark"]["error"]["duplicate"],
                    delete_after=5)
        else:
            await channel.send(
                ctx.message.author.mention + " " + self.lang["mark"]["error"]["typeNotFound"],
                delete_after=5)

        await ctx.message.delete()

    @commands.command(name="unmark",
                      usage="[marker type]",
                      help="Removes a marker from the user which is displayed in the slotlist behind the users name",
                      brief="Removes a maker from the username in the slotlist.")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def unmark(self, ctx):
        channel = ctx.message.channel
        user = ctx.message.author

        args = ctx.message.content.split(" ")[1:]
        if len(args) == 0:
            await channel.send(
                ctx.message.author.mention + " " + self.lang["unmark"]["error"]["args"],
                delete_after=5)
            await ctx.message.delete()
            return

        emoji_name = " ".join(args)
        if emoji_name in cfg['marks'].keys():
            if self.mark.remove_mark(user.id, channel.id, emoji_name):
                await self.io.write(channel)
                await channel.send(
                    ctx.message.author.mention + " " + self.lang["unmark"]["suc"],
                    delete_after=5)
            else:
                await channel.send(
                    ctx.message.author.mention + " " + self.lang["unmark"]["error"]["duplicate"],
                    delete_after=5)
        else:
            await channel.send(
                ctx.message.author.mention + " " + self.lang["unmark"]["error"]["typeNotFound"],
                delete_after=5)

        await ctx.message.delete()
