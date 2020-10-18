class Edit:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def reserveSlots(self, query):
        """
                Creates Requests to Users for paticipating again
                Args:
                    query (list): List containing event-id, user-id, slotnumber, message-id, and date
                Returns:
                    (bool): if successful
        """

        try:
            sql = "INSERT INTO Message (Event, User, SlotNumber, MessageID, DateUntil) VALUES (%s, %s, %s, %s, %s);"
            self.cursor.executemany(sql, query)
            self.db.commit()
        except:
            return False

        # Blocks all reserved slots
        try:
            sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
            var = [('C00000000000000000', x[0], x[2]) for x in query]
            self.cursor.executemany(sql, var)
            self.db.commit()
        except:
            return False

        return True

    def copyDummies(self, target, origin):
        """
        Copies dummy user from one event to another
        Args:
            target (str): target event
            origin (str): origin event

        Returns:
            (bool): if successful
        """

        sql = "UPDATE Slot s1, (SELECT User, Number FROM Slot WHERE (NOT User regexp '^[0-9]') AND Event = %s) s2 " \
              "SET s1.User = s2.User WHERE s1.Event = %s AND s1.Number = s2.Number"

        var = [str(origin), str(target)]
        self.cursor.execute(sql, var)
        self.db.commit()

        return True

    def deleteAllMessages(self, event):
        """
        Deletes all eventmessages for an event

        Args:
            event (str): event id

        Returns:
            list: deleted msgs
        """

        sql = "SELECT User, MessageID FROM Message " \
              "WHERE Event = %s AND RecUser is NULL;"
        self.cursor.execute(sql, [str(event)])
        slots = self.cursor.fetchall()

        sql = "DELETE FROM Message WHERE Event = %s;"
        self.cursor.execute(sql, [str(event)])
        self.db.commit()

        return slots

    def cleanupMessage(self, date):
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
        self.cursor.execute(sql, [str(date)])
        slots = self.cursor.fetchall()

        if slots:
            sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
            var = [(None, x[0], x[2]) for x in slots]
            self.cursor.executemany(sql, var)
            self.db.commit()

        channels = list(dict.fromkeys([x[0] for x in slots]))
        campUsers = [(x[1], x[3]) for x in slots]

        sql = "SELECT Event, User, RecUser, MessageID FROM Message " \
              "WHERE (DATEDIFF(DateUntil, %s) < 0) AND RecUser is not Null;"
        self.cursor.execute(sql, [str(date)])
        result = self.cursor.fetchall()

        sql = "DELETE FROM Message WHERE (DATEDIFF(DateUntil, %s) < 0);"
        self.cursor.execute(sql, [str(date)])
        self.db.commit()

        return [[channels, campUsers], result]

    def validateSwap(self, event, req_user, rec_user):
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
        self.cursor.execute(sql, val)

        if self.cursor.fetchone() is not None:
            return 2

        sql = "SELECT User FROM Slot WHERE Event = %s AND Description != %s;"
        self.cursor.execute(sql, [event, 'Reserve'])
        result = self.cursor.fetchall()

        if not ((str(req_user),) in result and (str(rec_user),) in result):
            return 0

        return 1

    def createSwap(self, event, req_user, rec_user, msg_id, date):
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
        self.cursor.execute(sql, val)
        self.db.commit()
