import os
import datetime
import logging

import discord
from discord.ext import commands
from discord.ext.commands import errors as derrors


async def send_msg(ctx: discord.ext.commands.Context, error_msg: str) -> None:
    """
    Sends an error msg to the author and in the channel of the message
    :param ctx: Message to reply to
    :param error_msg: Error message
    :return:
    """
    await ctx.send(f'{ctx.message.author.mention} {error_msg}', delete_after=5)


def init_logger(path: str) -> logging.Logger:
    """
    Init the custom logger and the general discord logging
    :param path: Path to the log dir
    :return:
    """
    today = datetime.date.today()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename=os.path.join(path, 'logs', f'{today}.log'), encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
    logger.addHandler(handler)

    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    discord_handler = logging.FileHandler(filename=os.path.join(path, 'logs', 'discord.log'), encoding='utf-8', mode='w')
    discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    discord_logger.addHandler(discord_handler)

    return logger


class CustomParentException(Exception):
    def __init__(self):
        self.message = ""
        self.custom = True
        super().__init__()

    def __str__(self):
        return self.message


class Util(commands.Cog):
    def __init__(self, logger):
        self.logger = logger

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel":
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                pass

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)
        elif isinstance(error, derrors.CommandNotFound):
            await send_msg(ctx, "Command not found! Check **!help** for all commands")
        elif isinstance(error, derrors.MissingRequiredArgument):
            await send_msg(ctx, f"Arguments are missing! Check **!help {ctx.command}** for correct usage")
        elif isinstance(error, derrors.BadBoolArgument):
            await send_msg(ctx, f"The given boolean is argument is faulty! Check **!help {ctx.command}** for correct "
                                f"usage ")
        elif isinstance(error, derrors.MissingRole):
            await send_msg(ctx, f"You are missing the configured {error.missing_role}.")

        elif hasattr(error, 'original') and hasattr(error.original, 'custom'):
            await send_msg(ctx, error.original.message)
        else:
            await send_msg(ctx, "Unexpected error. Please contact your local admin.")

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        log += str(error)

        self.logger.error(log)

        raise error

