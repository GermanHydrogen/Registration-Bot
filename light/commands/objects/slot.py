class SlotTaken(Exception):
    pass


class SlotNotTaken(Exception):
    pass


class SlotForbidden(Exception):
    pass


class Slot:
    def __init__(self):
        self.group = -1

        self.number = ""
        self.desc = ""
        self.user = ""

    def from_data(self, number: str, description: str, user=""):
        """
        Construct slot
        :param number: Slotnumber
        :param description: Title
        :param user: User
        :return: self
        """
        # Check if number is valid
        if not number.isnumeric():
            raise TypeError

        self.number = number
        self.desc = description
        self.user = user

        return self

    def from_line(self, line: str):
        """
        Constructs slot from slotlist line
        :param line: slotlist line
        :return: self
        """
        self.number = ""
        line = line.replace("**", "").split("-")

        self.user = ("-".join(line[1:]).replace("**", "")).strip()
        line = line[0]

        for x in line[1:]:
            if x.isdigit():
                self.number += x
            else:
                break

        if self.number == "":
            raise ValueError

        self.desc = line[len(self.number) + 1:].strip()

        return self

    def slot_user(self, user_name: str):
        """
        Slots user
        :param user_name: user name
        :return:
        """
        if self.user != "" and user_name != self.user:
            raise SlotTaken
        else:
            self.user = user_name

    def unslot_user(self, user_name: str):
        """
        Unslots user
        :param user_name: user nam
        :return:
        """
        if self.user == "":
            raise SlotNotTaken
        elif self.user != user_name:
            raise SlotForbidden
        else:
            self.user = ""

    def __str__(self):
        if self.number == "":
            raise ValueError
        else:
            return f"#{self.number} {self.desc} - {self.user}"
