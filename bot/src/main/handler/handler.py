from mysql.connector import errors
from discord.ext import commands

from bot.config.loader import cfg
from bot.src.main.objects.util import Util


class Handler(commands.Cog):
    def __init__(self, client, logger, db, util: Util):
        self.client = client
        self.logger = logger
        self.db = db

        self.util = util

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # --- Cooldown ---
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(ctx.message.author.mention +
                           f" You are missing the the parameter {error.param.name}",
                           delete_after=5)

        elif isinstance(error, commands.CommandInvokeError):
            # --- DB has gone away error ---
            if isinstance(error.original, errors.OperationalError) or isinstance(error.original, errors.DatabaseError):
                self.db.reconnect()  # Reconnect DB
                try:
                    await ctx.command.__call__(ctx, *(ctx.args[2:]))  # Retry
                except:
                    await ctx.send(ctx.message.author.mention + " Internal Error. Please try again.",
                                   delete_after=5)

                    log = "User: " + str(ctx.message.author).ljust(20) + "\t"
                    log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
                    log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
                    log += str(error.original)

                    self.logger.error(log)
                    raise
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

    # Valdiate Config
    @commands.Cog.listener()
    async def on_ready(self):
        def validate_role(guild, id):
            if (role := guild.get_role(id)) is None:
                print("\t" + '\033[91m' + str(id) + ' NOT Found!' + '\033[0m')
                self.logger.error("Role" + str(id) + " was NOT Found!")
            else:
                print("\t" + '\033[92m' + role.name + ' Found! ' + '\033[0m')

        if (guild := self.client.get_guild(int(cfg['guild']))) is None:
            print('\033[91m' + "Guild" + ' NOT Found! ' + '\033[0m')
            self.logger.error("Guild was not found!")
            exit(0)
        else:
            print('\033[92m' + 'Guild: ' + f'{guild.name}' + '\033[0m')

        if (backup := self.client.get_user(int(cfg['backup']))) is None:
            print('\033[91m' + 'The Backup-User was NOT Found!' + '\033[0m')
            self.logger.error("The Backup-User was NOT Found!")
        else:
            print('\033[92m' + 'Backup-User: ' + f'{backup.name}' + '\033[0m')

        print("Validating configured games")
        if len(cfg['games'].keys()) == 0:
            print("\033[93m" + "Warning: No games are configured" + "\033[0m")
        else:
            for game, info in cfg['games'].items():
                print(f"Testing {info['name']}")
                validate_role(guild, info['role'])
                validate_role(guild, info['beginner-role'])

                instructors = [self.client.get_user(x) for x in info['instructor']]
                if all([x is not None for x in instructors]):
                    print("\t" + '\033[92m' + 'Instructor' + ' Found! ' + '\033[0m')
                else:
                    print("\t" + '\033[91m' + 'Instructor' + ' NOT Found! ' + '\033[0m')
                    self.logger.error("Instructor for " + info['name'] + " not found in validation process!")

        print("Validating configured marks")
        if len(cfg['marks'].keys()) == 0:
            print("\033[93m" + "Warning: No marks are configured" + "\033[0m")
        else:
            for elem in cfg['marks'].keys():
                if self.util.get_emoji(cfg['marks'][elem]):
                    print("\t" + '\033[92m' + elem + ' Found! ' + '\033[0m')
                else:
                    print("\t" + '\033[91m' + elem + ' NOT Found! ' + '\033[0m')
                    self.logger.error("Mark " + elem + " not found in validation process!")

        print("VALIDATION COMPLETE")
