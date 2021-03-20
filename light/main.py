import os

from discord.ext.commands import Bot

from commands.admin import Admin
from commands.user import User
from commands.moderator import Moderator
from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig
from util import Util, init_logger

from config.loader import cfg

path = os.path.dirname(os.path.abspath(__file__))

# Bot definition
client = Bot(command_prefix=cfg['prefix'], case_insensitive=True)
client.remove_command("help")

# Get logger
logger = init_logger(path)

# Init slotlist buffer
state = ClientState()

# Get guild configs
guildConfig = RoleConfig(os.path.join(path, 'config', 'guildConfig.yml'))
guildConfig.load()

# Add commands
client.add_cog(Admin(client=client, state=state, guild_config=guildConfig))
client.add_cog(Moderator(client=client, state=state, guild_config=guildConfig))
client.add_cog(User(client=client, state=state, guild_config=guildConfig))
client.add_cog(Util(logger=logger))

client.run(cfg['token'])
