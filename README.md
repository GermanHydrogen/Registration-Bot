# Registration-Bot
A simple Discord Bot for managing regestrations to events for your community.

## Usage
First of all create an Slotlist with following requirements:
- Begins with "Slotliste"
- Each slot has its own line
- Each slot description beginns with "#[Number of the slot]"
- Each slot description ends with an "-"

### Example
Slotliste

#01-CO-

#02-XO-

=========

Then init the bot with !create.

### Commands
- !create

- !slot [num]

- !unslot

- !forceSlot [num] [player]
  
- !forceUnslot [player]
