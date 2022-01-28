import discord
from discord.ext import commands

from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig, is_administrator
from util import send_msg


class Admin(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, guild_config: RoleConfig):
        # Meta Information for the help command
        self.description = "All commands accessible with the defined admin role or admin permission."

        self.client = client
        self.state = state

        self.guildConfig = guild_config

    @commands.command(name="setModeratorRole",
                      usage="[role name]",
                      help="Defines the role, which has access to the moderator commands.\n"
                           "User which got the admin permission have access to all commands.",
                      brief="Define the moderator role for this guild.")
    @commands.guild_only()
    @is_administrator
    async def set_moderator_role(self, ctx, *, role_name: str):
        guild = ctx.message.guild

        role = self.guildConfig.set_moderator_role(self.client, guild, str(role_name))

        await send_msg(ctx, f"Successfully set {role} as the moderator role.")

    @commands.command(name="setAdminRole",
                      usage="[role name]",
                      help="Defines the role, which has access to the admin commands.\n"
                      "User which got the admin permission have access to all commands.",
                      brief="Define the admin role for this guild.")
    @commands.guild_only()
    @is_administrator
    async def set_admin_role(self, ctx, *, role_name: str):
        guild = ctx.message.guild

        role = self.guildConfig.set_admin_role(self.client, guild, str(role_name))

        await send_msg(ctx, f"Successfully set {role} as the admin role.")

    @commands.command(name='setTypeConfig',
                      usage="[channel suffix] [required role name] [opt: newbie role name] [opt: soft <True|False>]",
                      help="This command can limit the access to a event type by user roles.\n\n"
                           "- The type identifier is"
                           "the channel name suffix, so the last word of the channel name is used. "
                           "So for example in the case of the channel name: '2021-12-24-arma3', "
                           "'arma3' would be the suffix.\n"
                           "- The required role, is the role which is required to join the event.\n"
                           "- The newbie role, is the role, which is given to all users, which try to join the event"
                           "but dont have the required role.\n"
                           "- The soft option can be set to True, if a newbie role was given. If set to True, the "
                           "required role is not necessary to join, but all users, which dont have the required role, "
                           "are given the newbie role when they join.",
                      brief="Sets the config for a event type for this guild."
                      )
    @commands.guild_only()
    @is_administrator
    async def set_type_config(self, ctx, game_name: str, required_role_name: str, newbie_role_name=None, soft=False):
        self.guildConfig.set_game(self.client, ctx.guild, game_name.lower(), required_role_name, newbie_role_name, bool(soft))
        await send_msg(ctx, f"The game {game_name} was successfully added to the config.")

    @commands.command(name='viewConfig',
                      usage="",
                      help="Displays the bot config of this guild.",
                      brief="Displays the bot config of this guild.")
    @commands.guild_only()
    @is_administrator
    async def view_config(self, ctx):
        await ctx.send(self.guildConfig.print_config(ctx.message.guild))

        await ctx.message.delete()