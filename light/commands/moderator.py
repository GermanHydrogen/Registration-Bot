import discord
from discord.ext import commands

from commands.objects.state import ClientState
from commands.objects.guildconfig import RoleConfig, is_moderator


class Moderator(commands.Cog):
    def __init__(self, client: discord.Client, state: ClientState, guild_config: RoleConfig):
        # Meta Information for the help command
        self.description = "All commands accessible with the defined moderator role or admin permission."

        self.client = client
        self.state = state

        self.guildConfig = guild_config

    @commands.command(name="create",
                      usage="",
                      help="Creates an event in the channel from your 'slotlist message'.\n"
                           "This 'slotlist message' has to begin with the string '>Slotlist<'.\n"
                           "Slots have to be declared with the format: #[number] [slot description] - [opt: Username], "
                           "while the number can contain leading zeros, but has to be unique for every event.",
                      brief="Creates an event in the channel.")
    @commands.guild_only()
    @is_moderator
    async def create(self, ctx):  # makes the slotlist editable for the bot
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, ctx.message.author, self.client.user, True)
        await slotlist.write(channel, False)

        await ctx.message.author.send(f"The event **{channel.name}** was successfully created!")

        await ctx.message.delete()

    @commands.command(name="forceSlot",
                      usage="[number] [username]",
                      help="Registers a username for the given slot. The username argument, doesnt have to be a "
                           "username, so it can also be used to block a slot for example.",
                      brief="Registers a user for a given slot.")
    @commands.guild_only()
    @is_moderator
    async def force_slot(self, ctx, slot_number: int, *, user_name: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.slot(slot_number, user_name)
        await slotlist.write()

        await ctx.send(f'{author.mention} {user_name} was successfully slotted.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="forceUnslot",
                      usage="[username]",
                      help="Withdraws a given user from the event.",
                      brief="Withdraws a given user from the event.")
    @commands.guild_only()
    @is_moderator
    async def force_unslot(self, ctx, *, user_name: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.unslot(user_name)
        await slotlist.write()

        await ctx.send(f'{author.mention} {user_name} was successfully slotted.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="editSlot",
                      usage="[number] [description]",
                      help="Edits the description of a slot given by its number.",
                      brief="Edits the description of a given slot.")
    @commands.guild_only()
    @is_moderator
    async def edit_slot(self, ctx, number: str, *, description: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.edit_slot(number, description)
        await slotlist.write()

        await ctx.send(f'The description of slot #{number} was changed to {description}.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="delSlot",
                      usage="[number]",
                      help="Deletes a slot given by its number.",
                      brief="Deletes a given slot.")
    @commands.guild_only()
    @is_moderator
    async def del_slot(self, ctx, number: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.remove_slot(number)
        await slotlist.write()

        await ctx.send(f'The slot #{number} was successfully removed.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="addSlot",
                      usage="[number] [group] [description]",
                      help="Adds a new slot to a slot-group given by its title or index (counting from 0).\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "If you want to refer to the group by its title and the title contains white-spaces "
                           "you have to use quotation marks around the group argument.\n",
                      brief="Adds a new slot to a slot-group.")
    @commands.guild_only()
    @is_moderator
    async def add_slot(self, ctx, number: str, group: str, description: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.new_slot(number, group, description)
        await slotlist.write()

        await ctx.send(f'The slot #{number} {description} was successfully created.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="addGroup",
                      usage="[index] [title]",
                      help="Adds a new slot-group.\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "The index argument, defines where the slot-group is placed in the order of the existing"
                           "slot-groups (counting from 0).\n"
                           "Slots can be added later with the addSlot command.",
                      brief="Adds a new slot-group.")
    @commands.guild_only()
    @is_moderator
    async def add_group(self, ctx, index: int, *, description: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.new_group(index, description)
        await slotlist.write()

        await ctx.send(f'Added group {description} successfully.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="editGroup",
                      usage="[Identifier] [New Description]",
                      help="Edits a slot-group identified by its name or index (counting from 0).\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "The index argument, defines where the slot-group is placed in the order of the existing"
                           "slot-groups (counting from 0).\n"
                           r"New line in the new description can be added with \n",
                      brief="Edits the name of an slot-group.")
    @commands.guild_only()
    @is_moderator
    async def edit_group(self, ctx, description: str, new_description: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        new_description = new_description.replace(r"\n", "\n")
        slotlist.edit_group(description, new_description)
        await slotlist.write()

        await ctx.send(f'The group {description} was changed to {new_description}.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="delGroup",
                      usage="[Identifier]",
                      help="Deletes a slot-group identified by its name or index (counting from 0).\n"
                           "A slot-group is defined as a paragraph of slots which can have a multi-line title.\n"
                           "The index argument, defines where the slot-group is placed in the order of the existing"
                           "slot-groups (counting from 0).\n"
                           "All slots of the slot-group are also deleted.",
                      brief="Deletes a slot-group.")
    @commands.guild_only()
    @is_moderator
    async def del_group(self, ctx, *, description: str):
        author = ctx.message.author
        channel = ctx.message.channel

        slotlist = await self.state.get_slotlist(channel, author, self.client.user)
        slotlist.remove_group(description)
        await slotlist.write()

        await ctx.send(f'The group {description} was successfully deleted.', delete_after=5)

        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass