import discord
from discord.ext import commands
from discord.ext.commands import errors as derrors


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
        async def send_error_msg(error_msg: str):
            """
            Sends an error msg to the author and in the channel of the message
            :param error_msg: Error message
            :return:
            """
            await ctx.send(f'{ctx.message.author.mention} {error_msg}', delete_after=5)

        if ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel":
            await ctx.message.delete()

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)
        elif isinstance(error, derrors.CommandNotFound):
            await send_error_msg("Command not found! Check **!help** for all commands")
        elif isinstance(error, derrors.MissingRequiredArgument):
            await send_error_msg(f"Arguments are missing! Check **!help {ctx.command}** for correct usage")

        elif hasattr(error, 'original') and hasattr(error.original, 'custom'):
            await send_error_msg(error.original.message)
        else:
            await send_error_msg("Unexpected error. Please contact your local admin.")

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        log += str(error)

        self.logger.error(log)

        raise error
