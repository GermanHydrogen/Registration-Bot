import mysql.connector
from src.main.objects.util import with_cursor


class Choice:
    def __init__(self, db):
        self.db = db

    @with_cursor
    def accept_message(self, cursor: mysql.connector.MySQLConnection.cursor, msg_id: str) -> (str, str):
        """
        Accept a request
            Args:
                cursor: Database cursor
                msg_id: Message ID
            Returns:
                (Type of Message (campaign/trade), Result of acceptance)
        """

        sql = "SELECT * FROM Message WHERE MessageID = %s;"
        cursor.execute(sql, [str(msg_id)])
        result = cursor.fetchone()

        # TODO: REWORK

        if not result:
            return None
        if result[2] is None:
            return "campaign", self.accept_reservation(msg_id, result[0], result[1], result[3])
        else:
            return "trade", self.accept_swap(msg_id, result[0], result[1], result[2])

    # TODO: REWORK
    @with_cursor
    def accept_reservation(self, cursor: mysql.connector.MySQLConnection.cursor,
                           msg_id: str, event: str, user: str, slotnumber: str) -> str:
        """
        Accept a Reservation
        Args:
            cursor: Database cursor
            msg_id: ID of the reservation message
            event: ID of an event
            user: ID of an user
            slotnumber: Number of a slot

        Returns:
            Channel if successfull
            channel_id, when not None
        """

        sql = "DELETE FROM Message WHERE MessageID = %s;"
        cursor.execute(sql, [str(msg_id)])
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND User = %s"
        var = [None, user, event]
        cursor.execute(sql, var)
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        cursor.execute(sql, [user, event, slotnumber])
        self.db.commit()

        return event

    # TODO: REWORK
    @with_cursor
    def accept_swap(self, cursor: mysql.connector.MySQLConnection.cursor,
                    msg_id: str, event: str, req_user: str, rec_user: str) -> list:
        """
        Accept a Reservation
            Args:
                cursor: Database cursor
                msg_id: ID of the reservation message
                event: ID of an event
                req_user: ID of a requester
                rec_user: Number of a recipient

            Returns:
                (list): if successfull event, req_user, rec_user, when not None
        """

        sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
        val = [event, req_user]
        cursor.execute(sql, val)
        slot_1 = cursor.fetchone()

        sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
        val = [event, rec_user]
        cursor.execute(sql, val)
        slot_2 = cursor.fetchone()

        sql = "DELETE FROM Message WHERE MessageID = %s;"
        cursor.execute(sql, [msg_id])
        self.db.commit()

        if not slot_1:
            return req_user
        if not slot_2:
            return rec_user

        sql = "UPDATE Slot SET User = Null WHERE Number = %s AND Event = %s;"
        cursor.execute(sql, [slot_1[0], event])
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        val = [(req_user, event, slot_2[0]), (rec_user, event, slot_1[0])]
        cursor.executemany(sql, val)
        self.db.commit()

        return [event, req_user, rec_user]

    @with_cursor
    def deny_message(self, cursor: mysql.connector.MySQLConnection.cursor, msg_id: str):
        """
        Deny a request
            Args:
                cursor: Database cursor
                msg_id: Message ID
            Returns:
                (string): Type of Message (campaign/trade)
                (list): result of deny
        """
        sql = "SELECT * FROM Message WHERE MessageID = %s;"
        cursor.execute(sql, [str(msg_id)])
        result = cursor.fetchone()

        if not result:
            return None
        if result[2] is None:
            return "campaign", self.deny_reservation(msg_id, result[0], result[3])
        else:
            return "trade", self.deny_swap(msg_id, result[0], result[1], result[2])

    @with_cursor
    def deny_reservation(self, cursor: mysql.connector.MySQLConnection.cursor, msg_id, event, slotnumber):
        """
        Deny a Reservation
        Args:
            cursor: Database cursor
            msg_id: ID of the reservation message
            event: ID of an event
            slotnumber: Slotnumber with possible leading zeros
        Returns:
            (string): channel if successfull channel_id, when not None
        """

        sql = "DELETE FROM Message WHERE MessageID = %s;"
        cursor.execute(sql, [str(msg_id)])
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        var = [None, event, slotnumber]
        cursor.execute(sql, var)
        self.db.commit()

        return event

    @with_cursor
    def deny_swap(self, cursor: mysql.connector.MySQLConnection.cursor, msg_id, event, req_user, rec_user):
        """
        Deny a Reservation
           Args:
               cursor: Database cursor
               msg_id: ID of the reservation message
               event: ID of an event
               req_user: ID of a requester
               rec_user: Number of a recipient

           Returns:
               (list): if successfull event, req_user, rec_user, when not None
           """

        sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
        val = [event, req_user]
        cursor.execute(sql, val)
        slot_1 = cursor.fetchone()

        sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
        val = [event, rec_user]
        cursor.execute(sql, val)
        slot_2 = cursor.fetchone()

        sql = "DELETE FROM Message WHERE MessageID = %s;"
        cursor.execute(sql, [msg_id])
        self.db.commit()

        if not slot_1:
            return req_user
        if not slot_2:
            return rec_user

        return event, req_user, rec_user