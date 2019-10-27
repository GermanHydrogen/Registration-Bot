import os
import yaml
import datetime

import re
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions, has_role

from list import SlotList, get_list, get_member, get_channel_author

''' --- onLoad ----'''
client = Bot(command_prefix="!", case_insensitive=True)

client.remove_command("help")

path = os.path.dirname(os.path.abspath(__file__))


#load conf
if os.path.isfile(path + '/config.yml'):
    with open(path + "/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Please add config.yml to the dir")
    exit()

if not cfg["token"] and cfg["role"]:
    print("No valid token in config.yml")
    exit()

TODAY = datetime.date.today()

if not os.path.isfile(path + f'/logs/{TODAY}.log'):
    LOG_FILE = open(path + f"/logs/{TODAY}.log", "w+")
    LOG_FILE.write(f"---- Created: {datetime.datetime.now()} ----\n\n")
    LOG_FILE.close()


''' ---        ----'''


@client.event
async def on_command_error(ctx, error):
    if(ctx.message.channel != "DMChannel" and ctx.message.channel != "GroupChannel"):
        await ctx.message.delete()

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(ctx.message.author.mention + " " +str(error), delete_after=error.retry_after + 1)
    else:
        await ctx.send(ctx.message.author.mention + " Command not found! Check **!help** for all commands", delete_after=5)

    f = open(path + f"/logs/{TODAY}.log", "a")
    log =  str(datetime.datetime.now()) +                     "\t"
    log += "User: " + str(ctx.message.author).ljust(20) +    "\t"
    log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
    log += "Command: " + str(ctx.message.content) + "\t"
    log += str(error) + "\n"
    f.write(log)
    f.close()

    raise error

''' --- User Commands --- '''

@client.command(hidden = False, description= "[number] slots the author of the message in the slot")
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def slot(ctx, num=""):
    channel = ctx.message.channel
    channel_author = await get_channel_author(ctx.channel)
    channel_name = channel.name.split("-")[-1]

    author = ctx.message.author

    instructor = ctx.guild.get_member(cfg[channel_name])
    if not instructor:
        instructor = ctx.guild.get_member(cfg['backup'])


    if not (channel_name in [x.name for x in ctx.message.author.roles]):

        # User-Message
        await author.send(f"Welcome to the Rosenrudel!\nTo proceed to your first Mission, please report to your Instructor **{instructor.display_name}**.")
        # Channel-Message
        await channel_author.send(f"The **new** User: {author} as {author.display_name} **tried** to slot for {channel.name} in Position #{num}")
        # Instructor-Message
        await instructor.send(f"The **new** User: {author} as {author.display_name} **tried** to slot for {channel.name} in Position #{num}")

    elif num:
        liste, x = await get_list(ctx, client)

        list = SlotList(liste, message = x)

        if(list.enter(ctx.message.author.display_name, num)):
            await list.write()
            try:
                await channel_author.send(f"User: {author} as {ctx.message.author.display_name} **slotted** for {channel.name} in Position #{num}")
                await author.send(f"You have signed up for the assault on {'/'.join( ctx.channel.name.split('-')[:-1])}.")
            except:
                pass
        else:
            await channel.send(author.mention + " The given slot isn't valid or available!", delete_after=5)

        del list

    else:
        await channel.send(ctx.message.author.mention + " Please specify the slot (Number)!", delete_after=5)

    await ctx.message.delete()

@client.command(hidden = False, description="unslot the author of the message")
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def unslot(ctx):
    channel = ctx.message.channel

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message = x)

    if list.exit(ctx.message.author.display_name):
        await list.write()
        del list
        try:
            await (await get_channel_author(ctx.channel)).send(f"User: {ctx.message.author} as {ctx.message.author.display_name} **unslotted** for {channel.name}")
            await ctx.message.author.send(f"Guess we'll be kicking russian butts without you on {'/'.join( ctx.channel.name.split('-')[:-1])}. Who do you think you are, deserting your comrades like this?")
        except:
            pass
        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " Du bist nicht eingetragen!", delete_after=5)
        await ctx.message.delete()

@client.command()
async def help(ctx):
    output = "My commands are:\n```yaml\n"

    for element in client.commands:
        if(element != help and not element.hidden):
            output += f"{element}:".ljust(20) + f"{element.description}\n"

    if (cfg['role'] in [x.name for x in ctx.message.author.roles]):
        output += "\n#Admin Commands:\n"
        for element in client.commands:
            if (element != help and element.hidden):
                output += f"{element}:".ljust(20) + f"{element.description}\n"


    output += "```"

    await ctx.message.author.send(output)
    await ctx.message.delete()

''' --- Admin Commands --- '''

@client.command(hidden = True, description= "Initialize the slotlist")
@has_role(cfg["role"])
@commands.guild_only()
async def create(ctx):                          #makes the slotlist editable for the bot
    channel = ctx.message.channel
    out = []

    async for x in channel.history(limit=1000):
        msg = x.content
        if re.search("Slotliste", msg):
            await x.delete()  #await (await channel.send(msg)).pin()

            out.append("Slotlist")

            liste = SlotList(msg, channel=channel)
            await liste.write()
            del liste


    if "Slotlist" in out:
        await ctx.message.author.send("The event was created successfully")
    else:
        await ctx.message.author.send("The Slotlist was not found!")

    await ctx.message.delete()



@client.command(hidden = True, description="[User] Unslots an User")
@has_role(cfg["role"])
@commands.guild_only()
async def forceUnslot(ctx):           # [Admin Function] unslots an user
    channel = ctx.message.channel

    player = ctx.message.content.split(" ")[1:]
    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Please specify a **user**!", delete_after=5)
        return

    seperator  = " "
    player = seperator.join(player)

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message = x)

    if list.exit(player):
        await list.write()
        await channel.send(ctx.message.author.mention + " " + player +" wurde erfolgreich  ausgetragen!", delete_after=5)
        await ctx.message.delete()

        try:
            member = get_member(ctx.guild, player)
            await member.send(f"You were removed from the Operation {ctx.channel.name}")
        except:
            pass

    else:
        await channel.send(ctx.message.author.mention + " " + player + " isn't registered!", delete_after=5)
        await ctx.message.delete()

    del list


@client.command(hidden = True, description="[Number] [User] Slots an User in a Slot")
@has_role(cfg["role"])
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def forceSlot(ctx):      # [Admin Function] slots an user
    channel = ctx.message.channel

    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Please specify a **slot** and **user**!", delete_after=5)
        return


    num = argv[1]
    player = argv[2:]

    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Please specify a **user**!", delete_after=5)
        return

    seperator = " "
    player = seperator.join(player)


    liste, x = await get_list(ctx, client)

    list = SlotList(liste, message = x)

    if (list.enter(player, num)):
        await list.write()
        del list
        await channel.send(ctx.message.author.mention + " The user was successfully slotted!", delete_after=5)



        try:
            member = get_member(ctx.guild, player)
            await member.send(f"You were enlisted to the Operation on {'/'.join( ctx.channel.name.split('-')[:-1])} by {str(ctx.message.author.display_name)}")
        except:
            pass

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " The given slot is invalid or available!", delete_after=5)
        await ctx.message.delete()

@client.command(hidden = True, description="[Number] [Description] Adds a Slot to the list")
@has_role(cfg["role"])
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def addslot(ctx):
    channel = ctx.message.channel
    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Please specify a **slot** and **description**!", delete_after=5)
        return


    slot = argv[1]
    desc = " ".join(argv[2:])

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if(list.add(slot, desc)):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " The slot was successfully added!", delete_after=5)

        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " The given slot is invalid or unavailable!", delete_after=5)
        await ctx.message.delete()

@client.command(hidden = True, description="[Number] [Description] Deletes a Slot from the list")
@has_role(cfg["role"])
@commands.cooldown(1,2, commands.BucketType.channel)
@commands.guild_only()
async def delslot(ctx, slot):
    channel = ctx.message.channel
    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message=x)

    if list.delete(slot):
        await list.write()
        del list

        await channel.send(ctx.message.author.mention + " The slot was successfully deleted!", delete_after=5)

        await ctx.message.delete()

    else:
        await channel.send(ctx.message.author.mention + " The given slot is invalid or unavailable!", delete_after=5)
        await ctx.message.delete()
''' ---        --- '''

client.run(cfg['token'])
