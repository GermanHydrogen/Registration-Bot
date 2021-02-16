class SlotGroup:
    def __init__(self, prim: int, title="", before=""):
        self.prim = prim
        self.title = title
        self.before = before

    def __str__(self):
        return f"{self.before}{self.title}"
