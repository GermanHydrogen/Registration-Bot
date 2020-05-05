import re


async def get_list(ctx, client):
    """
    Get Slotlist from Channel
    Args:
        ctx (command object): Command
        client (client object): Client

    Returns:
        (string), (message object): Slotliste, Message of the Slotlist
    """
    channel = ctx.message.channel
    async for x in channel.history(limit=1000):
        msg = x.content
        if re.search("Slotliste", msg) and x.author == client.user:
            return msg, x
















