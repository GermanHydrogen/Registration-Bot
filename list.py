import re

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
        if re.search("Slotliste", msg) and x.author == client.user: #TODO: Token in conf machen
            return msg, x



class SlotList():

    data = {}
    msg = ""

    list = ""

    def __init__(self, input, list):

        self.list = list
        self.msg = input


        for line in input.splitlines(False):
            if line and line[0] == "#":
                if line.split("-")[-1].replace(" ", "") == "":
                    self.data[get_number(line[1:])] = " "
                else:
                    self.data[get_number(line[1:])] = line.split("-")[-1]


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

    async def write(self): #Update List in Discord
        output = ""
        for line in self.msg.splitlines(False):
            if line and line[0] == "#":
                for x in line.split("-")[:-1]:
                    output += x + "-"
                output += self.data[get_number(line[1:])] + "\n"
            else:
                output += line + "\n"

        await self.list.edit(content=output)

