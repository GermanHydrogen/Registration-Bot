import os
import yaml
import datetime
import logging

from discord.ext.commands import Bot

from commands.admin import Admin
from commands.user import User
from commands.moderator import Moderator
from commands.objects.state import ClientState
from util import Util

''' --- onLoad ----'''
client = Bot(command_prefix="!", case_insensitive=True)

client.remove_command("help")

path = os.path.dirname(os.path.abspath(__file__))


#load conf
if os.path.isfile(os.path.join(path, 'config', 'config.yml')):
    with open(os.path.join(path, 'config', 'config.yml'), 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
elif os.path.isfile(os.path.join(path, 'config', 'default.yml')):
    with open(os.path.join(path, 'config', "default.yml"), 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Config file missing!")
    exit()

if os.path.isfile(os.path.join(path, 'config', f'{cfg["language"]}.yml')):
    with open(os.path.join(path, 'config', f'{cfg["language"]}.yml')) as ymlfile:
        lang = yaml.safe_load(ymlfile)
else:
    print("Language file missing!")
    exit()

#load log

TODAY = datetime.date.today()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=path + f"/logs/{TODAY}.log", encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
logger.addHandler(handler)

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
discord_handler = logging.FileHandler(filename=path + '/logs/discord.log', encoding='utf-8', mode='w')
discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discord_logger.addHandler(discord_handler)


''' ---        ----'''

state = ClientState()

client.add_cog(Admin(client=client, state=state, lang=lang))
client.add_cog(Moderator(client=client, state=state, lang=lang))
client.add_cog(User(client=client, state=state, lang=lang))
client.add_cog(Util(logger=logger))

client.run(cfg['token'])
