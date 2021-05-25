import datetime

from discord.ext import commands
from discord.ext.commands import has_role

from src.main.objects.slotlist import IO
from src.dmInteraction.util.util import Util
from src.dmInteraction.util.edit import Edit

from config.loader import cfg


class Campaign(commands.Cog, name='Admin Commands'):
    def __init__(self, client, lang, logger, db, cursor):

        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

        self.io = IO(cfg, client, db, cursor)
        self.util = Util(db, cursor)
        self.edit = Edit(db, cursor)

    @commands.command(name="campaign",
                      alias="copy",
                      usage="[slotlist id or name]",
                      help="Sends all users of the given slotlists a request, if they want to be slotted"
                           "in this slotlist. If the request is accepted, the user is automatically slotted."
                           "While the request is valid (~2days), the slots in the 'new' slotlist get blocked.",
                      brief="Effectively copies the users from one slotlist to the slotlist of the current channel.")
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

        # Check if an event exists in this channel
        if self.util.get_event_id(ctx.message.channel.name) is None:
            await ctx.message.channel.send(
                ctx.message.author.mention + " " + self.lang["campaign"]["channel"]["not_event"],
                delete_after=5)
            return

        # Cleanup
        old = self.edit.deleteAllMessages(str(ctx.message.channel.id))
        for elem in old:
            user = self.client.get_user(int(elem[0]))
            msg = await user.fetch_message(int(elem[1]))

            await msg.delete()
            await user.send("``` " + msg.content + " ```")
            await user.send(self.lang['campaign']['private']['timeout'])

        slots = self.util.get_slots(str(event).strip(), str(ctx.message.channel.id))
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

                    user = self.client.get_user(int(elem[0]))
                    msg = await user.send(self.lang["campaign"]["request"]['message'].format(
                        ctx.message.author.display_name,
                        event_date,
                        elem[2],
                        elem[1]))

                    if self.edit.reserveSlots(str(ctx.message.channel.id), elem[0], elem[1], str(msg.id), str(date)):
                        await msg.add_reaction('\N{THUMBS UP SIGN}')
                        await msg.add_reaction('\N{THUMBS DOWN SIGN}')
                    else:
                        await user.send(self.lang["campaign"]['request']['error']['user'])
                        await ctx.message.author.send(self.lang["campaign"]['request']['error']['admin'])

                        log = "User: " + str(user.name).ljust(20) + "\t"
                        log += "Channel:" + str('DM').ljust(20) + "\t"
                        log += "Command: " + str('creating campaing-msg').ljust(20) + "\t"
                        log += 'Campaign message could not be created'

                        self.logger.error(log)

        if self.edit.copyDummies(ctx.message.channel.id, event):
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


class Swap(commands.Cog, name='User Commands'):
    def __init__(self, client, lang, logger, db, cursor):
        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

        self.io = IO(cfg, client, db, cursor)
        self.util = Util(db, cursor)
        self.edit = Edit(db, cursor)

    @commands.command(name="trade",
                      alias='swap',
                      usage="[username]",
                      help="Send the given user a trade request to swap your slot with its."
                           "The user has two days to answer the request. This DOES NOT WORK if one"
                           "of you is slotted in a reserve slot!",
                      brief="Sends the given user a trade request to swap your slot with its.")
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

            msg = await user.send(
                self.lang["trade"]["request"].format(ctx.message.author, descr_rec, descr_req, channel.name))
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
