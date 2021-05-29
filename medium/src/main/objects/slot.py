from src.main.objects.notify import EditLocale
import mysql.connector
import discord
from src.main.objects.util import with_cursor


class EditSlot:
    def __init__(self, db):
        self.db = db

        self.notify = EditLocale(db)

    @with_cursor
    def slot(self, cursor: mysql.connector.MySQLConnection.cursor, channel: discord.TextChannel,
             user_id: int, num: str, user_displayname: str = None, force: bool = False) -> bool:
        """
        Slots a given user in the given slot
        Args:
            cursor: Database cursor
            channel: Server channel
            user_id: User ID
            num: Number of the slot
            user_displayname: User nickname (optional)
            force: If true, accept duplicates (optional)

        Returns:
           (bool): if successful
        """

        sql = "SELECT User FROM Slot, Event " \
              "WHERE Event.ID = Slot.Event and Event = %s and Number = %s and (NOT Event.Locked OR %s);"
        var = [channel.id, num, force]
        cursor.execute(sql, var)
        slot = cursor.fetchone()

        if slot is None or slot[0] is not None:
            return False

        sql = "SELECT ID, Nickname FROM User WHERE ID = %s;"
        cursor.execute(sql, [user_id])
        result = cursor.fetchone()

        if (not force) and (result is None):
            sql = "INSERT INTO User (ID, Nickname) VALUES (%s, %s);"
            var = [str(user_id), user_displayname]
            cursor.execute(sql, var)
            self.db.commit()
        elif not force and (result is not None) and result[1] != user_displayname:
            sql = "UPDATE User SET Nickname= %s WHERE ID = %s;"
            var = [str(user_displayname), str(user_id)]
            cursor.execute(sql, var)
            self.db.commit()

        if not force:
            sql = "UPDATE Slot SET User = NULL WHERE STRCMP(User, %s) = 0 AND Event = %s;"
            var = [str(user_id), str(channel.id)]
            cursor.execute(sql, var)
            self.db.commit()

        self.notify.create(channel.id, user_id)

        try:
            sql = "UPDATE Slot SET User = %s WHERE Number = %s and Event = %s;"
            var = [user_id, num, channel.id]
            cursor.execute(sql, var)
            self.db.commit()
        except mysql.connector.errors.DatabaseError:
            return False

        return True

    @with_cursor
    def unslot(self, cursor: mysql.connector.MySQLConnection.cursor,
               channel: discord.TextChannel, user_id: str = "", slot: str = "") -> bool:
        """
        Unslots a user or clears an slot from an Event
        Args:
            cursor: Database cursor
            channel: Server channel
            user_id: User ID
            slot: Slotnumber

        Returns:
            (bool): if successful
        """
        type = ['Number', 'User'][int(slot == "")]
        arg = [slot, user_id][int(slot == "")]

        sql = f"SELECT Number FROM Slot WHERE STRCMP({type} , %s) = 0 and Event = %s;"
        var = [arg, channel.id]
        cursor.execute(sql, var)
        result = cursor.fetchone()

        if result:

            sql = f"UPDATE Slot SET User = NULL WHERE STRCMP({type}, %s) = 0 and Event = %s;"
            var = [arg, channel.id]
            cursor.execute(sql, var)
            self.db.commit()

            self.notify.toggle(channel.id, user_id, True)

            return result[0]
        else:
            return False

    @with_cursor
    def add(self, cursor: mysql.connector.MySQLConnection.cursor, channel: discord.TextChannel,
            slot: int, group: str, desc: str):
        """
           Adds a slot to a given event
           Args:
                cursor: Database cursor
                channel (channel): Server channel
                slot (int): Slot-Number
                group (string): Group-Number (counting form 0) or Group-Name
                desc (string): Name

           Returns:
               (bool): if successful
           """

        sql = "SELECT Description FROM Slot WHERE Event = %s and Number = %s;"
        var = [channel.id, slot]
        cursor.execute(sql, var)

        result = cursor.fetchone()

        # Pushes Reserve Slots
        if result and (result[0] == "Reserve" and not desc == "Reserve"):
            sql = "SELECT Number FROM Slot WHERE Event = %s and Description = %s"
            cursor.execute(sql, [channel.id, 'Reserve'])

            result = cursor.fetchall()
            new = [(int(x[0]) + 10, channel.id, x[0]) for x in result]

            sql = "UPDATE Slot SET Number = %s WHERE Event=%s and Number = %s"
            cursor.executemany(sql, new)
            self.db.commit()

        elif result:
            return False

        if group.isdigit():

            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Number = %s;"
            cursor.execute(sql, [channel.id, group])

            if cursor.fetchall() is None:
                return False

        else:

            sql = "SELECT Number FROM SlotGroup WHERE Event = %s and Name = %s;"
            var = [channel.id, group]
            cursor.execute(sql, var)
            group = cursor.fetchone()[0]

            if not group:
                return False

        sql = "INSERT INTO Slot (Event, Number, Description, GroupNumber) VALUES (%s, %s, %s, %s);"
        var = [channel.id, slot, desc, group]
        cursor.execute(sql, var)
        self.db.commit()

        length = len(str(slot)) + len(desc) + 15

        sql = "UPDATE SlotGroup SET Length = Length + %s WHERE Number = %s and Event = %s;"
        var = [length, group, channel.id]

        cursor.execute(sql, var)
        self.db.commit()

        return True

    @with_cursor
    def delete(self, cursor: mysql.connector.MySQLConnection.cursor, channel: discord.TextChannel, slot: str) -> bool:
        """
        Deletes a given slot
        Args:
            cursor: Database cursor
            channel: Server channel
            slot: Slot-Number

        Returns:
           (bool): if successful
           """

        sql = "SELECT Description, GroupNumber FROM Slot WHERE Event = %s and Number = %s;"
        var = [channel.id, slot]
        cursor.execute(sql, var)
        desc = cursor.fetchone()
        if not desc:
            return False

        length = len(str(slot)) + len(desc[0]) + 15

        sql = "DELETE FROM Slot WHERE Event = %s AND Number = %s;"
        cursor.execute(sql, [channel.id, slot])
        self.db.commit()

        sql = "UPDATE SlotGroup SET Length = Length - %s WHERE Number = %s AND Event = %s"
        var = [length, desc[1], channel.id]
        cursor.execute(sql, var)
        self.db.commit()

        return True

    @with_cursor
    def edit(self, cursor: mysql.connector.MySQLConnection.cursor,
             channel: discord.TextChannel, slot: str, desc: str) -> bool:
        """
        Edits a slot name
        Args:
           cursor: Database cursor
           channel: Server channel
           slot: Slot-Number
           desc: Name

        Returns:
           (bool): if successful
        """

        sql = "SELECT Description, GroupNumber FROM Slot WHERE Event = %s and Number = %s;"
        var = [channel.id, slot]
        cursor.execute(sql, var)
        old_desc = cursor.fetchone()
        if not old_desc:
            return False

        sql = "UPDATE Slot SET Description = %s WHERE Number = %s AND Event = %s;"
        var = [desc, slot, channel.id]
        cursor.execute(sql, var)
        self.db.commit()

        length = len(desc) - len(old_desc[0])

        sql = "UPDATE SlotGroup SET Length = Length + %s WHERE Event = %s AND Number = %s;"
        var = [length, channel.id, old_desc[1]]
        cursor.execute(sql, var)
        self.db.commit()

        return True

    @with_cursor
    def add_group(self, cursor: mysql.connector.MySQLConnection.cursor,
                  channel: discord.TextChannel, number: int, name: str = "") -> bool:
        """
        Adds a slot-group to a given event
        Args:
            cursor: Database cursor
            channel: Server channel
            number: Group-Number (counting from 0)
            name: Group-Name (optional)

        Returns:
            (bool): if successful
        """

        sql = "SELECT Name, Number FROM SlotGroup WHERE Event = %s and Number = %s;"
        var = [channel.id, int(number)]
        cursor.execute(sql, var)
        result = cursor.fetchone()
        if result and result[0] == "Reserve":
            sql = "UPDATE SlotGroup SET Number = %s WHERE Event = %s and Name = %s"
            var = [int(number) + 1, channel.id, 'Reserve']
            cursor.execute(sql, var)
            self.db.commit()

        elif result:
            return False

        sql = "INSERT INTO SlotGroup (Number, Event, Name, Struct, Length) VALUES (%s, %s, %s, '\n', %s);"
        length = len(name) + 1
        var = [number, channel.id, name, length]
        cursor.execute(sql, var)
        self.db.commit()

        return True

    @with_cursor
    def del_group(self, cursor: mysql.connector.MySQLConnection.cursor,
                  channel: discord.TextChannel, group: str) -> bool:
        """
        Deletes a slot from a given event
        Args:
            cursor: Database cursor
            channel: Server channel
            group: Group-Number (counting form 0) or Group-Name

        Returns:
           (bool): if successful
        """

        if group.isdigit():
            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Number = %s;"
            cursor.execute(sql, [channel.id, group])

            if cursor.fetchone() is None:
                return False

        else:
            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Name = %s;"
            var = [channel.id, group]
            cursor.execute(sql, var)

            if not group:
                return False

            group = cursor.fetchone()[0]

        sql = "DELETE FROM Slot WHERE GroupNumber = %s AND Event = %s;"
        cursor.execute(sql, [group, channel.id])
        self.db.commit()

        sql = "DELETE FROM SlotGroup WHERE Number = %s AND Event = %s;"
        cursor.execute(sql, [group, channel.id])
        self.db.commit()

        return True

    @with_cursor
    def edit_group(self, cursor: mysql.connector.MySQLConnection.cursor,
                   channel: discord.TextChannel, group: str, name: str) -> bool:
        """
        Edits the name of slot from a given event
        Args:
            cursor: Database cursor
            channel: Server channel
            group: Group-Number (counting form 0) or Group-Name
            name: Group Name to change to

        Returns:
           (bool): if successful
        """

        if group.isdigit():
            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Number = %s;"
            cursor.execute(sql, [channel.id, group])

            if cursor.fetchone() is None:
                return False

        else:
            sql = "SELECT Number FROM SlotGroup WHERE Event = %s AND Name = %s;"
            var = [channel.id, group]
            cursor.execute(sql, var)

            if not group:
                return False

            group = cursor.fetchone()[0]

        sql = "UPDATE SlotGroup SET Name=%s WHERE Number = %s AND Event = %s;"
        cursor.execute(sql, [name, group, channel.id])
        self.db.commit()

        return True

    @with_cursor
    def toggle_lock(self, cursor: mysql.connector.MySQLConnection.cursor, channel: discord.TextChannel) -> bool:
        """
        Toggles the lock on an event
        Args:
            cursor: Database cursor
            channel: Server channel

        Returns:
            (bool): if successful
        """

        sql = "UPDATE Event SET Locked = NOT Locked WHERE ID = %s;"
        cursor.execute(sql, [channel.id])
        self.db.commit()

        return cursor.rowcount == 1
