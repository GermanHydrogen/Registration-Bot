import re

from discord import Message
from numpy import argmin

def get_number(input): #Get Slotnumber of a line
    num = ""
    for x in input:
        if (x.isdigit()):
            num += x
        else:
            break

    return num

def get_key(dict, value): #Get Key for an value in dict
    for num, player in dict.items():
        if player.replace(" ", "") == value.replace(" ", ""):
            return num


async def get_list(ctx, client): #Get Slotlist from Channel
    channel = ctx.message.channel
    async for x in channel.history(limit=1000):
        msg = x.content
        if re.search("Slotliste", msg) and x.author == client.user:
            return msg, x

def get_member(guild, name):
    list = guild.members
    for member in list:
        if member.name == name or member.nick == name:
            return member
    return None

async def get_channel_author(channel):
    x : Message
    async for x in channel.history(limit=10000):
        pass

    return x.author


class SlotList():

    data = {}
    msg = ""

    message = None
    channel = None

    def __init__(self, input, message = None, channel = None):

        self.message = message
        self.channel = channel
        self.msg = input


        for line in input.splitlines(False):
            if line and line[0] == "#":
                if line.split("-")[-1].replace(" ", "").replace("**", "") == "":
                    self.data[get_number(line[1:])] = " "
                else:
                    self.data[get_number(line[1:])] = line.split("-")[-1].replace("**", "")



    def enter(self, player, slot): #Slot Player

        if not slot in self.data.keys():
            return False

        elif self.data[slot].replace(" ", "") == "":

            if " " + player in self.data.values():
                self.data[get_key(self.data, player)] = " "

            self.data[slot] = " " + player
        else:
            return False



        return True

    def exit(self, player): #Unslot Player
        if " " + player in self.data.values():
            self.data[get_key(self.data, player)] = " "
            return True
        else:
            return False

    def add(self, slot, desc):
        if slot in self.data.keys():
            return False

        else:
            target = self.msg.splitlines(False)

            liste = list(self.data.keys())
            nearest = [abs(int(x)-int(slot)) for x in liste]

            nearest = argmin(nearest)
            nearest = (liste[nearest])
            print(nearest)


            for line, index in zip(target, range(len(target))):
                if line and line[0] == "#" and int(get_number(line[1:])) == int(nearest):

                    if len(line.split("-")) == 2:
                        spacer = " "
                    else:
                        spacer = "-"

                    if int(slot) - int(nearest) > 0:
                        target = target[:index+1] + [f"#{slot}{spacer}{desc} -** **"] + target[index+1:]
                    else:
                        target = target[:index] + [f"#{slot}{spacer}{desc} -** **"] + target[index:]


                    self.msg = "\n".join(target)

                    self.data[slot] = " "

                    return True

            target += [f"#{slot} {desc} -** **"]
            self.msg = "\n".join(target)


            self.data[slot] = " "

            return True

    def delete(self, slot):
        if not slot in self.data.keys():
            return False

        else:
            target = self.msg.splitlines(False)
            for line, index in zip(target, range(len(target))):
                if line and line[0] == "#" and get_number(line[1:]) == slot:
                    target.pop(index)
                    self.msg = "\n".join(target)
                    self.data.pop(slot)
                    return True

            return False


    async def write(self): #Update List in Discord
        output = ""
        for line in self.msg.splitlines(False):
            if line and line[0] == "#":
                for x in line.split("-")[:-1]:
                    output += x + "-"
                output += f"**{self.data[get_number(line[1:])]}**\n"
            else:
                output += line + "\n"

        if(self.channel == None):
            await self.message.edit(content=output)
        else:
            await (await self.channel.send(output)).pin()

