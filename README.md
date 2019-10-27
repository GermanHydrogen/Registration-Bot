# Registration-Bot
A simple Discord Bot for managing registrations to events for your community.

# Deutsch



## Eventerstellung
### Channel

Channelname: [Datum]-[Bezeichner] (z.B 2019-10-15-arma3)

Die erste Nachricht im Channel muss vom Eventersteller sein!

### Slotliste
- Beginnt mit "Slotliste"
- Jeder Slot nimmt eine Zeile ein

- Ein Slot ist aufgebaut aus #[Nummer] [Beschreibung] -
- Das "-" am Ende ist wichtig

#### Beispiel
Slotliste

#01 CO -

#02 XO -


#03 Fireteamleader -

### Abschließend

Zum Initialisieren des Bots !create ausführen.

## Managment

### Event Bearbeiten

- !addslot [num] [Beschreibung]  &nbsp;&nbsp;&nbsp; Fügt einen Slot zur Liste hinzu
- !delslot [num]                &nbsp;&nbsp;&nbsp; Löscht einen Slot

### Commands

- !forceslot [num] [Nutzer]     &nbsp;&nbsp;&nbsp;Trägt einen Nutzer in einen Slot ein
- !forceunslot [Nutzer]         &nbsp;&nbsp;&nbsp;&nbsp;Trägt einen Nutzer aus


---


# English

## Usage
First of all create an Slotlist with following requirements:
- Begins with "Slotliste"
- Each slot has its own line
- Each slot description begins with "#[Number of the slot]"
- Each slot description ends with an "-"

### Example
Slotliste

#01-CO-

#02-XO-

---

Then init the bot with !create.

### Commands
- !create

- !slot [num]

- !unslot

- !forceSlot [num] [player]

- !forceUnslot [player]
