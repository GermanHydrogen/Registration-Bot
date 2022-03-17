from discord.ext import commands

from bot.config.loader import cfg
from bot.src.main.objects.util import Util
from bot.src.main.objects.event_role import EventRole


class EventRoleHandler(commands.Cog):
    def __init__(self, client, event_role: EventRole):
        self.client = client
        self.event_role = event_role

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.client.get_guild(cfg['guild'])

        for game, c in cfg['games'].items():
            if 'temp_role' not in c:
                continue
            await self.event_role.manage_event_role(guild, game)


