import re

from discord import *

from math import ceil

import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Zaubertrick.-98",
    database="testDB"
)
mycursor = mydb.cursor()

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

def get_line_data(line):
    '''
    Extracts information from a line of a slotlist
    Args:
        line (string): line of a slotlist

    Returns:
       {num: {"player": playername, "descr": description}}

    '''
    dict = {"Description": "", "User": ""}
    num = ""
    line = line.split("-")

    dict["User"] = line[-1].replace("**", "")
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
            dict["Description"] += x


    dict["Description"] = dict["Description"].strip()
    dict["User"] = dict["User"].strip()

    return {num: dict}

def get_members(name, channel):
    '''
    Gets a member of a list
    Args:
        guild (guild object): Guild
        name (string): Name of a user

    Returns:
        (member object)

    '''
    list = channel.guild.members
    for member in list:
        if member.name == name or member.nick == name:
            return member
    return None

def get_user_id(nname, channel):
    sql = "SElECT ID FROM User WHERE Nickname = %s"
    var = [nname]

    mycursor.execute(sql, var)
    result = mycursor.fetchall()

    if result:
        return result[0][0]
    else:
        nname = get_members(nname, channel)
        if not nname:
            return None

        sql = f"INSERT INTO User VALUES (%s, %s)"
        var = [nname.id, nname.display_name]
        mycursor.execute(sql, var)

        return nname.id


def get_channel_author(channel):
    sql = f"SELECT User FROM Author WHERE Event = {channel.id}"
    mycursor.execute(sql)

    return channel.guild.get_member(int(mycursor.fetchone()[0]))


def createEvent(input, msg): #TODO Player ID

    channel = msg.channel
    split = channel.name.split("-")
    if not (len(split) == 4 and len(split[0]) == 4 and len(split[1]) == 2 and len(split[2]) == 2 and split[3]):
        return False

    date = "-".join(split[:3])
    name = split[-1]
    event = channel.id

    sql = f"SELECT ID FROM Event WHERE ID = {event}"
    mycursor.execute(sql)
    
    if mycursor.fetchall():
        sql = f"DELETE FROM Slot WHERE Event = {event}"
        mycursor.execute(sql)

        sql = f"DELETE FROM SlotGroup WHERE Event = {event}"
        mycursor.execute(sql)

        mydb.commit()
    else:
        sql = "INSERT INTO Event (ID, Name, Date, Type) VALUES (%s, %s, %s, %s)"
        var = [event, channel.name, date, name]
        mycursor.execute(sql, var)

        mydb.commit()

        sql = "INSERT INTO Author VALUES (%s, %s)"
        var = [event, msg.author.id]

        mycursor.execute(sql, var)
        mydb.commit()

    slots = {}
    struct = []

    current_buffer = ""

    for line in input.splitlines(False):
        if "Slotliste" in line:
            pass
        elif line and line[0] == "#":
            data = get_line_data(line)
            if not struct or current_buffer:
                struct.append({"Name": "", "Struct": current_buffer})
                current_buffer = ""

                if list(data.values())[0]["Description"].strip() == "Reserve":
                    struct[-1]["Name"] = "**Reserve**"

            data[list(data)[0]]["GroupNum"] = len(struct) -1
            if data[list(data)[0]]["User"]:
                data[list(data)[0]]["User"] = get_user_id(data[list(data)[0]]["User"], channel)
            else:
                data[list(data)[0]]["User"] = None

            slots.update(data)


        elif line.strip() == "":
            current_buffer += "\n"
        else:
            struct.append({"Name": line.strip(), "Struct": current_buffer})
            current_buffer = ""

    sql = "INSERT INTO SlotGroup VALUES (%s, %s, %s, %s)"
    var = [(num, event, elem["Name"],elem["Struct"]) for num, elem in enumerate(struct, start=0)]

    mycursor.executemany(sql, var)
    mydb.commit()

    sql = "INSERT INTO Slot VALUES (%s, %s, %s, %s, %s)"
    var = [(event, index, elem["Description"], elem["GroupNum"], elem["User"]) for index, elem in slots.items()]
    mycursor.executemany(sql, var)
    mydb.commit()

    return True

def slotEvent(channel, user, num):

    sql = f"SELECT User FROM Slot WHERE Event = {channel.id} and Number = {num}"
    mycursor.execute(sql)
    slot = mycursor.fetchone()

    if slot[0]:
        return False

    sql = f"SELECT ID, Nickname FROM User WHERE ID = {user.id}"
    mycursor.execute(sql)
    data = mycursor.fetchone()

    if not data:
        sql = f"INSERT INTO User VALUES ({user.id}, {user.display_name})"
        mycursor.execute(sql)
        mydb.commit()
    elif data[1] != user.display_name:
        sql = f"UPDATE User SET Nickname='{user.display_name}' WHERE ID = {user.id}"
        mycursor.execute(sql)
        mydb.commit()

    sql = f"UPDATE Slot SET User = NULL WHERE User = {user.id} and Event = {channel.id}"
    mycursor.execute(sql)
    mydb.commit()

    sql = f"UPDATE Slot SET User = {user.id} WHERE Number = {num} and Event = {channel.id}"
    mycursor.execute(sql)
    mydb.commit()

    return True

def unslotEvent(channel, user_id):

    sql = f"UPDATE Slot SET User = NULL WHERE User = {user_id} and Event = {channel.id}"
    mycursor.execute(sql)
    mydb.commit()

    return (mycursor.rowcount != 0)

def addSlot(channel, slot, group, desc):
    sql = f"SELECT Number FROM Slot WHERE Event = {channel.id}"
    mycursor.execute(sql)
    if mycursor.fetchone():
        return False

    sql = "INSERT INTO Slot (Event, Number, Description, GroupNum) VALUES (%s, %s, %s, %s)"
    var = [channel.id, slot, desc]


async def writeEvent(channel):

    id = channel.id

    sql = "SELECT Number, Name, Struct FROM SlotGroup WHERE Event = %s"
    var = [id]
    mycursor.execute(sql, var)
    group = mycursor.fetchall()


    output = "**Slotliste**\n"
    for element in group:
        output += element[2]
        if element[1] or element[1] != "":
            output += element[2] + "\n"


        sql = "SELECT " \
              "Number , Description, User FROM Slot " \
              "WHERE Event = %s and GroupNum = %s ORDER BY CONVERT(Number,UNSIGNED INTEGER) ASC"
        var = [id, element[0]]
        mycursor.execute(sql, var)
        slots = mycursor.fetchall()

        for x in slots:
            if x[2] != None:

                user = channel.guild.get_member(int(x[2]))
                output += f"#{x[0]} {x[1]} - **{user.display_name}**"
            else:
                output += f"#{x[0]} {x[1]} - "
            output += "\n"

    sql = "SELECT MSG_ID FROM Event WHERE ID = %s"
    var = [id]
    mycursor.execute(sql, var)
    msg = mycursor.fetchone()

    if msg[0]:

        try:
            msg = await channel.fetch_message(msg[0])
        except:
            msg = await channel.send(output)

            sql = "UPDATE Event SET MSG_ID = %s where ID = %s"
            var = [msg.id, channel.id]
            mycursor.execute(sql, var)
            mydb.commit()


        await msg.edit(content=output)

        pass
    else:
        new_msg = await channel.send(output)


        sql = "UPDATE Event SET MSG_ID = %s where ID = %s"
        var = [str(new_msg.id), str(channel.id)]
        mycursor.execute(sql, var)

        mydb.commit()

