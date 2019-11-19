import re

from discord import Message
from numpy import argmin

from math import ceil


def get_line_data(line):

    dict = {"desc": "", "player": ""}
    num = ""
    line = line.split("-")

    dict["player"] = line[-1].replace("**", "")
    line = "".join(line[:-1])

    count = 0

    for x in line[1:]:
        if (x.isdigit()):
            num += x
            count += 1
        else:
            break

    for x in line[count:]:
        if(x.isalpha() or x in " ()-"):
            dict["desc"] += x


    dict["desc"] = dict["desc"].strip()
    dict["player"] = dict["player"].strip()

    return {num: dict}

def leading_zeros(string):
    lenght = 0
    for x in string:
        if x == "0":
            lenght+=1
        else:
            break
    return lenght

def generator(begin, end):
    b = int(begin)
    e = int(end)
    out = list(range(b, e+1))

    lenght = leading_zeros(begin)

    out = [str(x).rjust(lenght+1, "0") for x in out]

    return out


def get_key(dict, player): #Get Key for an value in dict
    for num, val in dict.items():
        if val["player"] == player:
            return num

def get_free(dict):
    '''
    Takes the slot dictionary and returns the keys of the empty slots.
    :param dict:
    :return:
    '''
    output = []
    for index, elem in dict.items():
        if elem["player"] == "" and elem["desc"] != "Reserve":
            output.append(index)

    return output

def get_group(list, group):
    '''
    Takes the struct list of the Slotlist and returns the index
    of the Group
    :param list:
    :return index:
    '''
    for index, elem in enumerate(list, start=0):
        if elem["title"].replace("*", "").replace("__", "") == group:
            return index

    return None

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
    raise None

async def get_channel_author(channel):
    x : Message
    async for x in channel.history(limit=10000):
        pass

    return x.author


def sort_dict(dict):
    output = {}
    for elem in sorted(dict.keys()):
        output[elem] = dict[elem]
    return output

def sort_sup(item):
    return int(item["begins"])

class SlotList():

    def __init__(self, input, message = None, channel = None):

        self.slots = {}
        self.struct = []

        self.message = message
        self.channel = channel


        current = ""

        for line in input.splitlines(False):
            if "Slotliste" in line:
                pass
            elif line and line[0] == "#":
                data = get_line_data(line)
                if not self.struct or current:
                    self.struct.append({"title": "", "before": current, "begins": "", "ends": ""})
                    current = ""

                    if list(data.values())[0]["desc"].strip() == "Reserve":
                        self.struct[-1]["title"] = "**Reserve**"

                self.slots.update(data)

                if not self.struct[-1]["begins"]:
                    self.struct[-1]["begins"] = list(self.slots)[-1]

                self.struct[-1]["ends"] = list(self.slots)[-1]


            elif line.strip() == "":
                current += "\n"
            else:
                self.struct.append({"title": line.strip(), "before": current, "begins": "", "ends": ""})
                current = ""

        print(self.slots)
        print(self.struct)

    def enter(self, player, slot): #Slot Player
        if not slot in self.slots.keys():
            return False

        elif self.slots[slot]["player"].replace(" ", "") == "":

            if player != "K.I.A." and  player in [x["player"] for x in list(self.slots.values())]:

                self.slots[get_key(self.slots, player)]["player"] = ""

            self.slots[slot]["player"] = player
        else:
            return False



        return True

    def exit(self, player): #Unslot Player
        if player in [x["player"] for x in list(self.slots.values())]:
            self.slots[get_key(self.slots, player)]["player"] = ""

            return True
        else:
            return False


    def edit(self, slot, desc):
        if not slot in self.slots.keys() or self.slots[slot]["desc"] == "Reserve":
            return False

        else:
            self.slots[slot]["desc"] = desc
            return True

    def add(self, slot, group, desc):
        if slot in self.slots.keys():
            return False

        else:
            index = get_group(self.struct, group.replace("*", "").replace("__", ""))
            if not index:
                if group.isdigit() and self.struct[int(group)]:
                    index = int(group)
                else:
                    return False

            liste = generator(self.struct[index]["begins"], self.struct[index]["ends"])

            if not slot in liste:
                if int(slot) < int(self.struct[index]["begins"]):
                    self.struct[index]["begins"] = slot
                else:
                    self.struct[index]["ends"] = slot

            self.slots.update({slot:{"desc": desc, "player": ""}})
            self.slots = sort_dict(self.slots)


            return True

    def delete(self, slot):
        if not slot in self.slots.keys():
            return False

        else:
            self.slots.pop(slot)
            return True


    def group_add(self, begin, end, name = ""):
        if get_group(self.struct, name.replace("*", "").replace("_", "")) and name.strip():
            return False
        elif not begin.isdigit or not end.isdigit():
            return False

        for x in generator(begin, end):
            if x in list(self.slots):
                if self.slots[x]["desc"] == "Reserve":

                    reserve = get_group(self.struct, "Reserve")

                    lenght = len(self.struct[reserve]["ends"])
                    add = int(self.struct[reserve]["ends"]) - int(self.struct[reserve]["begins"])

                    b = str(ceil((int(end) + 1) / 10) * 10).rjust(lenght, "0")
                    e = str(ceil((int(end) + 1) / 10) * 10 + add).rjust(lenght, "0")

                    for x,y in zip(generator(b, e), generator(self.struct[reserve]["begins"], self.struct[reserve]["ends"])):
                        self.slots[x] = self.slots.pop(y)

                    self.struct[reserve]["begins"] = b
                    self.struct[reserve]["ends"] =e

                    break
                else:
                    return False

        liste = []
        for num, elem in enumerate(self.struct, start=0):
            if elem["ends"]:
                liste.append(elem["ends"])
            else:
                if num-1 >= 0:
                    liste.append(self.struct[num-1]["ends"])
                else:
                    liste.append("0")

        nearest = [abs(int(x) - int(begin)) for x in liste]
        nearest = argmin(nearest)

        buffer = self.struct[nearest+1:]
        self.struct = self.struct[:nearest+1]

        self.struct.append({"title": name, "before": "\n", "begins": begin, "ends": end})
        self.struct += (buffer)



        for key in generator(begin, end):
            self.slots.update({key:{"desc": "", "player": ""}})

        self.slots = sort_dict(self.slots)
        return True

    def group_delete(self, name):
        if not get_group(self.struct, name.replace("*", "").replace("_", "")) and name.strip():
            if name.isdigit() and int(name) < len(self.struct):
               index = int(name)
            else:
                return False
        else:
            index = get_group(self.struct, name.replace("*", "").replace("__", ""))

        for x in generator(self.struct[index]["begins"], self.struct[index]["begins"]):
            self.slots.pop(x)

        self.struct.pop(index)

        return True

    async def write(self): #Update List in Discord

        free = get_free(self.slots)
        reserve = get_group(self.struct, "Reserve")

        if reserve:
            reserve = self.struct[reserve]

        last = list(self.slots)[-1]
        lenght = len(last)

        # Add Reserve
        if not free and not reserve:

            add = int(len(self.slots) * 0.1)

            begin = str(ceil((int(last) + 1)/10)*10).rjust(lenght, "0")
            end = str(ceil((int(last) + 1)/10)*10 + add - 1).rjust(lenght, "0")


            for x in generator(begin, end):
                self.slots.update({x:{"desc": "Reserve", "player": ""}})


            if not self.struct[-1]["begins"]:
                buffer = self.struct.pop()
                self.struct.append({"title": "**Reserve**", "before": "\n", "begins": begin, "ends": end})
                self.struct.append(buffer)
            else:
                self.struct.append({"title": "**Reserve**", "before": "\n", "begins": begin, "ends": end})


        # Pull reserve into free slots
        elif free and reserve:

            for slot in free:
                key = ""
                for key in generator(reserve["begins"], reserve["ends"]):
                    if self.slots[key]["player"]:
                        self.enter(self.slots[key]["player"], slot)
                        break
                if key == reserve["ends"]:
                    break
        # Delete reserve
        if get_free(self.slots) and reserve:

            for key in generator(reserve["begins"], reserve["ends"]):
                try:
                    self.slots.pop(key)
                except:
                    pass

            self.struct.pop(get_group(self.struct, "Reserve"))
        # Sort reserve
        elif reserve:
            for key in generator(reserve["begins"], reserve["ends"]):
                if self.slots[key]["player"] == "":
                    num = ""
                    for num in generator(str(int(key) + 1).rjust(lenght, "0"), reserve["ends"]):
                        try:
                            if self.slots[num]["player"] != "":
                                self.enter(self.slots[num]["player"], key)
                                break
                        except:
                            pass

                    if num == reserve["ends"]:
                        break


        output = "**Slotliste**\n"



        for group in self.struct:
            output += group["before"]
            if group["title"]:
                output += group["title"] + "\n"
            try:
                for x in generator(group["begins"], group["ends"]):
                        try:
                            elem = self.slots[x]
                            if elem["player"] != "":
                                output += f"#{x} {elem['desc']} - **{elem['player']}**"
                            else:
                                output += f"#{x} {elem['desc']} - "
                            output += "\n"
                        except:
                            pass
            except:
                pass


        if(self.channel == None):
            await self.message.edit(content=output)
        else:
            await (await self.channel.send(output)).pin()

