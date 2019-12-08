import re

from discord import Message
from math import ceil


def get_line_data(line):
    '''
    Extracts information from a line of a slotlist
    Args:
        line (string): line of a slotlist

    Returns:
       {num: {"player": playername, "descr": description}}

    '''
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
    '''
    Determines the number format
    Args:
        string: number

    Returns:
        (int) : number of leading zeros
    '''
    lenght = 0
    for x in string:
        if x == "0":
            lenght+=1
        else:
            break
    return lenght

def generator(begin, end):
    '''
    Generates a list of formated numbers
    Args:
        begin (string): First number
        end (string): Last number

    Returns:
        (list)

    '''

    b = int(begin)
    e = int(end)
    out = list(range(b, e+1))

    lenght = leading_zeros(begin)

    out = [str(x).rjust(lenght+1, "0") for x in out]

    return out


def get_key(input, player): #
    '''
    Gets a key for an value in dict
    Args:
        input (dict): Slotlist dictionary
        player (string):  Playername

    Returns:
        returns slotnumber
    '''
    for num, val in input.items():
        if val["player"] == player:
            return num

def get_free(slotlist):
    '''
    Takes the slot dictionary and returns the keys of the empty slots.
    Args:
        slotlist (dict):

    Returns:

    '''

    output = []
    for index, elem in slotlist.items():
        if elem["player"] == "" and elem["desc"] != "Reserve":
            output.append(index)

    return output

def get_group(list, group):
    '''
    Takes the struct list of the Slotlist and returns the index
    of the Group
    Args:
        list:
        group:

    Returns:

    '''
    for index, elem in enumerate(list, start=0):
        if elem["title"].replace("*", "").replace("__", "") == group:
            return index

    return None



async def get_list(ctx, client):
    '''
    Get Slotlist from Channel
    Args:
        ctx (command object): Command
        client (client object): Client

    Returns:
        (string), (message object): Slotliste, Message of the Slotlist
    '''
    channel = ctx.message.channel
    async for x in channel.history(limit=1000):
        msg = x.content
        if re.search("Slotliste", msg) and x.author == client.user:
            return msg, x

def get_member(guild, name):
    '''
    Gets a member of a list
    Args:
        guild (guild object): Guild
        name (string): Name of a user

    Returns:
        (member object)

    '''
    list = guild.members
    for member in list:
        if member.name == name or member.nick == name:
            return member
    raise None

async def get_channel_author(channel):
    '''
    Gets the author of the channel by checking the first message
    Args:
        channel (channel object): Channel

    Returns:
        (user object): Author
    '''
    x : Message
    async for x in channel.history(limit=10000):
        pass

    return x.author


def sort_dict(input):
    '''
    Sorts the Slotlist
    Args:
        input (dict):

    Returns:
        (dict): the sorted Slotlist
    '''
    output = {}
    for elem in sorted(input.keys()):
        output[elem] = input[elem]
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


    def enter(self, player, slot): #Slot Player
        '''

        Args:
            player (string): A Player-Name
            slot (string): A Slot-Number

        Returns:
            (boolean): True if successfull

        '''
        if not slot in self.slots.keys():
            return False

        elif self.slots[slot]["player"].replace(" ", "") == "":

            if player != "K.I.A." and  player in [x["player"] for x in list(self.slots.values())]:

                self.slots[get_key(self.slots, player)]["player"] = ""

            self.slots[slot]["player"] = player
        else:
            return False



        return True

    def exit(self, player):
        '''
        Unslots a given Player
        Args:
            player (string):

        Returns:
            (string):  the slotnumber of the player if successfull
            (bool): False else
        '''
        if player in [x["player"] for x in list(self.slots.values())]:
            index = get_key(self.slots, player)
            self.slots[index]["player"] = ""

            return index
        else:
            return False


    def edit(self, slot, desc):
        '''
        Edits the description of a given slot in the slotlist
        Args:
            slot (string): Slotnumber
            desc (string): Description

        Returns:
            (boolean): True if successfull
        '''
        if not slot in self.slots.keys() or self.slots[slot]["desc"] == "Reserve":
            return False

        else:
            self.slots[slot]["desc"] = desc
            return True

    def add(self, slot, group, desc):
        '''
        Adds a slot to the slotlist
        Args:
            slot (string): Slotnumber
            group (string): Group name or number to which the slot is been added
            desc (string): Description of slot

        Returns:
            (boolean): True if successfull
        '''
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
        '''
        Deletes a slot from the slotlist
        Args:
            slot (string): Slotnumber

        Returns:
            (boolean): True if successfull
        '''
        if not slot in self.slots.keys():
            return False

        else:
            self.slots.pop(slot)
            return True


    def group_add(self, begin, end, name = ""):
        '''
        Adds a group to the slotlist and adds all slot in the given range
        Args:
            begin (string): First slotnumber of the group
            end (string): Last slotnumber of the group
            name (string) [opt]: Displayed title of the group

        Returns:
            (boolean): True if successfull
        '''
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
        nearest = nearest.index(min(nearest))

        buffer = self.struct[nearest+1:]
        self.struct = self.struct[:nearest+1]

        self.struct.append({"title": name, "before": "\n", "begins": begin, "ends": end})
        self.struct += (buffer)



        for key in generator(begin, end):
            self.slots.update({key:{"desc": "", "player": ""}})

        self.slots = sort_dict(self.slots)
        return True

    def group_delete(self, name):
        '''
        Deletes a group from the list
        Args:
            name: Name or number of the group

        Returns:
            (boolean): True if successfull
        '''
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
        '''
        Writes or edits the Slotlist in the discord channel
        '''


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

