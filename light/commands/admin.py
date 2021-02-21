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

    @commands.command(hidden=True, description="Initialize the slotlist")
    @has_role("Rosengarde")
    @commands.guild_only()
    async def create(self, ctx):  # makes the slotlist editable for the bot
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, ctx.message.author, self.client.user, True)
        await slotlist.write(channel, False)

        await ctx.message.author.send(f"The event **{channel.name}** was succesfully created!")

        await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [User] Slots an User in a Slot")
    @has_role("Rosengarde")
    @commands.guild_only()
    async def forceSlot(self, ctx, slot_number: int, *, user_name: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.slot(slot_number, user_name)
        await slotlist.write()

        await ctx.send(f'{author.mention} {user_name} was succesfully slotted.', delete_after=5)

        await ctx.message.delete()

    @commands.command(hidden=True, description="[User] Unslots an User or slot")
    @has_role("Rosengarde")
    @commands.guild_only()
    async def forceUnslot(self, ctx, *, user_name: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.unslot(user_name)
        await slotlist.write()

        await ctx.send(f'{author.mention} {user_name} was succesfully slotted.', delete_after=5)

        await ctx.message.delete()