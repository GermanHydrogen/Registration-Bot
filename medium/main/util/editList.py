from notify.util.editLocale import EditLocale
import mysql.connector


class EditList:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

        self.notify = EditLocale(db, cursor)

    def slotEvent(self, channel, user_id, num, user_displayname=None, force=False):
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
        self.cursor.execute(sql, var)
        slot = self.cursor.fetchone()

        if slot is None or slot[0] is not None:
            return False

        sql = "SELECT ID, Nickname FROM User WHERE ID = %s;"
        self.cursor.execute(sql, [user_id])
        result = self.cursor.fetchone()

        if (not force) and (result is None):
            sql = "INSERT INTO User VALUES (%s, %s);"
            var = [str(user_id), user_displayname]
            self.cursor.execute(sql, var)
            self.db.commit()
        elif not force and (result is not None) and result[1] != user_displayname:
            sql = "UPDATE User SET Nickname= %s WHERE ID = %s;"
            var = [str(user_displayname), str(user_id)]
            self.cursor.execute(sql, var)
            self.db.commit()

        if not force:
            sql = "UPDATE Slot SET User = NULL WHERE STRCMP(User, %s) = 0 AND Event = %s;"
            var = [str(user_id), str(channel.id)]
            self.cursor.execute(sql, var)
            self.db.commit()

        self.notify.create(channel.id, user_id)

        try:
            sql = "UPDATE Slot SET User = %s WHERE Number = %s and Event = %s;"
            var = [user_id, num, channel.id]
            self.cursor.execute(sql, var)
            self.db.commit()

        except mysql.connector.errors.DatabaseError:
            return False

        return True

    def unslotEvent(self, channel, user_id):
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
        self.cursor.execute(sql, var)

        result = self.cursor.fetchone()

        if result:

            sql = "UPDATE Slot SET User = NULL WHERE STRCMP(User, %s) = 0 and Event = %s;"
            var = [user_id, channel.id]
            self.cursor.execute(sql, var)
            self.db.commit()

            self.notify.toggle(channel.id, user_id, True)

            return result[0]
        else:
            return False

    def addSlot(self, channel, slot, group, desc):
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
        self.cursor.execute(sql, var)

        result = self.cursor.fetchone()

        # Pushes Reserve Slots
        if result and (result[0] == "Reserve" and not desc == "Reserve"):
            sql = "SELECT Number FROM Slot WHERE Event = %s and Description = %s"
            self.cursor.execute(sql, [channel.id, 'Reserve'])

            result = self.cursor.fetchall()
            new = [(int(x[0]) + 10, channel.id, x[0]) for x in result]

            sql = "UPDATE Slot SET Number = %s WHERE Event=%s and Number = %s"
            self.cursor.executemany(sql, new)
            self.db.commit()

        elif result:
            return False

        if group.isdigit():

            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Number = %s;"
            self.cursor.execute(sql, [channel.id, group])

            if self.cursor.fetchall() is None:
                return False

        else:

            sql = "SELECT Number FROM SlotGroup WHERE Event = %s and Name = %s;"
            var = [channel.id, group]
            self.cursor.execute(sql, var)
            group = self.cursor.fetchone()[0]

            if not group:
                return False

        sql = "INSERT INTO Slot (Event, Number, Description, GroupNumber) VALUES (%s, %s, %s, %s);"
        var = [channel.id, slot, desc, group]
        self.cursor.execute(sql, var)
        self.db.commit()

        length = len(str(slot)) + len(desc) + 15

        sql = "UPDATE SlotGroup SET Length = Length + %s WHERE Number = %s and Event = %s;"
        var = [length, group, channel.id]

        self.cursor.execute(sql, var)
        self.db.commit()

        return True

    def delSlot(self, channel, slot):
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
        self.cursor.execute(sql, var)
        desc = self.cursor.fetchone()
        if not desc:
            return False

        length = len(str(slot)) + len(desc[0]) + 15

        sql = "DELETE FROM Slot WHERE Event = %s AND Number = %s;"
        self.cursor.execute(sql, [channel.id, slot])
        self.db.commit()

        sql = "UPDATE SlotGroup SET Length = Length - %s WHERE Number = %s AND Event = %s"
        var = [length, desc[1], channel.id]
        self.cursor.execute(sql, var)
        self.db.commit()

        return True

    def editSlot(self, channel, slot, desc):
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
        self.cursor.execute(sql, var)
        old_desc = self.cursor.fetchone()
        if not old_desc:
            return False

        sql = "UPDATE Slot SET Description = %s WHERE Number = %s AND Event = %s;"
        var = [desc, slot, channel.id]
        self.cursor.execute(sql, var)
        self.db.commit()

        length = len(desc) - len(old_desc[0])

        sql = "UPDATE SlotGroup SET Length = Length + %s WHERE Event = %s AND Number = %s;"
        var = [length, channel.id, old_desc[1]]
        self.cursor.execute(sql, var)
        self.db.commit()

        return True

    def addGroup(self, channel, number, name=""):
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
        self.cursor.execute(sql, var)
        result = self.cursor.fetchone()
        if result and result[0] == "Reserve":
            sql = "UPDATE SlotGroup SET Number = %s WHERE Event = %s and Name = %s"
            var = [int(number) + 1, channel.id, 'Reserve']
            self.cursor.execute(sql, var)
            self.db.commit()

        elif result:
            return False

        sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, '\n', %s);"
        length = len(name) + 1
        var = [number, channel.id, name, length]
        self.cursor.execute(sql, var)
        self.db.commit()

        return True

    def delGroup(self, channel, group):
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
            self.cursor.execute(sql, [channel.id, group])

            if self.cursor.fetchone() is None:
                return False

        else:
            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Name = %s;"
            var = [channel.id, group]
            self.cursor.execute(sql, var)

            if not group:
                return False

            group = self.cursor.fetchone()[0]

        sql = "DELETE FROM Slot WHERE GroupNumber = %s AND Event = %s;"
        self.cursor.execute(sql, [group, channel.id])
        self.db.commit()

        sql = "DELETE FROM SlotGroup WHERE Number = %s AND Event = %s;"
        self.cursor.execute(sql, [group, channel.id])
        self.db.commit()

        return True
