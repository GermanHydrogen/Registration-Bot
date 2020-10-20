from mysql.connector import errors
from discord.ext import commands


class Handler(commands.Cog):
    def __init__(self, logger, db):
        self.logger = logger
        self.db = db

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # --- Cooldown ---
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)

        # --- DB has gone away error ---
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, errors.OperationalError) or isinstance(error.original, errors.DatabaseError):
                self.db.reconnect()     # Reconnect DB
                try:
                    await ctx.command.__call__(ctx, *(ctx.args[2:]))    # Retry
                except:
                    await ctx.send(ctx.message.author.mention + " Internal Error. Please try again.",
                           delete_after=5)

                    log = "User: " + str(ctx.message.author).ljust(20) + "\t"
                    log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
                    log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
                    log += str(error.original)

                    self.logger.error(log)
                return

        else:
            await ctx.send(ctx.message.author.mention + " Command not found! Check **!help** for all commands",
                           delete_after=5)

        if ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel":
            await ctx.message.delete()

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        log += str(error)

        self.logger.error(log)

        raise error
