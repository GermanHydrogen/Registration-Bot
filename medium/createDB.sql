CREATE TABLE IF NOT EXISTS User(
    ID VARCHAR(18) NOT NULL,
    Nickname VARCHAR(50)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci,

    PRIMARY KEY (ID)
);

create TABLE IF NOT EXISTS Event(
    ID VARCHAR(18) NOT NULL,
    Name VARCHAR(50),
    Author VARCHAR(18) NOT NULL,
    Date DATE,
    Type VARCHAR(15),
    Message VARCHAR(18),

    PRIMARY KEY (ID),
    FOREIGN KEY (Author) REFERENCES User(ID)
);

CREATE TABLE IF NOT EXISTS SlotGroup(
    Number TINYINT UNSIGNED ,
    Event VARCHAR(18),
    Name VARCHAR(100)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci,
    Struct VARCHAR(10) NOT NULL ,
    CONSTRAINT slotgroup PRIMARY KEY (Number, Event),
    FOREIGN KEY (Event) REFERENCES Event(ID)
);


CREATE TABLE IF NOT EXISTS Slot(
    Event VARCHAR(18),
    Number VARCHAR(4),
    Description VARCHAR(50)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci,
    User VARCHAR(18),
    GroupNumber TINYINT UNSIGNED NOT NULL,

  CONSTRAINT prim PRIMARY KEY (Event, Number),
  FOREIGN KEY (User) REFERENCES User(ID),
  FOREIGN KEY (Event, GroupNumber) REFERENCES SlotGroup(Event, Number) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS CampaignMessage
(
    Event VARCHAR(18),
    User VARCHAR(18),

    SlotNumber VARCHAR(4),

    MessageID VARCHAR(18) UNIQUE,
    DateUntil DATE,

    CONSTRAINT prim PRIMARY KEY (Event, User),
    FOREIGN KEY (User) REFERENCES User(ID),
    FOREIGN KEY (Event, SlotNumber) REFERENCES Slot(Event, Number)
);

CREATE TABLE IF NOT EXISTS TradeMessage(

    Event VARCHAR(18),

    ReqUser VARCHAR(18) CHECK(ReqUser regexp '^[0-9]'),
    RecUser VARCHAR(18) NOT NULL CHECK(RecUser regexp '^[0-9]'),

    MessageID VARCHAR(18) NOT NULL UNIQUE,
    DateUntil DATE NOT NULL ,

    CONSTRAINT prim PRIMARY KEY (Event, ReqUser),
    CONSTRAINT user CHECK (ReqUser != RecUser),
    FOREIGN KEY (Event) REFERENCES Event(ID),
    FOREIGN KEY (ReqUser) REFERENCES User(ID),
    FOREIGN KEY (RecUser) REFERENCES User(ID)
);


INSERT INTO User VALUES ('A00000000000000000', 'K.I.A.');
INSERT INTO User VALUES ('B00000000000000000', 'M.I.A.');
INSERT INTO User VALUES ('C00000000000000000', 'BLOCKED');
INSERT INTO User VALUES ('D00000000000000000', 'Auf Nachfrage beim Missionsbauer');

CREATE TRIGGER BotTest before update on Slot
  for each row
   begin
    if 0 < (SELECT COUNT(*) FROM Slot s
        WHERE new.User regexp '^[0-9]' AND
              new.User = s.User AND
              new.Event = s.Event
        GROUP BY s.User) then
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot add or update row: only';
      end if;
      end;

