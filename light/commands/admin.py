import re
import discord
from discord.ext import commands
from discord.ext.commands import has_role

import commands.objects.slotlist as sl
from commands.objects.state import ClientState


class Admin(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, lang: dict):
        self.client = client
        self.state = state
        self.lang = lang

    @commands.command(hidden=True, description="Initialize the slotlist")
    @has_role("Rosengarde")
    @commands.guild_only()
    async def create(self, ctx):  # makes the slotlist editable for the bot
        channel = ctx.message.channel

        try:
            slotlist = await self.state.get_slotlist(channel, ctx.message.author, self.client.user, True)
        except sl.SlotlistNotFound:
            await ctx.message.author.send(self.lang["create"]["error"]["general"]["user"])
            await ctx.message.delete()
            return

        await slotlist.write(channel, False)

        await ctx.message.author.send(self.lang["create"]["success"]["user"])
        await ctx.message.delete()
