from config.loader import cfg
from datetime import datetime, timedelta
from notify.util.handler import Handler


class EditLocale:
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor

    def deltaEventTime(self, event, time):
        """
            Calculates datetime for notification
                Args:
                    event(string): ID of an event
                    time(int): timedelta

                Returns:
                    (datetime): datetime if successfull, when not False
        """
        sql = "SELECT concat(Date,' ',Time) as date FROM Event WHERE ID = %s;"
        self.cursor.execute(sql, [str(event)])
        result = self.cursor.fetchone()

        if not result:
            return False

        result = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        delta = timedelta(hours=int(time))

        return result - delta

    def create(self, event, user, time=cfg["std_notify"]):
        """
            Creates notification
                Args:
                    event(string): ID of an event
                    user(string): User ID
                    time(int): timedelta

        """
        if not str(user).isdigit():
            return

        time = self.deltaEventTime(event, time)

        sql = "INSERT IGNORE INTO Notify (Event, User, Time) VALUES (%s, %s, %s);"
        var = [event, str(user), time]

        self.cursor.execute(sql, var)
        self.db.commit()

    def toggle(self, event, user, overwrite = False):
        """
            Toggles notification for a specific event
                Args:
                    event(string): ID of an event
                    user(string): User ID
                    overwrite (Bool): disable notification for event

                Returns:
                    (Bool): Currents notification status if successfull, when not None
        """
        sql = "SELECT Enabled FROM Notify WHERE Event=%s AND User=%s;"
        var = [str(event), str(user)]
        self.cursor.execute(sql, var)
        result = self.cursor.fetchone()

        if not result:
            return None

        if not overwrite:
            sql = "UPDATE Notify SET Enabled = NOT Enabled WHERE Event=%s AND User=%s;"
        else:
            sql = "UPDATE Notify SET Enabled = False WHERE Event=%s AND User=%s;"

        self.cursor.execute(sql, var)
        self.db.commit()

        return not result[0]

    def changeTime(self, event, user, time):
        """
            Changes notification time
                Args:
                    event(string): ID of an event
                    user(string): User ID
                    time(int): timedelta

                Returns:
                    (Bool): if successfull
        """
        time = self.deltaEventTime(event, time)

        sql = "UPDATE Notify SET Time = %s WHERE Event = %s AND User = %s;"
        var = [time, str(event), str(user)]

        self.cursor.execute(sql, var)
        self.db.commit()

        if self.cursor.rowcount == 1:
            return time
        else:
            return None
