CREATE TABLE User(
    ID VARCHAR(18) NOT NULL,
    Nickname VARCHAR(50)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci,

    PRIMARY KEY (ID)
);

create TABLE Event(
    ID VARCHAR(18) NOT NULL,
    Name VARCHAR(50),
    Date DATE,
    Type VARCHAR(15),
    Message VARCHAR(18),
    PRIMARY KEY (ID)
);

CREATE TABLE Author(
    Event VARCHAR(18),
    User VARCHAR(18),
    CONSTRAINT author PRIMARY KEY (Event, User),
    FOREIGN KEY (Event) REFERENCES Event(ID),
    FOREIGN KEY (User) REFERENCES User(ID)
);

CREATE TABLE SlotGroup(
    ID MEDIUMINT UNSIGNED UNIQUE AUTO_INCREMENT,
    Number TINYINT UNSIGNED ,
    Event VARCHAR(18),
    Name VARCHAR(100)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci,
    Struct VARCHAR(10) NOT NULL ,
    CONSTRAINT slotgroup PRIMARY KEY (Number, Event),
    FOREIGN KEY (Event) REFERENCES Event(ID)
);


CREATE TABLE Slot(
    Event VARCHAR(18),
    Number VARCHAR(4),
    Description VARCHAR(50)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci,
    User VARCHAR(18),
    GroupID MEDIUMINT UNSIGNED,

  CONSTRAINT prim PRIMARY KEY (Event, Number),
  FOREIGN KEY (User) REFERENCES User(ID),
  FOREIGN KEY (GroupID) REFERENCES SlotGroup(ID) ON DELETE CASCADE ,
  FOREIGN KEY (Event) References Event(ID)
);

CREATE TABLE CampaignMessage
(
    Event VARCHAR(18),
    User VARCHAR(18),

    SlotNumber VARCHAR(4),

    MessageID VARCHAR(18) UNIQUE,
    DateUntil DATE,

    CONSTRAINT prim PRIMARY KEY (Event, User),
    FOREIGN KEY (Event) REFERENCES Event(ID),
    FOREIGN KEY (User) REFERENCES User(ID),
    FOREIGN KEY (Event, SlotNumber) REFERENCES Slot(Event, Number)
);

INSERT INTO User VALUES ('A00000000000000000', 'K.I.A.');
INSERT INTO User VALUES ('B00000000000000000', 'M.I.A.');
INSERT INTO User VALUES ('C00000000000000000', 'BLOCKED');



