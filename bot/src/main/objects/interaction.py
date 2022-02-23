import mysql.connector

from bot.src.main.objects.util import with_cursor


class Interaction:
    def __init__(self, db):
        self.db = db

    @with_cursor
    def reserve_slots(self, cursor: mysql.connector.MySQLConnection.cursor,
                      event: str, user: str, slotnumber: str, msg_id: str, date: str) -> bool:
        """
        Creates Requests to Users for paticipating again
        Args:
            cursor: Database cursor
            event: Event of the slot
            user: Discord user id for which the slot is reserved
            slotnumber: Number of the slot to reserve the slot
            msg_id: Message ID of the request
            date: When the slot was reserved
        Returns:
            if successful
        """

        try:
            sql = "INSERT INTO Message (Event, User, SlotNumber, MessageID, DateUntil) VALUES (%s, %s, %s, %s, %s);"
            cursor.execute(sql, [event, user, slotnumber, msg_id, date])
            self.db.commit()
        except:
            return False

        # Blocks all reserved slots
        try:
            sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
            cursor.execute(sql, ['C00000000000000000', event, slotnumber])
            self.db.commit()
        except:
            return False

        return True

    @with_cursor
    def copy_dummies(self, cursor: mysql.connector.MySQLConnection.cursor, target: str, origin: str):
        """
        Copies dummy user from one event to another
        Args:
            cursor: Database cursor
            target: target event
            origin: origin event

        Returns:
            (bool): if successful
        """

        sql = "UPDATE Slot s1, (SELECT User, Number FROM Slot WHERE (NOT User regexp '^[0-9]') AND Event = %s) s2 " \
              "SET s1.User = s2.User WHERE s1.Event = %s AND s1.Number = s2.Number"

        var = [str(origin), str(target)]
        cursor.execute(sql, var)
        self.db.commit()

        return True

    @with_cursor
    def delete_all_messages(self, cursor: mysql.connector.MySQLConnection.cursor, event: str) -> list:
        """
        Deletes all eventmessages for an event
        Args:
            cursor: Database cursor
            event: event id

        Returns:
            list: deleted msgs
        """

        sql = "SELECT User, MessageID FROM Message " \
              "WHERE Event = %s AND RecUser is NULL;"
        cursor.execute(sql, [str(event)])
        slots = cursor.fetchall()

        sql = "DELETE FROM Message WHERE Event = %s;"
        cursor.execute(sql, [str(event)])
        self.db.commit()

        return slots

    @with_cursor
    def cleanup_message(self, cursor: mysql.connector.MySQLConnection.cursor, date: str) -> (list, list, list):
        """
        Deletes all timeouted messages
        Args:
            cursor: Database cursor
            date: given date
        Returns:
            (list): list of effected channel ids's (campaign)
            (list): list of effected users (campaign)
            (list): list of effected event id, user, recUser, msgID (trade)
        """

        sql = "SELECT Event, User, SlotNumber, MessageID FROM Message " \
              "WHERE (DATEDIFF(DateUntil, %s) < 0) AND RecUser is NULL;"
        cursor.execute(sql, [str(date)])
        slots = cursor.fetchall()

        if slots:
            sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
            var = [(None, x[0], x[2]) for x in slots]
            cursor.executemany(sql, var)
            self.db.commit()

        channels = list(dict.fromkeys([x[0] for x in slots]))
        campUsers = [(x[1], x[3]) for x in slots]

        sql = "SELECT Event, User, RecUser, MessageID FROM Message " \
              "WHERE (DATEDIFF(DateUntil, %s) < 0) AND RecUser is not Null;"
        cursor.execute(sql, [str(date)])
        result = cursor.fetchall()

        sql = "DELETE FROM Message WHERE (DATEDIFF(DateUntil, %s) < 0);"
        cursor.execute(sql, [str(date)])
        self.db.commit()

        return [[channels, campUsers], result]

    @with_cursor
    def validate_swap(self, cursor: mysql.connector.MySQLConnection.cursor,
                      event: str, req_user: str, rec_user: str) -> int:
        """
        Validate a swap message
            Args:
                cursor: Database cursor
                event: Event ID
                req_user: User ID of the requester
                rec_user: User ID of the recipient
            Returns:
                (int): Status (1: valid, 2: exceeds limit, 0: not in the list)
        """

        if not rec_user.isdigit():
            return 0

        sql = "SELECT COUNT(*) FROM Message WHERE Event = %s AND User = %s GROUP BY User;"
        val = [event, req_user]
        cursor.execute(sql, val)

        if cursor.fetchone() is not None:
            return 2

        sql = "SELECT User FROM Slot WHERE Event = %s AND Description != %s;"
        cursor.execute(sql, [event, 'Reserve'])
        result = cursor.fetchall()

        if not ((str(req_user),) in result and (str(rec_user),) in result):
            return 0

        return 1

    @with_cursor
    def create_swap(self, cursor: mysql.connector.MySQLConnection.cursor,
                    event: str, req_user: str, rec_user: str, msg_id: str, date: str) -> None:
        """
        Creates a swap request
            Args:
                cursor: Database cursor
                event: Event ID
                req_user: User ID of the requester
                rec_user: User ID of the recipient
                msg_id: Message ID of the request
                date: Date until the request is due
        """

        sql = "INSERT INTO Message (Event, User, RecUser, MessageID, DateUntil) VALUES (%s, %s, %s, %s, %s);"
        val = [event, req_user, rec_user, msg_id, date]
        cursor.execute(sql, val)
        self.db.commit()
