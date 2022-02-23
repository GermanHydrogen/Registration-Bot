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
from src.main.handler.interaction import InteractionHandler as dmHandler

from src.main.handler.notify import NotifyHandler as ntHandler
from src.main.objects.interaction import Interaction
from src.main.objects.interaction_choice import Choice
from src.main.objects.mark import Mark
from src.main.objects.notify import EditLocale
from src.main.objects.slot import EditSlot
from src.main.objects.slotlist import IO

from src.main.objects.util import CustomHelp, Util

from config.loader import cfg, lang


class Bot(discord.ext.commands.Bot):
    def __init__(self, db: mysql.connector.MySQLConnection):
        intents = discord.Intents.default()
        intents.members = True
        super(Bot, self).__init__(command_prefix='!', intents=intents, case_insensitive=True, help_command=CustomHelp())

        # ----
        self.logger: logging.Logger
        self._init_logger()

        self.util = Util(self, db)
        self.io = IO(cfg, db, self.util)
        self.notify = EditLocale(self, self.logger, lang, db)
        self.list = EditSlot(db, self.notify)
        self.mark = Mark(db)
        self.interaction = Interaction(db)
        self.choice = Choice(db)

        # ---

        self.add_cog(Handler(self, self.logger, db, self.util))
        self.add_cog(dmHandler(self, lang, self.logger, db, self.io, self.choice, self.interaction, self.notify))
        self.add_cog(ntHandler(lang, self.logger, self.notify, self.util))

        self.add_cog(User(lang, self.logger, self.io, self.util, self.list, self.mark))
        self.add_cog(Admin(self, lang, self.logger, self.io, self.util, self.list))

        self.add_cog(Campaign(lang, self.logger, self.io, self.util, self.interaction))
        self.add_cog(Swap(lang, self.logger, self.io, self.util, self.interaction))

        self.add_cog(Global(lang, self.logger, db))
        self.add_cog(Locale(lang, self.logger, self.notify))

    def _init_logger(self) -> None:
        """
        Initialises the loggers for the Bot
        """
        path = os.path.dirname(os.path.abspath(__file__))

        today = datetime.date.today()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename=path + f"/logs/{today}.log", encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
        self.logger.addHandler(handler)

        discord_logger = logging.getLogger('discord')
        discord_logger.setLevel(logging.DEBUG)
        discord_handler = logging.FileHandler(filename=path + '/logs/discord.log', encoding='utf-8', mode='w')
        discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        discord_logger.addHandler(discord_handler)


if __name__ == '__main__':
    # init sql
    try:
        mydb = mysql.connector.connect(
            host=cfg["host"],
            user=cfg["user"],
            passwd=cfg["passwd"],
            database=cfg["database"]
        )

        bot = Bot(mydb)
        bot.run(cfg['token'])
    except mysql.connector.errors.InterfaceError:
        exit()
