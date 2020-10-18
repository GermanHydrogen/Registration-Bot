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

    def get_slots(self, channel_id, intersection = ''):
        """
                Gets all taken slots of the channel
                If intersection is given, K.I.A (marked in the intersection channel) are removed
                Args:
                    channel_id (string): Server Channel
                    intersection (string): Server Channel to intersect with
                Returns:
                    (list): [(user, slot-number, description)]

           """
        if intersection == '':
            sql = "SELECT User, Number, Description FROM Slot WHERE Event = %s AND Description != %s AND User IS NOT NULL;"
            self.cursor.execute(sql, [str(channel_id), 'Reserve'])
        else:
            sql = "SELECT User, Number, Description FROM Slot s1 WHERE Event = %s AND Description != %s AND User IS NOT NULL " \
                  "AND NOT EXISTS(SELECT * FROM Slot s2 WHERE Event = %s AND s1.Number = s2.Number AND s2.User = 'A00000000000000000');"
            self.cursor.execute(sql, [str(channel_id), 'Reserve', str(intersection)])

        return self.cursor.fetchall()

    def get_slot_description(self, event, user):
        """
               Gets all taken slots of the channel
               Args:
                    event (string): Server Channel/ Event id
                    user (string): User ID

                Returns:
                    (string): '#[num] [description]'


        """
        sql = "SELECT Number, Description FROM Slot WHERE Event = %s AND User = %s"
        self.cursor.execute(sql, [str(event), str(user)])

        result = self.cursor.fetchone()

        if result:
            return '#' + str(result[0]) + " " + str(result[1])
        else:
            return None
