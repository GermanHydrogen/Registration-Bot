import asyncio

import discord
import mysql.connector
import datetime as dt

from config.loader import cfg
from datetime import datetime, timedelta

from src.main.objects.util import with_cursor


class EditLocale:
    def __init__(self, client, logger, lang, db):
        self.lang = lang
        self.client = client
        self.logger = logger
        self.db = db

    # TODO: Duplicate with src.util.Util.get_event_date
    @with_cursor
    def get_event(self, cursor: mysql.connector.MySQLConnection.cursor, event_id: int) -> tuple:
        """
        Gets the event date and time
        Args:
            cursor: Database cursor
            event_id: ID of the event
        Returns:
            date and time
        """
        sql = "SELECT Date, Time FROM Event WHERE ID = %s;"
        cursor.execute(sql, [event_id])
        result = cursor.fetchone()
        return result

    @with_cursor
    def update_event(self, cursor: mysql.connector.MySQLConnection.cursor, event_id, name, date, time="") -> None:
        """
        Updates Name, date and time of an event
        Args:
            cursor: Database cursor
            event_id: ID of the event
            name: (New) Name of the event
            date: (New) Date of the event
            time: (New) Time of the event
        """
        if time == "":
            sql = "UPDATE Event SET Name = %s, Date = %s WHERE ID = %s;"
            var = [name, date, event_id]
        else:
            sql = "UPDATE Event SET Name = %s, Date = %s, Time = %s WHERE ID = %s;"
            var = [name, date, time, event_id]

        cursor.execute(sql, var)
        self.db.commit()
        return cursor.rowcount

    @with_cursor
    def update_notify(self, cursor: mysql.connector.MySQLConnection.cursor,
                      event_id: int, old_time: str, new_time: str) -> bool:
        """
        Updates the time of notifications of an event
        Args:
            cursor: Database cursor
            event_id: Event ID
            old_time: Old event time
            new_time: New event time

        Returns:
            if successful
        """
        sql = "UPDATE Notify SET time= ADDTIME(%s, TIMEDIFF(time, %s))   WHERE Event = %s;"
        var = [new_time, old_time, event_id]
        cursor.execute(sql, var)
        self.db.commit()

        return cursor.rowcount != 0

    @with_cursor
    def delta_event_time(self, cursor: mysql.connector.MySQLConnection.cursor,
                         event_id: int, time: str) -> datetime:
        """
        Calculates datetime for notification
        Args:
            cursor: Database cursor
            event_id: ID of an event
            time: timedelta

        Returns:
            (datetime): datetime if successfull, when not False
        """
        sql = "SELECT concat(Date,' ',Time) as date FROM Event WHERE ID = %s;"
        cursor.execute(sql, [str(event_id)])
        result = cursor.fetchone()

        if not result:
            return False

        result = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        delta = timedelta(hours=int(time))

        return result - delta

    @with_cursor
    def create(self, cursor: mysql.connector.MySQLConnection.cursor,
               event_id: str, user_id: str, time: int = cfg["std_notify"]) -> None:
        """
        Creates notification
        Args:
            cursor: Database cursor
            event_id: ID of an event
            user_id: User ID
            time: timedelta
        """
        if not str(user_id).isdigit():
            return

        time = self.delta_event_time(event_id, time)

        sql = "SELECT * FROM Notify WHERE Event = %s AND User = %s;"
        var = [event_id, str(user_id)]
        cursor.execute(sql, var)

        if cursor.fetchall():
            sql = "UPDATE Notify SET Enabled = True WHERE Event = %s AND User = %s;"
            var = [event_id, str(user_id)]
            cursor.execute(sql, var)
            self.db.commit()

        else:
            sql = "INSERT IGNORE INTO Notify (Event, User, Time) VALUES (%s, %s, %s);"
            var = [event_id, str(user_id), time]

            cursor.execute(sql, var)
            self.db.commit()

    @with_cursor
    def toggle(self, cursor: mysql.connector.MySQLConnection.cursor,
               event_id: int, user_id: int, overwrite: bool = False) -> bool:
        """
        Toggles notification for a specific event
        Args:
            cursor: Database cursor
            event_id: ID of an event
            user_id: User ID
            overwrite: disable notification for event

        Returns:
            Currents notification status if successfull, when not None
        """
        sql = "SELECT Enabled FROM Notify WHERE Event=%s AND User=%s;"
        var = [str(event_id), str(user_id)]
        cursor.execute(sql, var)
        result = cursor.fetchone()

        if not result:
            return None

        if not overwrite:
            sql = "UPDATE Notify SET Enabled = NOT Enabled WHERE Event=%s AND User=%s;"
        else:
            sql = "UPDATE Notify SET Enabled = False WHERE Event=%s AND User=%s;"

        cursor.execute(sql, var)
        self.db.commit()

        return not result[0]

    @with_cursor
    def change_time(self, cursor: mysql.connector.MySQLConnection.cursor,
                    event_id: str, user_id: str, time: int) -> datetime:
        """
        Changes notification time
        Args:
            cursor:
            event_id: ID of an event
            user_id: User ID
            time: timedelta

        Returns:
            if successfull a datetime
        """
        time = self.delta_event_time(event_id, time)

        sql = "UPDATE Notify SET Time = %s WHERE Event = %s AND User = %s;"
        var = [time, str(event_id), str(user_id)]

        cursor.execute(sql, var)
        self.db.commit()

        if cursor.rowcount == 1:
            return time
        else:
            return None

    @with_cursor
    def get_all_notify(self, cursor: mysql.connector.MySQLConnection.cursor) -> []:
        """
        Gets all notifications which should be triggered today
        """
        sql = "SELECT n.User, n.Time, n.Event FROM Notify n, User u \
                        WHERE n.User = u.ID AND u.Notify AND n.Enabled AND n.Time >= CURDATE();"
        cursor.execute(sql)
        return cursor.fetchall()

    @with_cursor
    async def notify(self, cursor: mysql.connector.MySQLConnection.cursor, event, user_id, delay):
        """
            Calculates datetime for notification
                Args:
                    cursor: Database cursor
                    event: ID of an event
                    user_id: User ID
                    delay: delay in sec.

        """

        await asyncio.sleep(delay)

        user = self.client.get_user(int(user_id))
        if user:
            sql = "SELECT Time FROM Notify WHERE Event = %s AND User = %s"
            cursor.execute(sql, [event, user_id])
            result = cursor.fetchall()

            if not result:
                return

            now = dt.datetime.now()
            delta = (result[0][0] - now).total_seconds()

            if abs(delta) > 1200:
                return

            sql = "SELECT Name, Time FROM Event WHERE ID = %s;"
            cursor.execute(sql, [event])
            result = cursor.fetchone()

            guild = self.client.get_guild(int(cfg['guild']))
            nickname = guild.get_member(int(user_id)).display_name
            try:
                await user.send(self.lang["notify_global"]["noti"].format(nickname, str(result[0]), str(result[1])))
            except discord.errors.Forbidden:
                log = "User: " + str(nickname).ljust(20) + "\t"
                log += "Channel:" + str(event).ljust(20) + "\t"
                log += "Command: " + "Notify: discord.errors.Forbidden".ljust(20) + "\t"
                self.logger.log(log)