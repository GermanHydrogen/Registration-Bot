# Registration-Bot
A simple Discord Bot for managing regestrations to events for your community.

## Install
1. #### Prerequisites:
    1. python 3.6 or later
    2. install lib: discord.py

2. Add config.yml with:  token: "[Your own Bot Token]"

## Usage
First of all create an Slotlist with following requirements:
- Begins with "Slotliste"
- Each slot has its own line
- Each slot description beginns with "#[Number of the slot]"
- The slot description ends with an "-"

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
