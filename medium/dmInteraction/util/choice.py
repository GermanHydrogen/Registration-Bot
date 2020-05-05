class Choice:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def acceptMessage(self, msg_id):
        """
            Accept a request
                Args:
                    msg_id (string): Message ID
                Returns:
                    (string): Type of Message (campaign/trade)
                    (list): result of acceptance
        """

        sql = "SELECT * FROM Message WHERE MessageID = %s;"
        self.cursor.execute(sql, [str(msg_id)])
        result = self.cursor.fetchone()
        if not result:
            return None
        if result[2] is None:
            return "campaign", self.acceptReservation(msg_id, result[0], result[1], result[3])
        else:
            return "trade", self.acceptSwap(msg_id, result[0], result[1], result[2])

    def acceptReservation(self, msg_id, event, user, slotnumber):
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
        self.cursor.execute(sql, [str(msg_id)])
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND User = %s"
        var = [None, user, event]
        self.cursor.execute(sql, var)
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        self.cursor.execute(sql, [user, event, slotnumber])
        self.db.commit()

        return event

    def acceptSwap(self, msg_id, event, req_user, rec_user):
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
        self.cursor.execute(sql, val)
        slot_1 = self.cursor.fetchone()

        sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
        val = [event, rec_user]
        self.cursor.execute(sql, val)
        slot_2 = self.cursor.fetchone()

        sql = "DELETE FROM Message WHERE MessageID = %s;"
        self.cursor.execute(sql, [msg_id])
        self.db.commit()

        if not slot_1:
            return req_user
        if not slot_2:
            return rec_user

        sql = "UPDATE Slot SET User = Null WHERE Number = %s AND Event = %s;"
        self.cursor.execute(sql, [slot_1[0], event])
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        val = [(req_user, event, slot_2[0]), (rec_user, event, slot_1[0])]
        self.cursor.executemany(sql, val)
        self.db.commit()

        return [event, req_user, rec_user]

    def denyMessage(self, msg_id):
        """
            Deny a request
                Args:
                    msg_id (string): Message ID
                Returns:
                    (string): Type of Message (campaign/trade)
                    (list): result of deny
        """
        sql = "SELECT * FROM Message WHERE MessageID = %s;"
        self.cursor.execute(sql, [str(msg_id)])
        result = self.cursor.fetchone()

        if not result:
            return None
        if result[2] is None:
            return "campaign", self.denyReservation(msg_id, result[0], result[3])
        else:
            return "trade", self.denySwap(msg_id, result[0], result[1], result[2])

    def denyReservation(self, msg_id, event, slotnumber):
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
        self.cursor.execute(sql, [str(msg_id)])
        self.db.commit()

        sql = "UPDATE Slot SET User = %s WHERE Event = %s AND Number = %s;"
        var = [None, event, slotnumber]
        self.cursor.execute(sql, var)
        self.db.commit()

        return event

    def denySwap(self, msg_id, event, req_user, rec_user):
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
        self.cursor.execute(sql, val)
        slot_1 = self.cursor.fetchone()

        sql = "SELECT Number FROM Slot WHERE Event = %s AND User = %s;"
        val = [event, rec_user]
        self.cursor.execute(sql, val)
        slot_2 = self.cursor.fetchone()

        sql = "DELETE FROM Message WHERE MessageID = %s;"
        self.cursor.execute(sql, [msg_id])
        self.db.commit()

        if not slot_1:
            return req_user
        if not slot_2:
            return rec_user

        return event, req_user, rec_user