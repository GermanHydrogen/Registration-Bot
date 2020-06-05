import datetime
import logging
import os

import mysql.connector

from discord.ext.commands import Bot

from main.commands.user import User
from main.commands.admin import Admin
from main.util.handler import Handler

from notify.commands.master import Global
from notify.commands.locale import Locale

from dmInteraction.commands import Campaign
from dmInteraction.util.handler import Handler as dmHandler

from notify.util.handler import Handler as ntHandler

from config.loader import cfg
from config.loader import lang

''' --- onLoad ----'''
client = Bot(command_prefix="!", case_insensitive=True)
client.remove_command("help")


# init sql
try:
    mydb = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        passwd=cfg["passwd"],
        database=cfg["database"]
    )

    mycursor = mydb.cursor(buffered=True)
except:
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

client.add_cog(Handler(logger))
client.add_cog(dmHandler(client, lang, logger, mydb, mycursor))

client.add_cog(User(client, lang, logger, mydb, mycursor))
client.add_cog(Admin(client, lang, logger, mydb, mycursor))

client.add_cog(Campaign(client, lang, logger, mydb, mycursor))

client.add_cog(Global(client, lang, logger, mydb, mycursor))
client.add_cog(Locale(client, lang, logger, mydb, mycursor))

client.add_cog(ntHandler(client, lang, logger, mydb, mycursor))

client.run(cfg['token'])
