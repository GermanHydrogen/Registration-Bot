import os
import yaml
from functools import wraps
import discord
from discord.ext.commands import errors as derrors

from util import CustomParentException


class ConfigAlreadyExists(Exception):
    pass


class GuildNotExisting(Exception):
    """
    Raised if a requested config for a guild is not found
    """

    def __init__(self):
        super().__init__()
        self.message = "A config for this guild does not exist at this point!"


class RoleNotFound(CustomParentException):
    """
    Raised if a configured role is invalid
    """
    def __init__(self, game: str, type: str):
        super().__init__()
        self.message = f"The set {type} role for {game} is invalid. Please contact your local admin"


class CannotAddRole(CustomParentException):
    """
    Raised if a configured role is invalid
    """
    def __init__(self):
        super().__init__()
        self.message = f"Cannot add role, because the role is higher in the hierarchy as the bot!"


class InvalidRole(CustomParentException):
    """
    Raised if a configured role is invalid
    """
    def __init__(self, role):
        super().__init__()
        self.message = f"Could not add {role}. Please contact your local admin"


class InvalidGameConfig(CustomParentException):
    """
    Raised if a configured role is invalid
    """
    def __init__(self):
        super().__init__()
        self.message = f"Invalid config. If you want soft lock mode, then please give a newbie role." \
                       f"If you want to "


def validate_role(client: discord.Client, guild: discord.Guild, role_name: str, overwrite=False) -> discord.Role:
    """
    Gets the role object from the id and validates if the role is settable by the bot
    :param client: Bot client
    :param guild: Guild of the role
    :param role_name: Role name of the role to get
    :param overwrite: Overwrites the position check
    :return:
    """
    if (role := discord.utils.get(guild.roles, name=role_name)) is None:
        return None

    client_member = guild.get_member(client.user.id)
    if client_member.top_role.position < role.position and not overwrite:
        raise CannotAddRole

    return role


class GuildConfig:
    def __init__(self, file_path: str):
        """https://www.youtube.com/watch?v=ihXu4BwvOx4
        Class to manage guild configs
        :param file_path: file path of configuration file
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError

        self.data = {}
        self.path = file_path

    def load(self):
        """
        Load configuration from file
        :return:
        """
        with open(self.path, 'r') as ymlFile:
            self.data = yaml.safe_load(ymlFile)
            if self.data is None:
                self.data = {}

    def write(self):
        """
        Write configuration to file
        :return:
        """
        with open(self.path, 'w') as ymlFile:
            yaml.dump(self.data, ymlFile)


class RoleConfig(GuildConfig):
    """
    <guild_id>:
        moderator_role: <moderator_role_id>
        admin_role: <admin_role_id>
        games:
            <game_name>:
                soft: <True | False>
                required: <required_role_id>
                newbie: <newbie_role_id>
    """
    def __add_structure(self, guild: discord.guild) -> None:
        """
        Adds the basic config structure for a guild
        :param guild: Guild the config is for
        :return:
        """
        if guild.id in self.data:
            return

        self.data[guild.id] = {'moderator_role': 0, 'admin_role': 0, 'games': {}}
        self.write()

    def set_game(self, client: discord.Client, guild: discord.Guild, game: str, required: str, newbie=None, soft=False) -> None:
        """
        Adds the basic config structure for a game
        :param client: Bot client
        :param guild: Guild to add the structure for
        :param game: Game to add the structure for
        :param required: Role which is required
        :param newbie: Role which is given when the user has not the required role
        :param soft: If the game is only soft locked (user without required can join, but gets the newbie role)
        :return:
        """
        self.__add_structure(guild)

        if game not in self.data[guild.id]['games']:
            self.data[guild.id]['games'][game] = {'soft': soft}
        else:
            self.data[guild.id]['games'][game]['soft'] = soft

        if required is not None:
            required = validate_role(client, guild, required)
            self.data[guild.id]['games'][game]['required'] = required.id

        if newbie is not None:
            newbie = validate_role(client, guild, newbie)
            self.data[guild.id]['games'][game]['newbie'] = newbie.id
        elif (newbie is None and soft) or (newbie is not None and not soft):
            raise InvalidGameConfig

        self.write()

    def set_moderator_role(self, client: discord.Client, guild: discord.guild, role_name: str) -> discord.Role:
        """
        Sets the moderator role for a guild.
        :param client: Bot client
        :param guild: Guild to add the config to
        :param role_name: Role id of the role to add
        :return: Role object which was found for the given id
        """
        role = validate_role(client, guild, role_name, True)
        self.__add_structure(guild)

        self.data[guild.id]['moderator_role'] = role.id
        self.write()

        return role

    def set_admin_role(self, client: discord.Client, guild: discord.guild, role_name: str) -> discord.Role:
        """
        Sets the admin role for a guild.
        :param client: Bot client
        :param guild: Guild to add the config to
        :param role_name: Role id of the role to add
        :return: Role object which was found for the given id
        """
        role = validate_role(client, guild, role_name, True)
        self.__add_structure(guild)

        self.data[guild.id]['admin_role'] = role.id
        self.write()
        return role

    def is_moderator(self, user: discord.Member) -> bool:
        """
        Checks if the user has the configured moderator role.
        Is overwritten by the administrator permission.
        :param user: Discord user to check
        :return:
        """

        # Overwrite with the administrator permission
        if user.guild_permissions.administrator:
            return True

        try:
            role_id = int(self.data[user.guild.id]['moderator_role'])
            return discord.utils.get(user.roles, id=role_id) is not None

        except KeyError and ValueError:     # if no role is configured
            return False

    def is_administrator(self, user: discord.Member) -> bool:
        """
        Checks if the user has the configured admin role.
        Is overwritten by the administrator permission.
        :param user: Discord user to check
        :return:
        """

        # Overwrite with the administrator permission
        if user.guild_permissions.administrator:
            return True

        try:
            role_id = int(self.data[user.guild.id]['admin_role'])
            return discord.utils.get(user.roles, id=role_id) is not None

        except KeyError and ValueError:  # if no role is configured
            return False

    def has_game_role(self, user: discord.Member, game: str) -> bool:
        """
        Checks if the user has the permission to slot for the game.
        :param user: Discord user to check
        :param game: Name of the game to check
        :return:
        """

        try:
            role_id = int(self.data[user.guild.id]['games'][game]['required'])
            return discord.utils.get(user.roles,
                                     id=role_id) is not None

        except KeyError or ValueError:  # if no role is configured
            return True

    def is_soft_locked(self, guild: discord.guild, game: str) -> bool:
        """
        Checks if a game is soft locked.
        :param guild: Guild for which the check is for
        :param game: Name of the game to check
        :return:
        """

        try:
            return self.data[guild.id]['games'][game]['soft']
        except KeyError or ValueError:  # if no role is configured
            return False

    async def set_user_newbie(self, user: discord.Member, game: str) -> None:
        """
        Gives the user the newbie role if it is set
        :param user: Discord user to give the role to
        :param game: Name of the game for which the newbie role is defined
        :return:
        """

        try:
            role_id = self.data[user.guild.id]['games'][game]['newbie']
            role = user.guild.get_role(role_id)
        except KeyError or ValueError:  # if no role is configured-
            return

        if role is None:
            raise RoleNotFound(game, 'newbie')

        try:
            await user.add_roles(role)
        except discord.Forbidden:
            raise InvalidRole(role)

    def print_config(self, guild: discord.guild) -> str:
        """
        Returns a overview of the config of the guild
        :param guild: Guild to return the config to
        :return:
        """
        def print_role(role_id: int, name: str) -> str:
            """
            Returns a string containing the state of the role
            :param role_id: Role id of the role
            :param name: Category name of the role
            :return:
            """
            if role_id == 0:
                return f"{name} Role: Not defined\n"
            elif (role := guild.get_role(role_id)) is not None:
                return f"{name} Role: {role}\n"
            else:
                return f"{name} Role: Invalid\n"

        try:
            config = self.data[guild.id]
        except KeyError:
            raise GuildNotExisting

        output = "**__Server Config__**\n\n"
        output += print_role(config['moderator_role'], "Moderator")
        output += print_role(config['admin_role'], "Admin")

        for name, game in config['games'].items():
            output += "\n"
            output += f"**{name}:**\n"
            output += f"\tSoft locked: {game['soft']}\n"
            try:
                output += "\t" + print_role(game['required'], 'Required')
            except KeyError:
                pass

            try:
                output += "\t" + print_role(game['newbie'], 'Newbie')
            except KeyError:
                pass

        return output


def is_moderator(func):
    """
    Decorator to check if the caller has the moderator role.
    Raises discord.ext.commands.errors.MissingRole, if it has not.
    :param func:
    :return:
    """
    @wraps(func)
    async def new_func(*args, **kwargs):
        guild_config = args[0].guildConfig
        author = args[1].author
        if not guild_config.is_moderator(author):
            raise derrors.MissingRole("Moderator")
        else:
            return await func(*args, **kwargs)

    return new_func


def is_administrator(func):
    """
    Decorator to check if the caller has the admin role.
    Raises discord.ext.commands.errors.MissingRole, if it has not.
    :param func:
    :return:
    """
    @wraps(func)
    async def new_func(*args, **kwargs):
        guild_config = args[0].guildConfig
        author = args[1].author
        if not guild_config.is_administrator(author):
            raise derrors.MissingRole("Admin")
        else:
            return await func(*args, **kwargs)

    return new_func
