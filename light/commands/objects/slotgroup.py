class SlotGroup:
    def __init__(self, prim: int, title="", before=""):
        """
        The Slotgroup is the meta container for all slots.
        It consists of a primary identifier, a title which is
        displayed and a string which is played before the slotlist is
        displayed. The before string is mainly used for line feeds.
        :param prim:
        :param title:
        :param before:
        """
        self.prim = prim
        self.title = title
        self.before = before

    def __str__(self):
        return f"{self.before}{self.title}"
