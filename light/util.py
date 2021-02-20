import discord
from discord.ext import commands
from discord.ext.commands import errors as derrors


async def send_error_msg(ctx: discord.Message, error: str):
    """
    Sends an error msg to the author and in the channel of the message
    :param ctx: Message
    :param error: Errormessage
    :return:
    """
    await ctx.send(f'{ctx.message.author.mention} {error}', delete_after=5)


class Util(commands.Cog):
    def __init__(self, logger):
        self.logger = logger

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel":
            await ctx.message.delete()

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)
        elif isinstance(error, derrors.CommandNotFound):
            await send_error_msg(ctx, "Command not found! Check **!help** for all commands")
        else:
            await send_error_msg(ctx, "Unexpected error. Please contact your local admin.")

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        log += str(error)

        self.logger.error(log)

        raise error
