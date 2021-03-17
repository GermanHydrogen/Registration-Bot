import discord
from discord.ext import commands

from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig, is_administrator
from util import send_msg


class Admin(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, lang: dict, guild_config: RoleConfig):
        self.client = client
        self.state = state
        self.lang = lang

        self.guildConfig = guild_config

    @commands.command(name='setModeratorRole', hidden=True, description="Set the moderator role")
    @commands.guild_only()
    @is_administrator
    async def set_moderator_role(self, ctx, role_name: str):
        guild = ctx.message.guild

        role = self.guildConfig.set_moderator_role(self.client, guild, str(role_name))

        await send_msg(ctx, f"Successfully set {role} as the moderator role.")

    @commands.command(name='setAdminRole', hidden=True, description="Set the admin role")
    @commands.guild_only()
    @is_administrator
    async def set_admin_role(self, ctx, role_name: str):
        guild = ctx.message.guild

        role = self.guildConfig.set_admin_role(self.client, guild, str(role_name))

        await send_msg(ctx, f"Successfully set {role} as the admin role.")

    @commands.command(name='setGameConfig', hidden=True, description="Set a game config")
    @commands.guild_only()
    @is_administrator
    async def set_game_config(self, ctx, game_name: str, required_role_name=None, newbie_role_name=None, soft=False):
        self.guildConfig.set_game(self.client, ctx.guild, game_name.lower(), required_role_name, newbie_role_name, bool(soft))
        await send_msg(ctx, f"The game {game_name} was successfully added to the config.")

    @commands.command(name='viewConfig', hidden=True, description="Prints the config of your guild")
    @commands.guild_only()
    @is_administrator
    async def view_config(self, ctx):
        await ctx.send(self.guildConfig.print_config(ctx.message.guild))

        await ctx.message.delete()