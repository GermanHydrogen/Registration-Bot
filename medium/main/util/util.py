class Util:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def get_channel_author(self, channel):
        """
            Gets the author of the channel
            Args:
                channel (channel): Server Channel

            Returns:
                (member object)

        """
        sql = "SELECT Author FROM Event WHERE ID = %s;"
        self.cursor.execute(sql, [channel.id])

        result = self.cursor.fetchone()

        if result:
            return channel.guild.get_member(int(result[0]))
        else:
            return None
