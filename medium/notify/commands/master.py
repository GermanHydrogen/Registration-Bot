from discord.ext import commands


class Global(commands.Cog, name='Reminder'):
    def __init__(self, client, lang, logger, db, cursor):

        self.client = client
        self.lang = lang
        self.logger = logger

        self.db = db
        self.cursor = cursor

    def toggle(self, user):
        """
            Toggles notification globally
                Args:
                    user(string): User ID

                Returns:
                    (Bool): Currents notification status if successfull, when not None
        """
        sql = "SELECT Notify FROM User WHERE ID = %s;"
        var = [str(user)]
        self.cursor.execute(sql, var)

        result = self.cursor.fetchone()

        if not result:
            return None

        sql = "UPDATE User SET Notify = NOT Notify WHERE ID = %s;"

        self.cursor.execute(sql, var)
        self.db.commit()

        return not result[0]

    @commands.command(name="toggleReminderGlobal",
                      usage="",
                      help="Enables/Disables if you get notified for a event at this guild. If you only want to change"
                           "the reminding option for this event, please use the command toggleReminder.",
                      brief="Enables/Disables if you get notified for a event at this guild.")
    @commands.guild_only()
    async def toggleReminderGlobal(self, ctx):

        author = ctx.message.author
        channel = ctx.message.channel

        result = self.toggle(author.id)

        if result is not None:

            result = ["nicht mehr", "wieder"][result]

            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_global"]["toggle"]["channel"]["suc"], delete_after=5)
            await author.send(self.lang["notify_global"]["toggle"]["private"].format(result))
        else:
            await channel.send(ctx.message.author.mention + " " +
                               self.lang["notify_global"]["toggle"]["channel"]["fail"], delete_after=5)

        await ctx.message.delete()
