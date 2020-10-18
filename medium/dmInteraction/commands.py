import datetime

from discord.ext import commands
from discord.ext.commands import has_role

from main.util.io import IO
from dmInteraction.util.util import Util
from dmInteraction.util.edit import Edit

from config.loader import cfg


class Campaign(commands.Cog):
    def __init__(self, client, lang, logger, db, cursor):

        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

        self.io = IO(cfg, db, cursor)
        self.util = Util(db, cursor)
        self.edit = Edit(db, cursor)

    @commands.command(hidden=True, description="Initialize the slotlist")
    @has_role(cfg["role"])
    @commands.guild_only()
    async def campaign(self, ctx, event):
        if not str(event).isdigit():
            event = self.util.get_event_id(event)
            if event is None:
                await ctx.message.channel.send(
                    ctx.message.author.mention + " " + self.lang["campaign"]["channel"]["error"],
                    delete_after=5)
                return

        slots = self.util.get_slots(str(event).strip(), str(ctx.message.channel.id))
        result = []
        date = datetime.date.today() + datetime.timedelta(days=2)

        if not slots:
            await ctx.message.delete()
            await ctx.message.channel.send(ctx.message.author.mention + " " + self.lang["campaign"]["channel"]["error"],
                                           delete_after=5)
            return
        else:
            event_date = self.util.get_event_date(str(ctx.message.channel.id))

            for elem in slots:
                if elem[0][0].isalpha():
                    continue
                else:
                    try:
                        user = self.client.get_user(int(elem[0]))
                        msg = await user.send(self.lang["campaign"]["request"].format(ctx.message.author.display_name,
                                                                                      event_date,
                                                                                      elem[2],
                                                                                      elem[1]))
                        await msg.add_reaction('\N{THUMBS UP SIGN}')
                        await msg.add_reaction('\N{THUMBS DOWN SIGN}')
                        result.append((str(ctx.message.channel.id), elem[0], elem[1], str(msg.id), str(date)))
                    except:
                        continue

        if self.edit.reserveSlots(result):
            await ctx.message.channel.send(
                ctx.message.author.mention + " " + self.lang["campaign"]["channel"]["success"],
                delete_after=5)

            log = "User: " + str(ctx.message.author).ljust(20) + "\t"
            log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
            log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
            self.logger.debug(log)

        else:
            await ctx.message.channel.send(ctx.message.author.mention + " " + self.lang["campaign"]["channel"]["error"],
                                           delete_after=5)

        await self.io.writeEvent(ctx.message.channel)

        await ctx.message.delete()

    @commands.command(hidden=False, description="[user] Sends a swap request to the user")
    @commands.cooldown(1, 0.5, commands.BucketType.channel)
    @commands.guild_only()
    async def swap(self, ctx):
        channel = ctx.message.channel
        date = datetime.date.today() + datetime.timedelta(days=1)

        argv = ctx.message.content.split(" ")

        if not len(argv) >= 2:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " + self.lang["trade"]["channel"]["error"]["arg"],
                               delete_after=5)
            return

        reqUser = ctx.message.author.id

        recUser = self.io.get_user_id(" ".join(argv[1:]), channel)

        if not recUser:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " + self.lang["trade"]["channel"]["error"]["val"],
                               delete_after=5)

            return
        valid = self.edit.validateSwap(channel.id, reqUser, recUser)

        if valid == 0:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " + self.lang["trade"]["channel"]["error"]["val"],
                               delete_after=5)

            return
        elif valid == 2:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " + self.lang["trade"]["channel"]["error"]["limit"],
                               delete_after=5)

        try:
            user = self.client.get_user(int(recUser))
            descr_req = self.util.get_slot_description(str(channel.id), str(reqUser))
            descr_rec = self.util.get_slot_description(str(channel.id), str(recUser))

            msg = await user.send(self.lang["trade"]["request"].format(ctx.message.author, descr_rec, descr_req, channel.name))
            await msg.add_reaction('\N{THUMBS UP SIGN}')
            await msg.add_reaction('\N{THUMBS DOWN SIGN}')

            self.edit.createSwap(str(channel.id), str(reqUser), str(recUser), str(msg.id), date)
        except:
            await ctx.message.delete()
            await channel.send(ctx.message.author.mention + " " + self.lang["trade"]["channel"]["error"]["send"],
                               delete_after=5)
            return

        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + self.lang["trade"]["channel"]["success"],
                           delete_after=5)
