import re
import discord
from discord.ext import commands
from discord.ext.commands import has_role

from commands.objects.state import ClientState


class Admin(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, lang: dict):
        self.client = client
        self.state = state
        self.lang = lang
