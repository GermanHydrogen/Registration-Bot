import re
import os
import yaml

import discord

from math import ceil

import mysql.connector

path = os.path.dirname(os.path.abspath(__file__))

# load conf
try:
    with open(path + "/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    mydb = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        passwd=cfg["passwd"],
        database=cfg["database"]
    )

    mycursor = mydb.cursor(buffered=True)
except:
    exit()


async def get_list(ctx, client):
    """
    Get Slotlist from Channel
    Args:
        ctx (command object): Command
        client (client object): Client

    Returns:
        (string), (message object): Slotliste, Message of the Slotlist
    """
    channel = ctx.message.channel
    async for x in channel.history(limit=1000):
        msg = x.content
        if re.search("Slotliste", msg) and x.author == client.user:
            return msg, x


def get_line_data(line):
    """
    Extracts information from a line of a slotlist
    Args:
        line (string): line of a slotlist

    Returns:
       {num: {"User": playername, "Description": description}}

    """
    output = {"Description": "", "User": ""}
    num = ""
    line = line.replace("**", "").split("-")

    output["User"] = "-".join(line[1:]).replace("**", "")
    line = line[0]

    for x in line[1:]:
        if x.isdigit():
            num += x
        else:
            break

    output["Description"] = line[len(num)+1:].strip()

    output["User"] = output["User"].strip()

    return {num: output}


def get_members(name, channel):
    """
    Gets a member of a list
    Args:
        name (string): Name of a user
        channel (discord.TextChannel): channel

    Returns:
        (discord.Member)

    """
    guild_member = channel.guild.members
    for member in guild_member:
        if member.name == name or member.nick == name:
            return member
    return None


def get_user_id(nname, channel):
    """
        Gets an user id
        Args:
            nname (string): Nickname of a user
            channel (channel): Channel

        Returns:
            (int)

    """

    sql = "SElECT ID FROM User WHERE Nickname = %s;"
    mycursor.execute(sql, [nname])
    result = mycursor.fetchall()

    if result:
        return result[0][0]
    else:
        nname = get_members(nname, channel)
        if not nname:
            return None

        sql = f"INSERT IGNORE INTO User VALUES (%s, %s);"
        var = [nname.id, nname.display_name]
        mycursor.execute(sql, var)
        mydb.commit()

        return nname.id


def get_channel_author(channel):
    """
        Gets the author of the channel
        Args:
            channel (channel): Server Channel

        Returns:
            (member object)

    """
    sql = "SELECT Author FROM Event WHERE ID = %s;"
    mycursor.execute(sql, [channel.id])

    result = mycursor.fetchone()

    if result:
        return channel.guild.get_member(int(result[0]))
    else:
        return None


def get_event_id(name):
    """
            Gets the id of an event
            Args:
                name (string): Eventname (e.g. 2020-02-13-arma3)

            Returns:
                (string): id

       """

    sql = "SELECT ID FROM Event WHERE Name = %s;"
    mycursor.execute(sql, [str(name)])
    result = mycursor.fetchone()

    if result:
        return result[0]
    else:
        return None


def get_event_date(channel_id):
    """
            Gets the date of an event
            Args:
                channel_id (string): Server Channel

            Returns:
                (string): date

    """

    sql = "SELECT Date FROM Event WHERE ID = %s;"
    mycursor.execute(sql, [str(channel_id)])
    result = mycursor.fetchone()
    if result:
        return result[0]
    else:
        return None


def get_slots(channel_id):
    """
            Gets all taken slots of the channel
            Args:
                channel_id (string): Server Channel

            Returns:
                (list): [(user, slot-number, description)]

       """
    sql = "SELECT User, Number, Description FROM Slot WHERE Event = %s AND Description != %s AND User IS NOT NULL;"
    mycursor.execute(sql, [str(channel_id), 'Reserve'])

    return mycursor.fetchall()


def pull_reserve(event_id):
    """
        Pulls users from reserve into open slots
        Args:
            event_id (string): Event ID

        Returns:
            (bool): if free slots exist

    """
    sql = "SELECT Number FROM Slot " \
          "WHERE Event = %s AND User IS NULL AND Description != 'Reserve';"

    mycursor.execute(sql, [event_id])
    free = mycursor.fetchall()

    sql = "SELECT Number, User FROM Slot " \
          "WHERE Event = %s and User IS NOT NULL AND Description = 'Reserve' " \
          "ORDER BY CONVERT(Number, UNSIGNED INTEGER);"

    mycursor.execute(sql, [event_id])
    reserve = mycursor.fetchall()

    if free and reserve:
        for index, elem in enumerate(free, start=0):

            if index == len(reserve):
                return True

            sql = "UPDATE Slot SET User= NULL WHERE Event= %s and Number = %s;"
            var = [event_id, reserve[index][0]]
            mycursor.execute(sql, var)
            mydb.commit()

            sql = "UPDATE Slot SET User= %s WHERE Event= %s and Number = %s;"
            var = [reserve[index][1], event_id, elem[0]]
            mycursor.execute(sql, var)
            mydb.commit()

        return False
    elif free:
        return True
    else:
        return False


def sort_reserve(channel):
    """
        Sorts the reserve slots, so its filled from bottom up
        Args:
            channel (discord.TextChannel): Server channel

        Returns:
            (bool): if successful

    """
    sql = "SELECT Number, User FROM Slot WHERE Event = %s and Description = 'Reserve' ORDER BY Number"
    mycursor.execute(sql, [channel.id])
    reserve = mycursor.fetchall()

    count = 0

    for x, y in reserve:
        if not y:
            continue
        else:
            sql = "UPDATE Slot SET User = NULL WHERE User = %s AND Event = %s;"
            mycursor.execute(sql, [y, channel.id])
            mydb.commit()

            sql = "UPDATE Slot SET User = %s WHERE Number = %s AND Event = %s;"
            var = [y, reserve[count][0], channel.id]
            mycursor.execute(sql, var)
            mydb.commit()

            count += 1


def createEvent(msg_list, author, bot=None):
    """
           Creates an event in the database
           Args:
               msg_list (list of msg object): The message containing the slotlist
               author (user object): Author of the slotlist
               bot (user object): Used Bot user (optional)

           Returns:
               (bool): if successful

    """

    channel = msg_list[0].channel
    split = channel.name.split("-")
    if not (len(split) == 4 and len(split[0]) == 4 and len(split[1]) == 2 and len(split[2]) == 2 and split[3]):
        return False

    date = "-".join(split[:3])
    name = split[-1]
    event = channel.id

    sql = "SELECT ID FROM Event WHERE ID = %s;"
    mycursor.execute(sql, [event])

    if mycursor.fetchall():
        sql = "DELETE FROM Slot WHERE Event = %s;"
        mycursor.execute(sql, [event])
        mydb.commit()

        sql = f"DELETE FROM SlotGroup WHERE Event = %s;"
        mycursor.execute(sql, [event])

        mydb.commit()
    else:
        # Check if Author User exists
        sql = "SELECT ID FROM User WHERE ID = %s;"
        mycursor.execute(sql, [author.id])

        if not mycursor.fetchall():
            sql = "INSERT INTO User VALUES (%s, %s);"
            var = [author.id, author.display_name]
            mycursor.execute(sql, var)
            mydb.commit()

        sql = "INSERT INTO Event (ID, Name, Author, Date, Type) VALUES (%s, %s, %s, %s, %s);"
        var = [event, channel.name, author.id, date, name]
        mycursor.execute(sql, var)

        mydb.commit()

    sql = "SELECT Number, MsgID FROM EventMessage WHERE Event = %s ORDER BY Number;"
    mycursor.execute(sql, [channel.id])

    messages = mycursor.fetchall()

    if False not in [msg.author == bot for msg in msg_list]:

        for index, elem in enumerate(messages, start=1):
            if index <= len(msg_list):

                sql = "UPDATE EventMessage SET MsgID = %s WHERE Event = %s AND Number = %s;"
                var = [msg_list[-index].id, channel.id, elem[0]]

                mycursor.execute(sql, var)
                mydb.commit()
            else:
                sql = "DELETE FROM EventMessage WHERE Number = %s"
                var = [elem[0]]
                mycursor.execute(sql, var)
                mydb.commit()
    else:
        sql = "DELETE FROM EventMessage WHERE Event = %s"
        var = [channel.id]
        mycursor.execute(sql, var)
        mydb.commit()

    content = "\n".join([x.content for x in msg_list[::-1]])

    slots = {}
    struct = []

    current_buffer = ""

    reserve = False

    for line in content.splitlines(False):
        if "Slotliste" in line:
            pass
        elif line and line[0] == "#":
            data = get_line_data(line)
            print(data)

            if not struct or current_buffer:
                struct.append({"Name": "", "Struct": current_buffer, "Length": len(current_buffer)})
                current_buffer = ""

                if list(data.values())[0]["Description"].strip().replace("**", "") == "Reserve" and \
                        struct[-1]["Name"].strip().replace("**", "") != "Reserve":

                    struct[-1]["Name"] = "**Reserve**"
                    struct[-1]["Length"] = len(struct[-1]["Struct"]) + len("**Reserve**")

                    reserve = True

            data[list(data)[0]]["GroupNum"] = len(struct) - 1

            struct[-1]["Length"] += len((list(data)[0])) + len(data[list(data)[0]]["Description"]) + 5

            if data[list(data)[0]]["User"]:
                struct[-1]["Length"] += len(data[list(data)[0]]["User"]) + 1
                data[list(data)[0]]["User"] = get_user_id(data[list(data)[0]]["User"], channel)

            else:
                data[list(data)[0]]["User"] = None
                struct[-1]["Length"] += 10   # Average lenght of a Discord Nickname + white space

            slots.update(data)

        elif line.strip() == "":
            current_buffer += "\n"
        else:
            if line.strip().replace("**", "") == "Reserve":
                reserve = True

            lenght = len(current_buffer) + len(line.strip()) + 1
            struct.append({"Name": line.strip(), "Struct": current_buffer, "Length": lenght})
            current_buffer = ""

    for a, b, c, d, e in [(num, event, elem["Name"], elem["Struct"], elem["Length"]) for num, elem in enumerate(struct, start=0)]:

        sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, %s, %s);"
        var = [a, b, c, d, e]

        mycursor.execute(sql, var)
        mydb.commit()

    sql = "INSERT INTO Slot VALUES (%s, %s, %s, %s, %s)"
    var = [(event, index, elem["Description"], elem["User"], elem["GroupNum"]) for index, elem in
           slots.items()]
    mycursor.executemany(sql, var)
    mydb.commit()

    if not reserve:
        lenght = int(len(list(slots)) * cfg["res_ratio"]) + 1
        begin = ceil((int(list(slots)[-1]) + 1) / 10) * 10
        msg_format = len(list(slots)[-1]) - 1

        groupNum = len(struct)
        sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, %s, %s);"
        var = [groupNum, channel.id, "Reserve", '\n', lenght*(9+14+len(str(groupNum)))+12]

        mycursor.execute(sql, var)
        mydb.commit()

        sql = "INSERT INTO Slot (Event, Number, Description, GroupNumber) VALUES (%s, %s, %s, %s);"
        var = [(channel.id, str(index).rjust(msg_format, "0"), "Reserve", groupNum) for index in
               range(begin, begin + lenght)]

        mycursor.executemany(sql, var)
        mydb.commit()

    return True


async def writeEvent(channel, manage = False, new = False):
    """
           Outputs the slotlist to a given channel
           Args:
               channel (channel): Server channel
               manage (bool): manage the distrebution of slotgroups to msg? (optional)
               new (bool): if its possible to add new msgs (optional)

           Returns:
               (bool): if successful

       """

    channel_id = channel.id

    free = pull_reserve(channel_id)
    sort_reserve(channel)

    if manage:
        sql = "SELECT Number, Length FROM SlotGroup WHERE Event = %s ORDER BY Number;"
        mycursor.execute(sql, [channel_id])
        group = mycursor.fetchall()

        total = sum([x[1] for x in group])

        sql = "SELECT Number FROM EventMessage WHERE Event = %s;"
        mycursor.execute(sql, [channel_id])

        ids = mycursor.fetchall()

        if not ids or new:
            number = int((total+400)/2000)+1
            limit = int(total/number)

            ids = []

            for x in range(0,number):
                sql = "INSERT INTO EventMessage (Event) VALUES (%s);"
                mycursor.execute(sql, [channel_id])
                mydb.commit()

                ids.append((mycursor.lastrowid,))

        else:

            number = len(ids)
            limit = int(total/number)

        times_limit = 1
        buffer = 0
        last_split = 0

        output = [[]]

        for index, elem in enumerate(group, start=0):
            buffer += elem[1]

            if buffer > limit * times_limit:

                sql = "UPDATE SlotGroup SET Msg = %s WHERE Event = %s AND Number = %s;"
                var = [(ids[times_limit-1][0], channel_id, x[0]) for x in group[last_split:index]]

                mycursor.executemany(sql, var)
                mydb.commit()

                last_split = index
                times_limit += 1
                output.append([])

            if times_limit >= number:
                break

        sql = "UPDATE SlotGroup SET Msg = %s WHERE Event = %s AND Number = %s;"
        var = [(ids[times_limit - 1][0], channel_id, x[0]) for x in group[last_split:]]

        mycursor.executemany(sql, var)
        mydb.commit()

    sql = "SELECT Number, MsgID FROM EventMessage WHERE Event = %s ORDER BY Number;"
    mycursor.execute(sql, [channel_id])
    msgs = mycursor.fetchall()

    output = "**Slotliste**\n"
    for msg_id in msgs:
        sql = "SELECT Number, Name, Struct, Length FROM SlotGroup WHERE Event = %s AND Msg = %s ORDER BY Number;"
        mycursor.execute(sql, [channel_id, msg_id[0]])
        group = mycursor.fetchall()

        for element in group:
            if element[1]:
                if element[1] == "Reserve" and free:
                    continue

                if element[1] != "":

                    if '\n' in element[2] and element[0] == group[0][0]:
                        output += '\u200B\n'
                    else:
                        output += element[2]

                    output += f"{element[1]}" + "\n"
            else:

                if '\n' in element[2] and element[0] == group[0][0]:
                    output += '\u200B\n'
                else:
                    output += element[2]

            sql = "SELECT " \
                  "Number , Description, User FROM Slot " \
                  "WHERE Event = %s and GroupNumber = %s ORDER BY CONVERT(Number,UNSIGNED INTEGER);"
            var = [channel_id, element[0]]
            mycursor.execute(sql, var)
            slots = mycursor.fetchall()
            for x in slots:
                if x[2] is not None:

                    sql = "SELECT Nickname FROM User WHERE ID = %s;"
                    mycursor.execute(sql, [x[2]])
                    user = mycursor.fetchone()[0]

                    output += f"#{x[0]} {x[1]} - {user}"
                else:
                    output += f"#**{x[0]} {x[1]}** - "
                output += "\n"

        if msg_id[1] is not None:

            try:
                msg = await channel.fetch_message(msg_id[1])
                await msg.edit(content=output)
            except:
                msg = await channel.send(output)

                sql = "UPDATE EventMessage SET MsgID = %s WHERE Number = %s;"
                var = [msg.id, msg_id[0]]
                mycursor.execute(sql, var)
                mydb.commit()

        else:
            new_msg = await channel.send(output)

            sql = "UPDATE EventMessage SET MsgID = %s WHERE Number = %s;"
            var = [new_msg.id, msg_id[0]]
            mycursor.execute(sql, var)

            mydb.commit()

        output = ""


def reserveSlots(query):
    """
            Creates Requests to Users for paticipating again
            Args:
                query (list): List containing event-id, user-id, slotnumber, message-id, and date
            Returns:
                (bool): if successful
    """

    try:
        sql = "INSERT INTO Message (Event, User, SlotNumber, MessageID, DateUntil) VALUES (%s, %s, %s, %s, %s);"
        mycursor.executemany(sql, query)
        mydb.commit()
    except:
        return False

    # Blocks all reserved slots
    try:
        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        var = [('C00000000000000000', x[0], x[2]) for x in query]
        mycursor.executemany(sql, var)
        mydb.commit()
    except:
        return False

    return True


def acceptMessage(msg_id):
    """
        Accept a request
            Args:
                msg_id (string): Message ID
            Returns:
                (string): Type of Message (campaign/trade)
                (list): result of acceptance
    """

    sql = "SELECT * FROM Message WHERE MessageID = %s;"
    mycursor.execute(sql, [str(msg_id)])
    result = mycursor.fetchone()
    if not result:
        return None
    if result[2] is None:
        return "campaign", acceptReservation(msg_id, result[0], result[1], result[3])
    else:
        return "trade", acceptSwap(msg_id, result[0], result[1], result[2])


def acceptReservation(msg_id, event, user, slotnumber):
    """
            Accept a Reservation
            Args:
                msg_id (string): ID of the reservation message
                event(string): ID of an event
                user(string): ID of an user
                slotnumber(string): Number of a slot

            Returns:
                (string): channel if successfull channel_id, when not None
    """

    sql = "DELETE FROM Message WHERE MessageID = %s;"
    mycursor.execute(sql, [str(msg_id)])
    mydb.commit()

    sql = "UPDATE Slot SET User = %s WHERE Event = %s AND User = %s"
    var = [None, user, event]
    mycursor.execute(sql, var)
    mydb.commit()

    sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
    mycursor.execute(sql, [user, event, slotnumber])
    mydb.commit()

    return event


def acceptSwap(msg_id, event, req_user, rec_user):
    """
        Accept a Reservation
            Args:
                msg_id (string): ID of the reservation message
                event(string): ID of an event
                req_user(string): ID of a requester
                rec_user(string): Number of a recipient

            Returns:
                (list): if successfull event, req_user, rec_user, when not None
    """

    sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
    val = [event, req_user]
    mycursor.execute(sql, val)
    slot_1 = mycursor.fetchone()

    sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
    val = [event, rec_user]
    mycursor.execute(sql, val)
    slot_2 = mycursor.fetchone()

    sql = "DELETE FROM Message WHERE MessageID = %s;"
    mycursor.execute(sql, [msg_id])
    mydb.commit()

    if not slot_1:
        return req_user
    if not slot_2:
        return rec_user

    sql = "UPDATE Slot SET User = Null WHERE Number = %s AND Event = %s;"
    mycursor.execute(sql, [slot_1[0], event])
    mydb.commit()

    sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
    val = [(req_user, event, slot_2[0]), (rec_user, event, slot_1[0])]
    mycursor.executemany(sql, val)
    mydb.commit()

    return [event, req_user, rec_user]


def denyMessage(msg_id):
    """
        Deny a request
            Args:
                msg_id (string): Message ID
            Returns:
                (string): Type of Message (campaign/trade)
                (list): result of deny
    """
    sql = "SELECT * FROM Message WHERE MessageID = %s;"
    mycursor.execute(sql, [str(msg_id)])
    result = mycursor.fetchone()

    if not result:
        return None
    if result[2] is None:
        return "campaign", denyReservation(msg_id, result[0], result[3])
    else:
        return "trade", denySwap(msg_id, result[0], result[1], result[2])


def denyReservation(msg_id, event, slotnumber):
    """
            Deny a Reservation
            Args:
                msg_id (string): ID of the reservation message
                event (string): ID of an event
                slotnumber (string): Slotnumber with possible leading zeros
            Returns:
                (string): channel if successfull channel_id, when not None
    """

    sql = "DELETE FROM Message WHERE MessageID = %s;"
    mycursor.execute(sql, [str(msg_id)])
    mydb.commit()

    sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
    var = [None, event, slotnumber]
    mycursor.execute(sql, var)
    mydb.commit()

    return event


def denySwap(msg_id, event, req_user, rec_user):
    """
           Deny a Reservation
               Args:
                   msg_id (string): ID of the reservation message
                   event(string): ID of an event
                   req_user(string): ID of a requester
                   rec_user(string): Number of a recipient

               Returns:
                   (list): if successfull event, req_user, rec_user, when not None
       """

    sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
    val = [event, req_user]
    mycursor.execute(sql, val)
    slot_1 = mycursor.fetchone()

    sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
    val = [event, rec_user]
    mycursor.execute(sql, val)
    slot_2 = mycursor.fetchone()

    sql = "DELETE FROM Message WHERE MessageID = %s;"
    mycursor.execute(sql, [msg_id])
    mydb.commit()

    if not slot_1:
        return req_user
    if not slot_2:
        return rec_user

    return event, req_user, rec_user


def cleanupMessage(date):
    """
        Deletes all timeouted messages
            Args:
                date (date): given date
            Returns:
                (list): list of effected channel ids's (campaign)
                (list): list of effected users (campaign)
                (list): list of effected event id, user, recUser, msgID (trade)
    """

    sql = "SELECT Event, User, SlotNumber, MessageID FROM Message " \
          "WHERE (DATEDIFF(DateUntil, %s) < 0) AND RecUser is NULL;"
    mycursor.execute(sql, [str(date)])
    slots = mycursor.fetchall()

    if slots:
        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        var = [(None, x[0], x[2]) for x in slots]
        mycursor.executemany(sql, var)
        mydb.commit()

    channels = list(dict.fromkeys([x[0] for x in slots]))
    campUsers = [(x[1], x[3]) for x in slots]

    sql = "SELECT Event, User, RecUser, MessageID FROM Message " \
          "WHERE (DATEDIFF(DateUntil, %s) < 0) AND RecUser is not Null;"
    mycursor.execute(sql, [str(date)])
    result = mycursor.fetchall()

    sql = "DELETE FROM Message WHERE (DATEDIFF(DateUntil, %s) < 0);"
    mycursor.execute(sql, [str(date)])
    mydb.commit()

    return [[channels, campUsers], result]


def slotEvent(channel, user_id, num, user_displayname=None, force=False):
    """
           Slots a given user in the given slot
           Args:
                channel (channel): Server channel
                user_id (int): User ID
                num (string): Number of the slot
                user_displayname (string): User nickname (optional)
                force (bool): If true, accept duplicates (optional)

           Returns:
               (bool): if successful

    """

    sql = "SELECT User FROM Slot WHERE Event = %s and Number = %s;"
    var = [channel.id, num]
    mycursor.execute(sql, var)
    slot = mycursor.fetchone()

    if slot is None or slot[0] is not None:
        return False

    sql = "SELECT ID, Nickname FROM User WHERE ID = %s;"
    mycursor.execute(sql, [user_id])
    result = mycursor.fetchone()

    if (not force) and (result is None):
        sql = "INSERT INTO User VALUES (%s, %s);"
        var = [str(user_id), user_displayname]
        mycursor.execute(sql, var)
        mydb.commit()
    elif not force and (result is not None) and result[1] != user_displayname:
        sql = "UPDATE User SET Nickname= %s WHERE ID = %s;"
        var = [str(user_displayname), str(user_id)]
        mycursor.execute(sql, var)
        mydb.commit()

    if not force:
        sql = "UPDATE Slot SET User = NULL WHERE STRCMP(User, %s) = 0 AND Event = %s;"
        var = [str(user_id), str(channel.id)]
        mycursor.execute(sql, var)
        mydb.commit()

    try:
        sql = "UPDATE Slot SET User = %s WHERE Number = %s and Event = %s;"
        var = [user_id, num, channel.id]
        mycursor.execute(sql, var)
        mydb.commit()

    except mysql.connector.errors.DatabaseError:
        return False

    return True


def unslotEvent(channel, user_id):
    """
            Unslots a user from an Event
            Args:
                channel (channel): Server channel
                user_id (string): User ID

           Returns:
               (bool): if successful

       """

    sql = "SELECT Number FROM Slot WHERE STRCMP(User, %s) = 0 and Event = %s;"
    var = [user_id, channel.id]
    mycursor.execute(sql, var)

    result = mycursor.fetchone()

    if result:

        sql = "UPDATE Slot SET User = NULL WHERE STRCMP(User, %s) = 0 and Event = %s;"
        var = [user_id, channel.id]
        mycursor.execute(sql, var)
        mydb.commit()

        return result[0]
    else:
        return False


def validateSwap(event, req_user, rec_user):
    """
        Validate a swap message
            Args:
                event (string): Event ID
                req_user (string): User ID of the requester
                rec_user (string): User ID of the recipient
            Returns:
                (int): Status (1: valid, 2: exceeds limit, 0: not in the list)
    """

    if not rec_user.isdigit():
        return 0

    sql = "SELECT COUNT(*) FROM Message WHERE Event = %s AND User = %s GROUP BY User;"
    val = [event, req_user]
    mycursor.execute(sql, val)

    if mycursor.fetchone() is not None:
        return 2

    sql = "SELECT User FROM Slot WHERE Event = %s AND Description != %s;"
    mycursor.execute(sql, [event, 'Reserve'])
    result = mycursor.fetchall()

    if not ((str(req_user),) in result and (str(rec_user),) in result):
        return 0

    return 1


def createSwap(event, req_user, rec_user, msg_id, date):
    """
        Creates a swap request
            Args:
                event (string): Event ID
                req_user (string): User ID of the requester
                rec_user (string): User ID of the recipient
                msg_id (string): Message ID of the request
                date (date): Date until the request is due
            Returns:

    """

    sql = "INSERT INTO Message (Event, User, RecUser, MessageID, DateUntil) VALUES (%s, %s, %s, %s, %s);"
    val = [event, req_user, rec_user, msg_id, date]
    mycursor.execute(sql, val)
    mydb.commit()


def addSlot(channel, slot, group, desc):
    """
           Adds a slot to a given event
           Args:
                channel (channel): Server channel
                slot (int): Slot-Number
                group (string): Group-Number (counting form 0) or Group-Name
                desc (string): Name

           Returns:
               (bool): if successful

       """

    sql = "SELECT Description FROM Slot WHERE Event = %s and Number = %s;"
    var = [channel.id, slot]
    mycursor.execute(sql, var)

    result = mycursor.fetchone()

    # Pushes Reserve Slots
    if result and (result[0] == "Reserve" and not desc == "Reserve"):
        sql = "SELECT Number FROM Slot WHERE Event = %s and Description = %s"
        mycursor.execute(sql, [channel.id, 'Reserve'])

        result = mycursor.fetchall()
        new = [(int(x[0]) + 10, channel.id, x[0]) for x in result]

        sql = "UPDATE Slot SET Number = %s WHERE Event=%s and Number = %s"
        mycursor.executemany(sql, new)
        mydb.commit()

    elif result:
        return False

    if group.isdigit():

        sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Number = %s;"
        mycursor.execute(sql, [channel.id, group])

        if mycursor.fetchall() is None:
            return False

    else:

        sql = "SELECT Number FROM SlotGroup WHERE Event = %s and Name = %s;"
        var = [channel.id, group]
        mycursor.execute(sql, var)
        group = mycursor.fetchone()[0]

        if not group:
            return False

    sql = "INSERT INTO Slot (Event, Number, Description, GroupNumber) VALUES (%s, %s, %s, %s);"
    var = [channel.id, slot, desc, group]
    mycursor.execute(sql, var)
    mydb.commit()

    length = len(str(slot)) + len(desc) + 15

    sql = "UPDATE SlotGroup SET Length = Length + %s WHERE Number = %s and Event = %s;"
    var = [length, group, channel.id]

    mycursor.execute(sql, var)
    mydb.commit()

    return True


def delSlot(channel, slot):
    """
           Deletes a given slot
           Args:
                channel (channel): Server channel
                slot (string): Slot-Number

           Returns:
               (bool): if successful

       """

    sql = "SELECT Description, GroupNumber FROM Slot WHERE Event = %s and Number = %s;"
    var = [channel.id, slot]
    mycursor.execute(sql, var)
    desc = mycursor.fetchone()
    if not desc:
        return False

    length = len(str(slot)) + len(desc[0]) + 15

    sql = "DELETE FROM Slot WHERE Event = %s AND Number = %s;"
    mycursor.execute(sql, [channel.id, slot])
    mydb.commit()

    sql = "UPDATE SlotGroup SET Length = Length - %s WHERE Number = %s AND Event = %s"
    var = [length, desc[1], channel.id]
    mycursor.execute(sql, var)
    mydb.commit()

    return True


def editSlot(channel, slot, desc):
    """
           Edits a slot name
           Args:
               channel (channel): Server channel
               slot (string): Slot-Number
               desc (string): Name

           Returns:
               (bool): if successful

    """

    sql = "SELECT Description, GroupNumber FROM Slot WHERE Event = %s and Number = %s;"
    var = [channel.id, slot]
    mycursor.execute(sql, var)
    old_desc = mycursor.fetchone()
    if not old_desc:
        return False

    sql = "UPDATE Slot SET Description = %s WHERE Number = %s AND Event = %s;"
    var = [desc, slot, channel.id]
    mycursor.execute(sql, var)
    mydb.commit()

    length = len(desc) - len(old_desc[0])

    sql = "UPDATE SlotGroup SET Length = Length + %s WHERE Event = %s AND Number = %s;"
    var = [length, channel.id, old_desc[1]]
    mycursor.execute(sql, var)
    mydb.commit()

    return True


def addGroup(channel, number, name=""):
    """
           Adds a slot-group to a given event
           Args:
                channel (channel): Server channel
                number (int): Group-Number (counting from 0)
                name (string): Group-Name (optional)

           Returns:
                (bool): if successful

       """
    sql = "SELECT Name, Number FROM SlotGroup WHERE Event = %s and Number = %s;"
    var = [channel.id, int(number)]
    mycursor.execute(sql, var)
    result = mycursor.fetchone()
    if result and result[0] == "Reserve":
        sql = "UPDATE SlotGroup SET Number = %s WHERE Event = %s and Name = %s"
        var = [int(number) + 1, channel.id, 'Reserve']
        mycursor.execute(sql, var)
        mydb.commit()

    elif result:
        return False

    sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, '\n', %s);"
    length = len(name) + 1
    var = [number, channel.id, name, length]
    mycursor.execute(sql, var)
    mydb.commit()

    return True


def delGroup(channel, group):
    """
            Deletes a slot from a given event
            Args:
                channel (channel): Server channel
                group (string): Group-Number (counting form 0) or Group-Name

            Returns:
               (bool): if successful

    """

    if group.isdigit():
        sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Number = %s;"
        mycursor.execute(sql, [channel.id, group])

        if mycursor.fetchone() is None:
            return False

    else:
        sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Name = %s;"
        var = [channel.id, group]
        mycursor.execute(sql, var)

        if not group:
            return False

        group = mycursor.fetchone()[0]

    sql = "DELETE FROM Slot WHERE GroupNumber = %s AND Event = %s;"
    mycursor.execute(sql, [group, channel.id])
    mydb.commit()

    sql = "DELETE FROM SlotGroup WHERE Number = %s AND Event = %s;"
    mycursor.execute(sql, [group, channel.id])
    mydb.commit()

    return True
