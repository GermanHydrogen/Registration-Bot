from discord.ext import commands


class Handler(commands.Cog):
    def __init__(self, logger):
        self.logger = logger

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel":
            await ctx.message.delete()

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)
        else:
            await ctx.send(ctx.message.author.mention + " Command not found! Check **!help** for all commands",
                           delete_after=5)

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        log += str(error)

        self.logger.error(log)

        raise error
