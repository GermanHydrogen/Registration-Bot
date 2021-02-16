from discord.ext import commands
import commands.objects.slotlist as sl
from commands.objects.state import ClientState


class User(commands.Cog):
    def __init__(self, state: ClientState, lang: dict):
        self.state = state
        self.lang = lang

    @commands.command(hidden=False, description="[number] slots the author of the message in the slot")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def slot(self, ctx, num: int):
        channel = ctx.message.channel
        author = ctx.message.auther

        slotlist = self.state.get_slotlist(guild_id=channel.guild.id, channel_id=channel.id)

        if slotlist is None:
            slotlist = sl.SlotList(channel, ctx.message.auther)

            if slotlist is None:
                pass
        try:
            slotlist.slot(num, author)
        except sl.SlotTaken:
            await channel.send(author.mention + " " + self.lang["slot"]["slot"]["error"]["general"]["channel"],
                               delete_after=5)
            await ctx.message.delete()
            return

        await slotlist.write(edit=True)
        await ctx.message.delete()
