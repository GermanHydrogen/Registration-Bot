import datetime
import logging
import os

import discord
from discord.ext.commands import Bot

import mysql.connector

from src.main.commands.user import User
from src.main.commands.admin import Admin
from src.main.handler.handler import Handler

from src.main.commands.notify import Locale, Global

from src.main.commands.interaction import Campaign, Swap
from src.main.handler.interaction import Handler as dmHandler

from src.main.handler.notify import Handler as ntHandler

from src.main.objects.util import CustomHelp

from config.loader import cfg, lang

''' --- onLoad ----'''

intents = discord.Intents.default()
intents.members = True
client = Bot(command_prefix="!", case_insensitive=True, intents=intents, help_command=CustomHelp())


# init sql
try:
    mydb = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        passwd=cfg["passwd"],
        database=cfg["database"]
    )
except mysql.connector.errors.InterfaceError:
    exit()

# init logger
path = os.path.dirname(os.path.abspath(__file__))

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

# load commands

client.add_cog(Handler(client, logger, mydb))
client.add_cog(dmHandler(client, lang, logger, mydb))

client.add_cog(User(client, lang, logger, mydb))
client.add_cog(Admin(client, lang, logger, mydb))

client.add_cog(Campaign(client, lang, logger, mydb))
client.add_cog(Swap(client, lang, logger, mydb))

client.add_cog(Global(client, lang, logger, mydb))
client.add_cog(Locale(client, lang, logger, mydb))

client.add_cog(ntHandler(client, lang, logger, mydb))

client.run(cfg['token'])
