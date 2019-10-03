import os
import yaml

import re
from discord.ext.commands import Bot, has_permissions

from list import SlotList, get_list



''' --- onLoad ----'''
client = Bot("!")

#load conf
if os.path.isfile('./config.yml'):
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Please add config.yml to the dir")
    exit()

if not cfg["token"]:
    print("No valid token in config.yml")
    exit()

''' ---        ----'''

@client.command(pass_context = True)
@has_permissions(manage_channels = True)
async def create(ctx):                          #makes the slotlist editable for the bot
    channel = ctx.message.channel
    async for x in channel.history(limit=1000):
        msg = x.content
        if msg == "!create":
            await x.delete()
        elif re.search("Slotliste", msg):
            await x.delete()
            await (await channel.send(msg)).pin()

            break

@client.command(pass_context = True)
async def slot(ctx, num=""):                 #slots the author of the message in a slot
    channel = ctx.message.channel
    if num:

        liste, x = await get_list(ctx, client)

        list = SlotList(liste, x)

        if(list.enter(ctx.message.author.display_name, num)):
            await list.write()
            del list
            await channel.send("Erfolgreich eingetragen")
        else:
            await channel.send("Der angegebene Slot ist ungültig oder schon belegt")


    else:
        await channel.send("Für was willst du dich slotten?")

@client.command(pass_context = True)
async def unslot(ctx):                          #unslot the author auf the message
    channel = ctx.message.channel

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, x)

    if list.exit(ctx.message.author.display_name):
        await list.write()
        del list
        await channel.send("Erfolgreich ausgetragen")
    else:
        await channel.send("Du bist nicht eingetragen")

@client.command(pass_context = True)
@has_permissions(manage_channels = True)
async def forceUnslot(ctx):           # [Admin Function] unslots an user
    channel = ctx.message.channel

    player = ctx.message.content.split(" ")[1:]
    if not player:
        await channel.send("Bitte einen User angeben")
        return

    seperator  = " "
    player = seperator.join(player)

    liste, x = await get_list(ctx, client)
    list = SlotList(liste, x)

    if list.exit(player):
        await list.write()
        del list
        await channel.send("Erfolgreich ausgetragen")
    else:
        await channel.send("User ist nicht eingetragen")

@client.command(pass_context = True)
@has_permissions(manage_channels = True)
async def forceSlot(ctx):      # [Admin Function] slots an user
    channel = ctx.message.channel

    argv = ctx.message.content.split(" ")

    if not len(argv) >= 2:
        print("Bitte Slot und Nutzer angeben")
        return


    num = argv[1]
    player = argv[2:]

    if not player:
        await channel.send("Bitte einen User angeben")
        return

    seperator = " "
    player = seperator.join(player)


    liste, x = await get_list(ctx, client)

    list = SlotList(liste, x)

    if (list.enter(player, num)):
        await list.write()
        del list
        await channel.send("Erfolgreich eingetragen")
    else:
        await channel.send("Der angegebene Slot ist ungültig oder schon belegt")



client.run(cfg['token'])