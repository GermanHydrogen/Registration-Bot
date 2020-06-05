from math import ceil
from datetime import datetime, timedelta
from config.loader import cfg


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


class IO:
    def __init__(self, cfg, db, cursor):
        self.cfg = cfg
        self.db = db
        self.cursor = cursor

    def get_user_id(self, nname, channel):
        """
            Gets an user id
            Args:
                nname (string): Nickname of a user
                channel (channel): Channel

            Returns:
                (int)

        """

        sql = "SElECT ID FROM User WHERE Nickname = %s;"
        self.cursor.execute(sql, [nname])
        result = self.cursor.fetchall()

        if result:
            return result[0][0]
        else:
            nname = get_members(nname, channel)
            if not nname:
                return None

            sql = f"INSERT IGNORE INTO User VALUES (%s, %s);"
            var = [nname.id, nname.display_name]
            self.cursor.execute(sql, var)
            self.db.commit()

            return nname.id

    def pull_reserve(self, event_id):
        """
            Pulls users from reserve into open slots
            Args:
                event_id (string): Event ID

            Returns:
                (bool): if free slots exist

        """
        sql = "SELECT Number FROM Slot " \
              "WHERE Event = %s AND User IS NULL AND Description != 'Reserve';"

        self.cursor.execute(sql, [event_id])
        free = self.cursor.fetchall()

        sql = "SELECT Number, User FROM Slot " \
              "WHERE Event = %s and User IS NOT NULL AND Description = 'Reserve' " \
              "ORDER BY CONVERT(Number, UNSIGNED INTEGER);"

        self.cursor.execute(sql, [event_id])
        reserve = self.cursor.fetchall()

        if free and reserve:
            for index, elem in enumerate(free, start=0):

                if index == len(reserve):
                    return True

                sql = "UPDATE Slot SET User= NULL WHERE Event= %s and Number = %s;"
                var = [event_id, reserve[index][0]]
                self.cursor.execute(sql, var)
                self.db.commit()

                sql = "UPDATE Slot SET User= %s WHERE Event= %s and Number = %s;"
                var = [reserve[index][1], event_id, elem[0]]
                self.cursor.execute(sql, var)
                self.db.commit()

            return False
        elif free:
            return True
        else:
            return False

    def sort_reserve(self, channel):
        """
            Sorts the reserve slots, so its filled from bottom up
            Args:
                channel (discord.TextChannel): Server channel

            Returns:
                (bool): if successful

        """
        sql = "SELECT Number, User FROM Slot WHERE Event = %s and Description = 'Reserve' ORDER BY Number"
        self.cursor.execute(sql, [channel.id])
        reserve = self.cursor.fetchall()

        count = 0

        for x, y in reserve:
            if not y:
                continue
            else:
                sql = "UPDATE Slot SET User = NULL WHERE User = %s AND Event = %s;"
                self.cursor.execute(sql, [y, channel.id])
                self.db.commit()

                sql = "UPDATE Slot SET User = %s WHERE Number = %s AND Event = %s;"
                var = [y, reserve[count][0], channel.id]
                self.cursor.execute(sql, var)
                self.db.commit()

                count += 1

    def createEvent(self, msg_list, author, time, bot=None):
        """
               Creates an event in the database
               Args:
                   msg_list (list of msg object): The message containing the slotlist
                   author (user object): Author of the slotlist
                   time (str): start time of the event
                   bot (user object): Used Bot user (optional)

               Returns:
                   (bool): if successful

        """

        channel = msg_list[0].channel
        split = channel.name.split("-")
        time = time.strip() + ":00"

        if not (len(split) == 4 and len(split[0]) == 4 and len(split[1]) == 2 and len(split[2]) == 2 and split[3]):
            return False

        date = "-".join(split[:3])
        name = split[-1]
        event = channel.id

        sql = "SELECT ID FROM Event WHERE ID = %s;"
        self.cursor.execute(sql, [event])

        if self.cursor.fetchall():
            sql = "DELETE FROM Slot WHERE Event = %s;"
            self.cursor.execute(sql, [event])
            self.db.commit()

            sql = "DELETE FROM SlotGroup WHERE Event = %s;"
            self.cursor.execute(sql, [event])
            self.db.commit()

            sql = "DELETE FROM Notify WHERE Event = %s;"
            self.cursor.execute(sql, [event])
            self.db.commit()

            sql = "UPDATE Event SET Name=%s, Author=%s, Date=%s, Time=%s,Type=%s WHERE ID = %s;"
            var = [channel.name, author.id, date, time, name, event]
            self.cursor.execute(sql, var)
            self.db.commit()

        else:
            # Check if Author User exists
            sql = "SELECT ID FROM User WHERE ID = %s;"
            self.cursor.execute(sql, [author.id])

            if not self.cursor.fetchall():
                sql = "INSERT INTO User (ID, Nickname) VALUES (%s, %s);"
                var = [author.id, author.display_name]
                self.cursor.execute(sql, var)
                self.db.commit()

            sql = "INSERT INTO Event (ID, Name, Author, Date, Time, Type) VALUES (%s, %s, %s, %s, %s, %s);"
            var = [event, channel.name, author.id, date, time, name]
            self.cursor.execute(sql, var)

            self.db.commit()

        sql = "SELECT Number, MsgID FROM EventMessage WHERE Event = %s ORDER BY Number;"
        self.cursor.execute(sql, [channel.id])

        messages = self.cursor.fetchall()

        if False not in [msg.author == bot for msg in msg_list]:

            for index, elem in enumerate(messages, start=1):
                if index <= len(msg_list):

                    sql = "UPDATE EventMessage SET MsgID = %s WHERE Event = %s AND Number = %s;"
                    var = [msg_list[-index].id, channel.id, elem[0]]

                    self.cursor.execute(sql, var)
                    self.db.commit()
                else:
                    sql = "DELETE FROM EventMessage WHERE Number = %s"
                    var = [elem[0]]
                    self.cursor.execute(sql, var)
                    self.db.commit()
        else:
            sql = "DELETE FROM EventMessage WHERE Event = %s"
            var = [channel.id]
            self.cursor.execute(sql, var)
            self.db.commit()

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
                    data[list(data)[0]]["User"] = self.get_user_id(data[list(data)[0]]["User"], channel)

                else:
                    data[list(data)[0]]["User"] = None
                    struct[-1]["Length"] += 10  # Average lenght of a Discord Nickname + white space

                slots.update(data)

            elif line.strip() == "":
                current_buffer += "\n"
            else:
                if line.strip().replace("**", "") == "Reserve":
                    reserve = True

                lenght = len(current_buffer) + len(line.strip()) + 1
                struct.append({"Name": line.strip(), "Struct": current_buffer, "Length": lenght})
                current_buffer = ""

        for a, b, c, d, e in [(num, event, elem["Name"], elem["Struct"], elem["Length"]) for num, elem in
                              enumerate(struct, start=0)]:
            sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, %s, %s);"
            var = [a, b, c, d, e]

            self.cursor.execute(sql, var)
            self.db.commit()

        sql = "INSERT INTO Slot VALUES (%s, %s, %s, %s, %s)"
        var = [(event, index, elem["Description"], elem["User"], elem["GroupNum"]) for index, elem in
               slots.items()]
        self.cursor.executemany(sql, var)
        self.db.commit()

        # Notify System

        result = datetime.strptime(date + " " + time, '%Y-%m-%d %H:%M:%S')
        delta = timedelta(hours=cfg["std_notify"])

        delta = result - delta

        sql = "INSERT INTO Notify VALUES (%s, %s, %s, %s)"
        var = [(event, elem["User"], 1, delta) for index, elem in slots.items() if elem["User"]]
        self.cursor.executemany(sql, var)
        self.db.commit()

        if not reserve:
            lenght = int(len(list(slots)) * self.cfg["res_ratio"]) + 1
            begin = ceil((int(list(slots)[-1]) + 1) / 10) * 10
            msg_format = len(list(slots)[-1]) - 1

            groupNum = len(struct)
            sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, %s, %s);"
            var = [groupNum, channel.id, "Reserve", '\n', lenght * (9 + 14 + len(str(groupNum))) + 12]

            self.cursor.execute(sql, var)
            self.db.commit()

            sql = "INSERT INTO Slot (Event, Number, Description, GroupNumber) VALUES (%s, %s, %s, %s);"
            var = [(channel.id, str(index).rjust(msg_format, "0"), "Reserve", groupNum) for index in
                   range(begin, begin + lenght)]

            self.cursor.executemany(sql, var)
            self.db.commit()

        return True

    async def writeEvent(self, channel, manage=False, new=False):
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

        free = self.pull_reserve(channel_id)
        self.sort_reserve(channel)

        if manage:
            sql = "SELECT Number, Length FROM SlotGroup WHERE Event = %s ORDER BY Number;"
            self.cursor.execute(sql, [channel_id])
            group = self.cursor.fetchall()

            total = sum([x[1] for x in group])

            sql = "SELECT Number FROM EventMessage WHERE Event = %s;"
            self.cursor.execute(sql, [channel_id])

            ids = self.cursor.fetchall()

            if not ids or new:
                number = int((total + 400) / 2000) + 1
                limit = int(total / number)

                ids = []

                for x in range(0, number):
                    sql = "INSERT INTO EventMessage (Event) VALUES (%s);"
                    self.cursor.execute(sql, [channel_id])
                    self.db.commit()

                    ids.append((self.cursor.lastrowid,))

            else:

                number = len(ids)
                limit = int(total / number)

            times_limit = 1
            buffer = 0
            last_split = 0

            output = [[]]

            for index, elem in enumerate(group, start=0):
                buffer += elem[1]

                if buffer > limit * times_limit:
                    sql = "UPDATE SlotGroup SET Msg = %s WHERE Event = %s AND Number = %s;"
                    var = [(ids[times_limit - 1][0], channel_id, x[0]) for x in group[last_split:index]]

                    self.cursor.executemany(sql, var)
                    self.db.commit()

                    last_split = index
                    times_limit += 1
                    output.append([])

                if times_limit >= number:
                    break

            sql = "UPDATE SlotGroup SET Msg = %s WHERE Event = %s AND Number = %s;"
            var = [(ids[times_limit - 1][0], channel_id, x[0]) for x in group[last_split:]]

            self.cursor.executemany(sql, var)
            self.db.commit()

        sql = "SELECT Number, MsgID FROM EventMessage WHERE Event = %s ORDER BY Number;"
        self.cursor.execute(sql, [channel_id])
        msgs = self.cursor.fetchall()

        output = "**Slotliste**\n"
        for msg_id in msgs:
            sql = "SELECT Number, Name, Struct, Length FROM SlotGroup WHERE Event = %s AND Msg = %s ORDER BY Number;"
            self.cursor.execute(sql, [channel_id, msg_id[0]])
            group = self.cursor.fetchall()

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
                self.cursor.execute(sql, var)
                slots = self.cursor.fetchall()
                for x in slots:
                    if x[2] is not None:

                        sql = "SELECT Nickname FROM User WHERE ID = %s;"
                        self.cursor.execute(sql, [x[2]])
                        user = self.cursor.fetchone()[0]

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
                    self.cursor.execute(sql, var)
                    self.db.commit()

            else:
                new_msg = await channel.send(output)

                sql = "UPDATE EventMessage SET MsgID = %s WHERE Number = %s;"
                var = [new_msg.id, msg_id[0]]
                self.cursor.execute(sql, var)

                self.db.commit()

            output = ""
