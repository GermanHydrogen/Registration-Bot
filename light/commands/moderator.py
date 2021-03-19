import discord
from discord.ext import commands

from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig, is_moderator


class Moderator(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, guild_config: RoleConfig):
        self.client = client
        self.state = state

        self.guildConfig = guild_config

    @commands.command(hidden=True, description="Initialize the slotlist")
    @commands.guild_only()
    @is_moderator
    async def create(self, ctx):  # makes the slotlist editable for the bot
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, ctx.message.author, self.client.user, True)
        await slotlist.write(channel, False)

        await ctx.message.author.send(f"The event **{channel.name}** was successfully created!")

        await ctx.message.delete()

    @commands.command(hidden=True, description="[Number] [User] Slots an User in a Slot")
    @commands.guild_only()
    @is_moderator
    async def forceSlot(self, ctx, slot_number: int, *, user_name: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.slot(slot_number, user_name)
        await slotlist.write()

        await ctx.send(f'{author.mention} {user_name} was successfully slotted.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(hidden=True, description="[User] Unslots an User or slot")
    @commands.guild_only()
    @is_moderator
    async def forceUnslot(self, ctx, *, user_name: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.unslot(user_name)
        await slotlist.write()

        await ctx.send(f'{author.mention} {user_name} was successfully slotted.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(hidden=True, description="[Number] [Description] Edit the description of a slot")
    @commands.guild_only()
    @is_moderator
    async def editSlot(self, ctx, number: str, *, description: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.edit_slot(number, description)
        await slotlist.write()

        await ctx.send(f'The description of slot #{number} was changed to {description}.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(hidden=True, description="[Number] [Description] Edit the description of a slot")
    @commands.guild_only()
    @is_moderator
    async def delSlot(self, ctx, number: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.remove_slot(number)
        await slotlist.write()

        await ctx.send(f'The slot #{number} was successfully removed.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass