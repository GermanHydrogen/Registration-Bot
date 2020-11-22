from functools import lru_cache
from discord import utils as dutil
from config.loader import cfg


class Util:
    def __init__(self, client, db, cursor):
        self.client = client
        self.db = db
        self.cursor = cursor

        self.guild = None

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

    @lru_cache(maxsize=None)
    def get_emoji(self, name=None, dict_name=None):
        if name is None and dict_name is not None:
            if dict_name in cfg['marks'].keys():
                name = cfg['marks'][dict_name]
            else:
                return None

        if not self.guild:
            self.guild = self.client.get_guild(int(cfg['guild']))

        return dutil.get(self.guild.emojis, name=name)
