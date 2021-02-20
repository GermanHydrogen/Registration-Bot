import discord

from discord.ext import commands
from commands.objects.state import ClientState


class User(commands.Cog):
    def __init__(self, client: discord.user, state: ClientState, lang: dict):
        self.state = state
        self.client = client
        self.lang = lang

    @commands.command(hidden=False, description="[number] slots the author of the message in the slot")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def slot(self, ctx, slot_number: int):
        channel = ctx.message.channel
        author = ctx.message.author

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.slot(slot_number, author)
        await slotlist.write()

        await author.send(f"You slotted yourself for the event **{channel.name}** by **{channel.guild.name}**.")

        await ctx.message.delete()

    @commands.command(hidden=False, description="unslot the author of the message")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def unslot(self, ctx):
        channel = ctx.message.channel
        author = ctx.message.author

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.unslot(author)
        await slotlist.write()

        await author.send(f"You unslotted yourself from the event **{channel.name}** by **{channel.guild.name}**.")

        await ctx.message.delete()
