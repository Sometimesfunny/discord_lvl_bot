# Discord LVL Bot
Simple levelling bot with beautiful background pictures (Inspired by [DBS DAO](https://t.me/bomzhuem))

# Install
## Requirements
- Python3.8+
## Dependencies
- discord.py 2.0.0+
## Installation
1. ```sh
    sudo apt update && sudo apt upgrade -y
    sudo apt install git
    git clone git@github.com:Sometimesfunny/discord_lvl_bot.git
    pip3 install -r requirements.txt
    ```
2. Create discord_lvl_config.ini
3. Insert this template:
```ini
[AUTH]
bot_token = 'YOUR_DISCORD_BOT_TOKEN'
```
4. Save file
## Run
```python
python3 discord_lvl_bot.py
```
# Features
- Levelling system
- /level command to check your level
- Wide settings
- Administrative commands

# Setup bot
1. Create file server_data.json
2. Fill the template:
```json
{
  "guild_id": 1006200270176407582,
  "channel_for_commands": 1011650910889447434,
  "channel_for_level_up": 1011650872364765225,
  "delta_in_experience": 10,
  "experience_per_message": 10,
  "allowed_roles": {
    "level": [
      1010587178574827550
    ],
    "set_experience_per_message": [],
    "set_delta_in_experience": [],
    "add_experience": [],
    "remove_experience": [],
    "set_experience": [],
    "set_level": [],
    "stats": [],
    "help": [],
    "pause": [],
    "resume": [],
    "set_commands_channel": [],
    "set_level_up_channel": [],
    "allow_roles": [],
    "disallow_roles": [],
    "give_boost": [],
    "stop_boost": []
  }
}
```
>Here you can change different parameters for XP gaining. Also you can manage role permissions from here.

## Data

>XP amount and users store in data.json
