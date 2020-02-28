import datetime
import logging

from discord.ext import commands
from discord.ext.commands import Bot, has_role

from list import *

''' --- onLoad ----'''
client = Bot(command_prefix="!", case_insensitive=True)

client.remove_command("help")

path = os.path.dirname(os.path.abspath(__file__))

# load conf
if os.path.isfile(path + '/config.yml'):
    with open(path + "/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Please add config.yml to the dir")
    exit()

if not cfg["token"] and cfg["role"] and cfg["language"]:
    print("No valid token in config.yml")
    exit()

# load lang

if os.path.isfile(path + f'/msg_conf/{cfg["language"]}.yml'):
    with open(path + f'/msg_conf/{cfg["language"]}.yml') as ymlfile:
        lang = yaml.safe_load(ymlfile)
else:
    print("Language File missing")
    exit()

# load log

TODAY = datetime.date.today()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=f"logs/{TODAY}.log", encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
logger.addHandler(handler)

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
discord_handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discord_logger.addHandler(discord_handler)


# Campaign-MSG cleanup

@client.event
async def on_ready():
    guild = client.get_guild(int(cfg['guild']))
    result = cleanupReservation(TODAY)

    if result is not None:
        channels = result[0]
        users = result[1]

        for elem in channels:
            channel = guild.get_channel(int(elem))
            await writeEvent(channel)

        for elem in users:
            user = client.get_user(int(elem[0]))
            msg = await user.fetch_message(int(elem[1]))

            await msg.delete()
            await user.send("``` " + msg.content + " ```")
            await user.send(lang['campaign']['private']['timeout'])

    print("Done")


''' ---        ----'''


@client.event
async def on_command_error(ctx, error):
    if ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel":
        await ctx.message.delete()

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(ctx.message.author.mention + " " + str(error), delete_after=error.retry_after + 1)
    else:
        await ctx.send(ctx.message.author.mention + " Command not found! Check **!help** for all commands",
                       delete_after=5)

    log = "User: " + str(ctx.message.author).ljust(20) + "\t"
    log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
    log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
    log += str(error)

    logger.error(log)

    raise error


@client.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is not None:
        return
    elif payload.user_id == client.user.id:
        return

    author = client.get_user(payload.user_id)

    channel = author.dm_channel
    if channel is None:
        channel = await author.create_dm()

    if channel.id != payload.channel_id:
        return

    msg = await channel.fetch_message(payload.message_id)

    if payload.emoji.name == '👎':
        list_channel_id = denyReservation(str(msg.id))
        if list_channel_id:
            guild = client.get_guild(int(cfg['guild']))
            list_channel = guild.get_channel(int(list_channel_id))

            await writeEvent(list_channel)
            await msg.delete()

            await channel.send("``` " + msg.content + " ```")
            await author.send(lang['campaign']['private']['deny']['success'])
        else:
            await author.send(lang['campaign']['private']['deny']['error'])

    elif payload.emoji.name == '👍':
        list_channel_id = acceptReservation(str(msg.id))
        if list_channel_id:
            guild = client.get_guild(int(cfg['guild']))
            list_channel = guild.get_channel(int(list_channel_id))

            await writeEvent(list_channel)
            await msg.delete()

            await channel.send("```" + msg.content + " ```")
            await author.send(lang['campaign']['private']['accept']['success'])
        else:
            await author.send(lang['campaign']['private']['accept']['error'])


''' --- User Commands --- '''


@client.command(hidden=False, description="[number] slots the author of the message in the slot")
@commands.cooldown(1, 0.5, commands.BucketType.channel)
@commands.guild_only()
async def slot(ctx, num=""):
    channel = ctx.message.channel
    channel_author = get_channel_author(channel)

    author = ctx.message.author

    instructor = ctx.guild.get_member(cfg["arma3"])
    if not instructor:
        instructor = ctx.guild.get_member(cfg['backup'])

    backup = ctx.guild.get_member(cfg['backup'])

    if not ("ArmA3-Rudelkrieger" in [x.name for x in ctx.message.author.roles]):  # TODO: STATIC

        # User-Message
        await author.send(lang["slot"]["new_user"]["user"].format(instructor.display_name).replace('\\n', '\n'))
        # Channel-Message
        await channel_author.send(
            lang["slot"]["new_user"]["channel"].format(author, author.display_name, channel.name, num))
        # Instructor-Message
        await instructor.send(
            lang["slot"]["new_user"]["instructor"].format(author, author.display_name, channel.name, num))
        # Assign-Rule
        await author.add_roles([x for x in ctx.guild.roles if x.name == "ArmA3-Rudelanwärter"][0])

    elif num:

        if slotEvent(channel, author.id, num, user_displayname=author.display_name):
            await writeEvent(channel)

            await author.send(
                lang["slot"]["slot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
            try:
                await channel_author.send(
                    lang["slot"]["slot"]["success"]["channel_author"].format(author, ctx.message.author.display_name,
                                                                             channel.name, num))
            except:
                try:
                    await backup.send(lang["slot"]["slot"]["success"]["channel_author"].format(author,
                                                                                               ctx.message.author.display_name,
                                                                                               channel.name, num))
                except:
                    pass
                pass

            log = "User: " + str(ctx.message.author).ljust(20) + "\t"
            log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
            log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
            logger.debug(log)

        else:
            await channel.send(author.mention + " " + lang["slot"]["slot"]["error"]["general"]["channel"],
                               delete_after=5)

    else:
        await channel.send(
            ctx.message.author.mention + " " + lang["slot"]["slot"]["error"]["number_missing"]["channel"],
            delete_after=5)

    await ctx.message.delete()


@client.command(hidden=False, description="unslot the author of the message")
@commands.cooldown(1, 0.5, commands.BucketType.channel)
@commands.guild_only()
async def unslot(ctx):
    channel = ctx.message.channel

    channel_author = get_channel_author(channel)

    backup = ctx.guild.get_member(cfg['backup'])
    index = unslotEvent(channel, ctx.message.author.id)
    if index:
        await writeEvent(channel)
        await ctx.message.author.send(
            lang["unslot"]["success"]["user"].format('/'.join(ctx.channel.name.split('-')[:-1])))
        if str(TODAY) == "-".join(channel.name.split("-")[:-1]):
            try:
                await channel_author.send(lang["unslot"]["success"]["channel_author_date"].format(ctx.message.author,
                                                                                                  ctx.message.author.display_name,
                                                                                                  channel.name, index))
                await backup.send(lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                     ctx.message.author.display_name,
                                                                                     channel.name, index))
            except:
                pass
        else:

            try:
                await channel_author.send(lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                             ctx.message.author.display_name,
                                                                                             channel.name, index))
                await backup.send(lang["unslot"]["success"]["channel_author"].format(ctx.message.author,
                                                                                     ctx.message.author.display_name,
                                                                                     channel.name, index))

            except:
                pass

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        logger.debug(log)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["unslot"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


@client.command()
async def help(ctx):
    output = "My commands are:\n```yaml\n"

    for element in client.commands:
        if element != help and not element.hidden:
            output += f"{element}:".ljust(20) + f"{element.description}\n"

    if cfg['role'] in [x.name for x in ctx.message.author.roles]:
        output += "\n#Admin Commands:\n"
        for element in client.commands:
            if element != help and element.hidden:
                output += f"{element}:".ljust(20) + f"{element.description}\n"

    output += "```"

    await ctx.message.author.send(output)
    await ctx.message.delete()


''' --- Admin Commands --- '''


@client.command(hidden=True, description="Initialize the slotlist")
@has_role(cfg["role"])
@commands.guild_only()
async def create(ctx):  # makes the slotlist editable for the bot
    channel = ctx.message.channel
    out = []

    async for x in channel.history(limit=1000):
        if re.search("Slotliste", x.content):

            out.append("Slotlist")

            createEvent(x, ctx.message.author, client.user)
            await writeEvent(channel)
            if not x.author == client.user:
                await x.delete()

            break

    if "Slotlist" in out:
        await ctx.message.author.send(lang["create"]["success"]["user"])

        if not os.path.isfile(path + f'/logs/{ctx.message.channel.name}.log'):
            LOG_FILE = open(path + f"/logs/{ctx.message.channel.name}.log", "w+")
            LOG_FILE.write(f"---- Created: {datetime.datetime.now()} ----\n\n")
            LOG_FILE.close()

    else:
        await ctx.message.author.send(lang["create"]["error"]["general"]["user"])

    await ctx.message.delete()


@client.command(hidden=True, description="Initialize the slotlist")
@has_role(cfg["role"])
@commands.guild_only()
async def campaign(ctx, event):
    if not str(event).isdigit():
        event = get_event_id(event)
        if event is None:
            await ctx.message.channel.send(ctx.message.author.mention + " " + lang["campaign"]["channel"]["error"],
                                           delete_after=5)
            return

    slots = get_slots(str(event).strip())
    result = []
    date = datetime.date.today() + datetime.timedelta(days=2)

    if not slots:
        await ctx.message.delete()
        await ctx.message.channel.send(ctx.message.author.mention + " " + lang["campaign"]["channel"]["error"],
                                       delete_after=5)
        return
    else:
        event_date = get_event_date(str(ctx.message.channel.id))

        for elem in slots:
            if elem[0][0].isalpha():
                continue
            else:
                try:
                    user = client.get_user(int(elem[0]))
                    msg = await user.send(lang["campaign"]["request"].format(ctx.message.author.display_name,
                                                                             event_date,
                                                                             elem[2],
                                                                             elem[1]))
                    await msg.add_reaction('\N{THUMBS UP SIGN}')
                    await msg.add_reaction('\N{THUMBS DOWN SIGN}')
                    result.append((str(ctx.message.channel.id), elem[0], elem[1], str(msg.id), str(date)))
                except:
                    continue

    if reserveSlots(result):
        await ctx.message.channel.send(ctx.message.author.mention + " " + lang["campaign"]["channel"]["success"],
                                       delete_after=5)
    else:
        await ctx.message.channel.send(ctx.message.author.mention + " " + lang["campaign"]["channel"]["error"],
                                       delete_after=5)

    await writeEvent(ctx.message.channel)

    await ctx.message.delete()


@client.command(hidden=True, description="[Number] [User] Slots an User in a Slot")
@has_role(cfg["role"])
@commands.cooldown(1, 0.5, commands.BucketType.channel)
@commands.guild_only()
async def forceSlot(ctx):  # [Admin Function] slots an user
    channel = ctx.message.channel

    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["arg_error"]["channel"],
                           delete_after=5)
        return

    num = argv[1]
    player = argv[2:]

    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["missing_target"]["channel"],
                           delete_after=5)
        return

    player = " ".join(player)

    try:
        player = get_user_id(player, channel)
    except:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["missing_target"]["channel"],
                           delete_after=5)
        return

    if player is None:
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["missing_target"]["channel"],
                           delete_after=5)
        return

    if slotEvent(channel, player, num, force=True):

        await writeEvent(channel)

        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["success"]["channel"],
                           delete_after=5)

        try:
            player = ctx.guild.get_member(int(player))
            await player.send(lang["forceSlot"]["success"]["target"].format(str(ctx.message.author.display_name),
                                                                            '/'.join(ctx.channel.name.split('-')[:-1])))
        except:
            pass

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        logger.debug(log)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["forceSlot"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[User] Unslots an User")
@has_role(cfg["role"])
@commands.cooldown(1, 0.5, commands.BucketType.channel)
@commands.guild_only()
async def forceUnslot(ctx):  # [Admin Function] unslots an user
    channel = ctx.message.channel

    player = ctx.message.content.split(" ")[1:]
    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["forceUnslot"]["error"]["missing_target"]["channel"],
                           delete_after=5)
        return

    player = " ".join(player)
    if not (len(player) > 1 and player[1:].isdigit()):
        player = get_user_id(player, channel)

    if unslotEvent(channel, player):
        await writeEvent(channel)
        await channel.send(ctx.message.author.mention + " " + lang["forceUnslot"]["success"]["channel"].format(player),
                           delete_after=5)
        await ctx.message.delete()

        log = "User: " + str(ctx.message.author).ljust(20) + "\t"
        log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
        log += "Command: " + str(ctx.message.content).ljust(20) + "\t"
        logger.debug(log)

        try:
            await player.send(lang["forceUnslot"]["success"]["target"].format(channel.name))
        except:
            pass

    else:
        await channel.send(
            ctx.message.author.mention + " " + lang["forceUnslot"]["error"]["general"]["channel"].format(player),
            delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[Number] [Group] [Description] Adds a Slot to the list")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def addslot(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 3:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["addslot"]["error"]["arg_error"]["channel"],
                           delete_after=5)
        return

    slot_num = argv[1]
    group = argv[2]
    desc = " ".join(argv[3:])

    if addSlot(channel, slot_num, group, desc):
        await writeEvent(channel)

        await channel.send(ctx.message.author.mention + " " + lang["addslot"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["addslot"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[Number] [Description] Deletes a Slot from the list")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def delslot(ctx, slot_num):
    channel = ctx.message.channel

    if delSlot(channel, slot_num):
        await writeEvent(channel)

        await channel.send(ctx.message.author.mention + " " + lang["delslot"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()

    else:
        await channel.send(ctx.message.author.mention + " " + lang["delslot"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[Number] [Description] Edits a Slot")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def editslot(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["editslot"]["error"]["arg_error"]["channel"],
                           delete_after=5)
        return

    slot_num = argv[1]
    desc = " ".join(argv[2:])

    if editSlot(channel, slot_num, desc):
        await writeEvent(channel)

        await channel.send(ctx.message.author.mention + " " + lang["editslot"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["editslot"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[Number] [optional name] Adds a group to the list")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def addgroup(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 1:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["addgroup"]["error"]["arg_error"]["channel"],
                           delete_after=5)
        return

    number = argv[1]
    if len(argv) > 2:
        name = " ".join(argv[2:])
    else:
        name = ""

    if addGroup(channel, number, name):
        await writeEvent(channel)

        await channel.send(ctx.message.author.mention + " " + lang["addgroup"]["success"]["channel"], delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["addgroup"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


@client.command(hidden=True, description="[name/number] Delets a group from the list")
@has_role(cfg["role"])
@commands.cooldown(1, 2, commands.BucketType.channel)
@commands.guild_only()
async def delgroup(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " " + lang["delgroup"]["error"]["arg_error"]["channel"],
                           delete_after=5)
        return

    if len(argv) > 1:
        name = " ".join(argv[1:])
    else:
        name = ""

    if delGroup(channel, name):
        await writeEvent(channel)

        await channel.send(ctx.message.author.mention + " " + lang["delgroup"]["success"]["channel"],
                           delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + lang["delgroup"]["error"]["general"]["channel"],
                           delete_after=5)
        await ctx.message.delete()


''' ---        --- '''

client.run(cfg['token'])
