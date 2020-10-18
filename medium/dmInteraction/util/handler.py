import datetime

from discord.ext import commands

from config.loader import cfg

from main.util.io import IO
from dmInteraction.util.edit import Edit
from dmInteraction.util.choice import Choice
from notify.util.editLocale import EditLocale


class Handler(commands.Cog):
    def __init__(self, client, lang, logger, db, cursor):

        self.client = client
        self.lang = lang
        self.logger = logger

        self.io = IO(cfg, db, cursor)
        self.choice = Choice(db, cursor)
        self.edit = Edit(db, cursor)

        self.notify = EditLocale(db, cursor)

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.client.get_guild(int(cfg['guild']))
        result = self.edit.cleanupMessage(datetime.date.today())

        if result is not None:
            camp = result[0]
            trade = result[1]

            if camp is not None:
                channels = camp[0]
                users = camp[1]

                for elem in channels:
                    channel = guild.get_channel(int(elem))
                    await self.io.writeEvent(channel)

                for elem in users:
                    user = self.client.get_user(int(elem[0]))
                    msg = await user.fetch_message(int(elem[1]))

                    await msg.delete()
                    await user.send("``` " + msg.content + " ```")
                    await user.send(self.lang['campaign']['private']['timeout'])

            if trade is not None:
                for elem in trade:
                    channel_name = guild.get_channel(int(elem[0])).name

                    req_user = self.client.get_user(int(elem[1]))
                    rec_user = self.client.get_user(int(elem[2]))

                    nickname = guild.get_member(int(elem[1])).display_name

                    msg = await rec_user.fetch_message(int(elem[3]))

                    await msg.delete()
                    await rec_user.send("``` " + msg.content + " ```")
                    await rec_user.send(self.lang['trade']['private']['timeout']['rec'].format(nickname, channel_name))

                    nickname = guild.get_member(int(elem[2])).display_name
                    await req_user.send(self.lang['trade']['private']['timeout']['req'].format(nickname, channel_name))

        print("Done")
        self.logger.info("Server Started")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.client.get_guild(int(cfg['guild']))

        if payload.guild_id is not None:
            return
        elif payload.user_id == self.client.user.id:
            return

        author = self.client.get_user(payload.user_id)

        channel = author.dm_channel
        if channel is None:
            channel = await author.create_dm()

        if channel.id != payload.channel_id:
            return

        msg = await channel.fetch_message(payload.message_id)

        if payload.emoji.name == '👎':
            result = self.choice.denyMessage(str(msg.id))
            if not result:  # if no message is found in db corresponding to the msg id
                await author.send(self.lang['trade']['private']['deny']['error'])

                log = "User: " + str(author.display_name).ljust(20) + "\t"
                log += "Channel:" + str('DM').ljust(20) + "\t"
                log += "Command: " + str('deny campaing-msg').ljust(20) + "\t"
                log += 'No corresponding msg was found in the DB'

                self.logger.debug(log)

            elif result[0] == 'trade' and isinstance(result[1], str):   # if one of the users has unslotted themselfes
                guild = self.client.get_guild(int(cfg['guild']))
                user = guild.get_member(int(result[1])).display_name

                await msg.delete()
                await channel.send("```" + msg.content + " ```")
                await author.send(self.lang['trade']['private']['unslot'].format(user))
            else:
                types = result[0]
                result = result[1]
                if types == "campaign":
                    guild = self.client.get_guild(int(cfg['guild']))
                    result = guild.get_channel(int(result))

                    await self.io.writeEvent(result)
                    await msg.delete()
                    await channel.send("``` " + msg.content + " ```")
                    await author.send(self.lang['campaign']['private']['deny']['success'])

                    log = "User: " + str(author.display_name).ljust(20) + "\t"
                    log += "Channel:" + str('DM').ljust(20) + "\t"
                    log += "Command: " + str('deny campaing-msg').ljust(20) + "\t"
                    self.logger.debug(log)

                else:
                    channel_name = guild.get_channel(int(result[0])).name

                    req_user = self.client.get_user(int(result[1]))
                    rec_user = self.client.get_user(int(result[2]))

                    nickname = guild.get_member(int(result[2])).display_name

                    await req_user.send(self.lang['trade']['private']['deny']['req'].format(nickname, channel_name))

                    await msg.delete()
                    await rec_user.send("``` " + msg.content + " ```")

                    nickname = guild.get_member(int(result[1])).display_name
                    await author.send(self.lang['trade']['private']['deny']['rec'].format(nickname, channel_name))

        elif payload.emoji.name == '👍':
            result = self.choice.acceptMessage(str(msg.id))
            if not result:      # if no message is found in db corresponding to the msg id
                await author.send(self.lang['trade']['private']['accept']['error'])

                log = "User: " + str(author).ljust(20) + "\t"
                log += "Channel:" + str('DM').ljust(20) + "\t"
                log += "Command: " + str('accept campaing-msg').ljust(20) + "\t"
                log += 'No corresponding msg was found in the DB'

                self.logger.debug(log)

            elif result[0] == 'trade' and isinstance(result[1], str):
                guild = self.client.get_guild(int(cfg['guild']))
                user = guild.get_member(int(result[1])).display_name

                await msg.delete()
                await channel.send("```" + msg.content + " ```")
                await author.send(self.lang['trade']['private']['unslot'].format(user))
            else:
                types = result[0]
                result = result[1]
                if types == "campaign":
                    guild = self.client.get_guild(int(cfg['guild']))
                    result = guild.get_channel(int(result))

                    await self.io.writeEvent(result)
                    await msg.delete()
                    await channel.send("```" + msg.content + " ```")
                    await author.send(self.lang['campaign']['private']['accept']['success'])

                    self.notify.create(result.id, author.id)

                    log = "User: " + str(author.display_name).ljust(20) + "\t"
                    log += "Channel:" + str('DM').ljust(20) + "\t"
                    log += "Command: " + str('accept campaing-msg').ljust(20) + "\t"
                    self.logger.debug(log)
                else:
                    channel = guild.get_channel(int(result[0]))

                    await self.io.writeEvent(channel)

                    req_user = self.client.get_user(int(result[1]))
                    rec_user = self.client.get_user(int(result[2]))

                    nickname = guild.get_member(int(result[2])).display_name

                    await req_user.send(self.lang['trade']['private']['accept']['req'].format(nickname, channel.name))

                    await msg.delete()
                    await rec_user.send("```" + msg.content + " ```")

                    nickname = guild.get_member(int(result[1])).display_name
                    await author.send(self.lang['trade']['private']['accept']['rec'].format(nickname, channel.name))

                    try:
                        backup = guild.get_member(cfg['backup'])

                        await backup.send(self.lang["trade"]["private"]["accept"]["backup"].format(
                            guild.get_member(int(result[2])).display_name,
                            guild.get_member(int(result[1])).display_name,
                            channel.name))

                    except:
                        pass