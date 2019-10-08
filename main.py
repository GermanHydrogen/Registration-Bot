import os
import yaml
import datetime

import re
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

from list import SlotList, get_list



''' --- onLoad ----'''
client = Bot("!")

client.remove_command("help")

path = os.path.dirname(os.path.abspath(__file__))

#load conf
if os.path.isfile(path + '/config.yml'):
    with open(path + "/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Please add config.yml to the dir")
    exit()

if not cfg["token"]:
    print("No valid token in config.yml")
    exit()

TODAY = datetime.date.today()

if not  os.path.isfile(path + f'/{TODAY}.log'):
    LOG_FILE = open(f"{TODAY}.log", "w")
    LOG_FILE.write(f"---- Created: {datetime.datetime.now()} ----\n\n")
    LOG_FILE.close()

''' ---        ----'''


@client.event
async def on_command_error(ctx, error):
    await ctx.message.delete()

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(ctx.message.author.mention + " " +str(error), delete_after=error.retry_after + 1)
    else:
        await ctx.send(ctx.message.author.mention + " Command not found! Check **!help** for all commands", delete_after=5)

    f = open(f"{TODAY}.log", "a")
    log =  str(datetime.datetime.now()) +                     "\t"
    log += "User: " + str(ctx.message.author).ljust(20) +    "\t"
    log += "Channel:" + str(ctx.message.channel).ljust(20) + "\t"
    log += str(error) + "\n"
    f.write(log)
    f.close()

    raise error

''' --- User Commands --- '''

@client.command(hidden = False, description= "[number] slots the author of the message in the slot")
@commands.cooldown(1,2, commands.BucketType.channel)
async def slot(ctx, num=""):
    channel = ctx.message.channel
    if num:

        liste, x = await get_list(ctx, client)

        list = SlotList(liste, message = x)

        if(list.enter(ctx.message.author.display_name, num)):
            await list.write()
            await ctx.message.author.send("Du hast Dich für das Event " + ctx.message.channel.name + " eingetragen!")
        else:
            await channel.send(ctx.message.author.mention + " Der angegebene Slot ist ungültig oder schon belegt!", delete_after=5)

        del list

    else:
        await channel.send(ctx.message.author.mention + " Bitte spezifiziere den Slot (Nummer)!", delete_after=5)

    await ctx.message.delete()

@client.command(hidden = False, description="unslot the author uf the message")
@commands.cooldown(1,2, commands.BucketType.channel)
async def unslot(ctx):
    channel = ctx.message.channel

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message = x)

    if list.exit(ctx.message.author.display_name):
        await list.write()
        del list
        await ctx.message.author.send("Du hast Dich für das Event " + ctx.message.channel.name + " ausgetragen!")
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

    output += "\n#Admin Commands:\n"

    if (ctx.message.author.permissions_in(ctx.message.channel).manage_channels):
        for element in client.commands:
            if (element != help and element.hidden):
                output += f"{element}:".ljust(20) + f"{element.description}\n"


    output += "```"

    await ctx.message.author.send(output)
    await ctx.message.delete()

''' --- Admin Commands --- '''

@client.command(hidden = True, description= "Initialize the slotlist")
@has_permissions(manage_channels = True)
async def create(ctx):                          #makes the slotlist editable for the bot
    channel = ctx.message.channel
    async for x in channel.history(limit=1000):
        msg = x.content
        if msg == "!create":
            await x.delete()
        elif re.search("Slotliste", msg):
            await x.delete()  #await (await channel.send(msg)).pin()

            liste = SlotList(msg, channel=channel)
            await liste.write()
            del liste
            break


@client.command(hidden = True, description="[User] Unslots an User")
@has_permissions(manage_channels = True)
async def forceUnslot(ctx):           # [Admin Function] unslots an user
    channel = ctx.message.channel

    player = ctx.message.content.split(" ")[1:]
    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Bitte einen User angeben!", delete_after=5)
        return

    seperator  = " "
    player = seperator.join(player)

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, message = x)

    if list.exit(player):
        await list.write()
        await channel.send(ctx.message.author.mention + " " + player +" wurde erfolgreich  ausgetragen!", delete_after=5)
        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " " + player + " ist nicht eingetragen!", delete_after=5)
        await ctx.message.delete()

    del list


@client.command(hidden = True, description="[Number] [User] Slots an User in a Slot")
@has_permissions(manage_channels = True)
@commands.cooldown(1,2, commands.BucketType.channel)
async def forceSlot(ctx):      # [Admin Function] slots an user
    channel = ctx.message.channel

    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Bitte Slot und Nutzer angeben!", delete_after=5)
        return


    num = argv[1]
    player = argv[2:]

    if not player:
        await ctx.message.delete()
        await channel.send(ctx.message.author.mention + " Bitte einen User angeben!", delete_after=5)
        return

    seperator = " "
    player = seperator.join(player)


    liste, x = await get_list(ctx, client)

    list = SlotList(liste, message = x)

    if (list.enter(player, num)):
        await list.write()
        del list
        await channel.send(ctx.message.author.mention + " Erfolgreich eingetragen!", delete_after=5)
        await ctx.message.delete()
    else:
        await channel.send(ctx.message.author.mention + " Der angegebene Slot ist ungültig oder schon belegt!", delete_after=5)
        await ctx.message.delete()

''' ---        --- '''



client.run(cfg['token'])