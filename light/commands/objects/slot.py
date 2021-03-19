from util import CustomParentException


class SlotTaken(CustomParentException):
    def __init__(self):
        """
        Raised if a slot is taken
        """
        super().__init__()
        self.message = "The slot is already taken"


class SlotNotTaken(CustomParentException):
    def __init__(self):
        """
        Raised if a slot is not taken
        """
        super().__init__()
        self.message = "The slot is empty"


class SlotForbidden(CustomParentException):
    def __init__(self):
        """
        Raised if a operation on a slot is forbidden
        """
        super().__init__()
        self.message = "This slot can't be accest by this command"


class Slot:
    def __init__(self):
        """
        A Slot is the main component of a slotlist and consists of an
        number (unique per slotlist), description and user, which is
        slotted in this slot.
        Every slot belongs to a group.

        A slot can be directly created by a the data, or
        constructed with a String with the format #[number] [description] - [user]
        """
        self.group = -1

        self.number = ""
        self.desc = ""
        self.user = ""

    def from_data(self, number: str, description: str, user="") -> 'Slot':
        """
        Construct slot
        :param number: Slotnumber
        :param description: Title
        :param user: User
        :return: Slot
        """
        # Check if number is valid
        if not number.isnumeric():
            raise TypeError

        self.number = number
        self.desc = description
        self.user = user

        return self

    def from_line(self, line: str) -> 'Slot':
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

    def slot_user(self, user_name: str) -> None:
        """
        Slots user
        :param user_name: user name
        :return: None
        """
        if self.user != "" and user_name != self.user:
            raise SlotTaken
        else:
            self.user = user_name

    def unslot_user(self, user_name: str) -> None:
        """
        Unslots user
        :param user_name: user nam
        :return: None
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
            bold = ""
            if self.user == "":
                bold = "**"

            return f"#{self.number} {bold}{self.desc}{bold} - {self.user}"

