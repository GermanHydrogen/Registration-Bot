import mysql.connector
from mysql.connector import errors as myerror

from bot.src.main.objects.util import with_cursor


class Mark:
    def __init__(self, db):
        self.db = db

    @with_cursor
    def add_mark(self, cursor: mysql.connector.MySQLConnection.cursor, user: int, event: int, mark_type: str) -> bool:
        """
        Adds an mark to an user for an specific event
        Args:
            cursor: Database cursor
            user: user id
            event: event id
            mark_type: mark name

        Returns:
            bool: if succesfull
        """

        sql = "INSERT INTO UserEventMark (Event, User, Type) VALUES (%s, %s, %s);"
        var = [event, user, mark_type]
        try:
            cursor.execute(sql, var)
            self.db.commit()
            return True
        except myerror.IntegrityError:
            return False

    @with_cursor
    def remove_mark(self, cursor: mysql.connector.MySQLConnection.cursor,
                    user: int, event: int, mark_type: str) -> bool:
        """
        Removes an mark from an user for an specific event
        Args:
            cursor: Database cursor
            user: user id
            event: event id
            mark_type: mark name

        Returns:
            bool: if succesfull
        """
        sql = "DELETE FROM UserEventMark WHERE Event = %s AND User = %s AND Type = %s;"
        var = [event, user, mark_type]
        cursor.execute(sql, var)
        self.db.commit()

        return cursor.rowcount == 1
