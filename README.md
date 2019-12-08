# Registration-Bot
A simple Discord Bot for managing registrations to events for your community. It's using the discord.py package by Rapptz.

## Usage
First of all create an Slotlist with following requirements:
- Begins with "Slotliste"
- Each slot has its own line
- Each slot description begins with "#[Number of the slot]"
- Each slot description ends with an "-"

### Example

```
Slotliste

#01-CO-
#02-XO-

Anvil
#03 Squadleader -
#04 Fireteamleader -
```
---

Then init the bot with !create.

### Commands
- !create

- !slot [num]
- !unslot

- !addgroup [first slot] [last slot] [name]
- !delslot [name]

- !addslot [num] [group] [desc]
- !editslot [num] [desc]
- !delslot [num]

- !forceSlot [num] [player]
- !forceUnslot [player]
