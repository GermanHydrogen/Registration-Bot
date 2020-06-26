class Util:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor
        
    def get_event_date(self, channel_id):
        """
                Gets the date of an event
                Args:
                    channel_id (string): Server Channel

                Returns:
                    (string): date

        """

        sql = "SELECT Date FROM Event WHERE ID = %s;"
        self.cursor.execute(sql, [str(channel_id)])
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def get_event_id(self, name):
        """
                Gets the id of an event
                Args:
                    name (string): Eventname (e.g. 2020-02-13-arma3)

                Returns:
                    (string): id

           """

        sql = "SELECT ID FROM Event WHERE Name = %s;"
        self.cursor.execute(sql, [str(name)])
        result = self.cursor.fetchone()

        if result:
            return result[0]
        else:
            return None

    def get_slots(self, channel_id):
        """
                Gets all taken slots of the channel
                Args:
                    channel_id (string): Server Channel

                Returns:
                    (list): [(user, slot-number, description)]

           """
        sql = "SELECT User, Number, Description FROM Slot WHERE Event = %s AND Description != %s AND User IS NOT NULL;"
        self.cursor.execute(sql, [str(channel_id), 'Reserve'])

        return self.cursor.fetchall()