from mysql.connector import errors as myerror


class Mark:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def addMark(self, user, event, mark_type):
        """
        Adds an mark to an user for an specific event
        Args:
            user (int): user id
            event (int): event id
            mark_type (string): mark name

        Returns:
            bool: if succesfull
        """

        sql = "INSERT INTO UserEventMark (Event, User, Type) VALUES (%s, %s, %s);"
        var = [event, user, mark_type]
        try:
            self.cursor.execute(sql, var)
            self.db.commit()
            return True
        except myerror.IntegrityError:
            return False

    def removeMark(self, user, event, mark_type):
        """
        Removes an mark from an user for an specific event
        Args:
            user (int): user id
            event (int): event id
            mark_type (string): mark name

        Returns:
            bool: if succesfull
        """
        sql = "DELETE FROM UserEventMark WHERE Event = %s AND User = %s AND Type = %s;"
        var = [event, user, mark_type]
        self.cursor.execute(sql, var)
        self.db.commit()

        return self.cursor.rowcount == 1
