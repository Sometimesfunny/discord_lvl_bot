import discord
import asyncio
import configparser
from discord import app_commands
from discord.ext import tasks
import datetime
from PIL import Image
from picture_processing.level_utils import *
from level.utils import *

TEMP_FOLDER_PATH = 'data/temp/'
FONTS_FOLDER_PATH = 'data/fonts/'
TEMPLATES_FOLDER_PATH = 'data/templates/'


# create discord bot class
class DiscordBot(discord.Client):
    # constructor
    def __init__(
        self, 
        users_data : dict, 
        server_data : dict, 
        *args, **kwargs
        ):
        intents = discord.Intents.default()
        super().__init__(intents=intents ,*args, **kwargs)
        self.synced = False
        self.users_data = users_data
        self.pause_experience = False
        if server_data['delta_in_experience'] is not None:
            self.delta_in_experience = datetime.timedelta(seconds=server_data['delta_in_experience'])
        else:
            self.delta_in_experience = datetime.timedelta(seconds=10)
            server_data['delta_in_experience'] = self.delta_in_experience.total_seconds()
        if server_data['experience_per_message'] is not None:
            self.experience_per_message = server_data['experience_per_message']
        else:
            self.experience_per_message = 10
            server_data['experience_per_message'] = self.experience_per_message
        if server_data['guild_id'] is not None:
            self.guild_id = server_data['guild_id']
        else:
            self.guild_id = None
            server_data['guild_id'] = self.guild_id
        if server_data['channel_for_commands'] is not None:
            self.channel_commands_id = server_data['channel_for_commands']
        else:
            self.channel_commands_id = None
            server_data['channel_for_commands'] = self.channel_commands_id
        if server_data['channel_for_level_up'] is not None:
            self.channel_for_level_up = server_data['channel_for_level_up']
        else:
            self.channel_for_level_up = None
            server_data['channel_for_level_up'] = self.channel_for_level_up

    # on ready function
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        if not self.synced:
            commands = await tree.sync()
            for command in commands:
                print(command.name)
            self.synced = True
        saving_loop.start()

    # on message function
    async def on_message(self, message : discord.Message):
        if message.author.bot:
            return
        if not self.pause_experience:
            if message.author.id in self.users_data.keys():
                current_level = get_level(self.users_data[message.author.id]['experience'])
                if datetime.datetime.now().timestamp() - self.users_data[message.author.id]['last_experience_recieved'] < self.delta_in_experience.total_seconds():
                    return
                self.gain_experience(message.author.id, self.experience_per_message)
                new_level = get_level(self.users_data[message.author.id]['experience'])
                if new_level > current_level:
                    if server_data['channel_for_level_up'] is not None:
                        await bot.get_channel(server_data['channel_for_level_up']).send(f'{message.author.mention} you advanced to level {new_level}!')
                    else:
                        await message.channel.send(f'{message.author.mention} you leveled up to level {new_level}!')
            else:
                self.gain_experience(message.author.id, self.experience_per_message)
            save_data(self.users_data, 'data.json')
    
    # gain experience function
    def gain_experience(self, user_id : int, amount : int):
        if user_id in self.users_data.keys():
            self.users_data[user_id]['experience'] += amount
            self.users_data[user_id]['last_experience_recieved'] = datetime.datetime.now().timestamp()
        else:
            self.users_data[user_id] = {
                'experience': amount,
                'last_experience_recieved': datetime.datetime.now().timestamp()
                }
        
data = None

config = configparser.ConfigParser()
config.read('discord_lvl_config.ini')
token = config['AUTH']['bot_token']

data = load_data('data.json')
server_data = load_server_data('server_data.json')
templates = load_templates(TEMPLATES_FOLDER_PATH)

# run bot
bot = DiscordBot(data, server_data, command_prefix='!')

@tasks.loop(minutes=5)
async def saving_loop():
    await bot.wait_until_ready()
    save_data(bot.users_data, 'data.json')

tree = app_commands.CommandTree(bot)

work_guild = bot.get_guild(server_data['guild_id'])

SYS_COMMANDS = [
    'set_experience_per_message',
    'set_delta_in_experience',
    'add_experience',
    'remove_experience',
    'set_experience',
    'set_level',
    'stats',
    'help',
    'pause',
    'resume',
    'set_commands_channel',
    'set_level_up_channel',
    'allow_roles',
    'disallow_roles',
    'give_boost',
    'stop_boost'
]

# create command level
@tree.command(name='level', description='Shows current level and experience', guild=work_guild)
async def level(interaction : discord.Interaction, user : discord.User = None):
    if not check_channel(interaction.channel.id, server_data):
        await interaction.response.send_message(f'This command can only be used in {interaction.guild.get_channel(server_data["channel_for_commands"]).mention}', ephemeral=True)
        return
    if (user is None) or (not interaction.user.guild_permissions.administrator):
        user = interaction.user
    if not check_role(interaction.user, 'level', server_data):
        await interaction.response.send_message(f'{interaction.user.mention} you do not have permission to use this command', ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    await user.display_avatar.save(f'{TEMP_FOLDER_PATH}{user.id}.png')
    image = Image.open(f"{TEMP_FOLDER_PATH}{user.id}.png")
    image = resize(image, 128)
    image.save(f'{TEMP_FOLDER_PATH}{user.id}_resized.png')
    if user.id not in bot.users_data.keys():
        level = 0
        exp = 0
        exp_next = get_exp(level+1)
        bot.users_data[user.id] = {
            'experience': exp,
            'last_experience_recieved': 0
        }
    else:
        level = get_level(bot.users_data[user.id]["experience"])
        exp =  bot.users_data[user.id]["experience"]-get_exp(level)
        exp_next = get_exp(level+1)-get_exp(level)
    prepare_image(user.id, f'{user.name}#{user.discriminator}', level, user.top_role.name.upper(), exp, exp_next, templates['10x10'], templates['21x21'], templates['template'], TEMP_FOLDER_PATH, FONTS_FOLDER_PATH)
    await interaction.followup.send(file=discord.File(f'{TEMP_FOLDER_PATH}{user.id}_ready.png'))
    clear_user_temp_files(user.id, TEMP_FOLDER_PATH)

# create command to set experience per message
@tree.command(name='set_experience_per_message', description='Sets experience per message', guild=work_guild)
async def set_experience_per_message(interaction : discord.Interaction, amount : int):
    if not check_role(interaction.user, 'set_experience_per_message', server_data):
        return
    bot.experience_per_message = amount
    server_data['experience_per_message'] = amount
    save_data(server_data, 'server_data.json')
    await interaction.response.send_message(f'Experience per message set to {amount}')

# create command to set delta in experience
@tree.command(name='set_delta_in_experience', description='Sets delta in experience', guild=work_guild)
async def set_delta_in_experience(interaction : discord.Interaction, amount : int):
    if not check_role(interaction.user, 'set_delta_in_experience', server_data):
        return
    bot.delta_in_experience = datetime.timedelta(seconds=amount)
    server_data['delta_in_experience'] = amount
    save_data(server_data, 'server_data.json')
    await interaction.response.send_message(f'Delta in experience set to {amount} seconds')

# create command to add experience to user
@tree.command(name='add_experience', description='Adds experience to user', guild=work_guild)
async def add_experience(interaction : discord.Interaction, user : discord.User, amount : int):
    if not check_role(interaction.user, 'add_experience', server_data):
        return
    if user.id in bot.users_data.keys():
        bot.users_data[user.id]['experience'] += amount
    else:
         bot.users_data[user.id] = {
            'experience': amount,
            'last_experience_recieved': datetime.datetime.now().timestamp()
            }
    await interaction.response.send_message(f'{user.mention} gained {amount} experience')

# create command to remove experience from user
@tree.command(name='remove_experience', description='Removes experience from user', guild=work_guild)
async def remove_experience(interaction : discord.Interaction, user : discord.User, amount : int):
    if not check_role(interaction.user, 'remove_experience', server_data):
        return
    if user.id in bot.users_data.keys():
         bot.users_data[user.id]['experience'] -= amount
    else:
         bot.users_data[user.id] = {
            'experience': -amount,
            'last_experience_recieved': datetime.datetime.now().timestamp()
            }
    await interaction.response.send_message(f'{user.mention} lost {amount} experience')

# create command to set user experience
@tree.command(name='set_experience', description='Sets user experience', guild=work_guild)
async def set_experience(interaction : discord.Interaction, user : discord.User, amount : int):
    if not check_role(interaction.user, 'set_experience', server_data):
        return
    bot.users_data[user.id] = {
        'experience': amount,
        'last_experience_recieved': datetime.datetime.now().timestamp()
        }
    await interaction.response.send_message(f'{user.mention} experience set to {amount}')

# create command to set user level
@tree.command(name='set_level', description='Sets user level', guild=work_guild)
async def set_level(interaction : discord.Interaction, user : discord.User, level : int):
    if not check_role(interaction.user, 'set_level', server_data):
        return
    bot.users_data[user.id] = {
        'experience': get_exp(level),
        'last_experience_recieved': datetime.datetime.now().timestamp()
        }
    await interaction.response.send_message(f'{user.mention} level set to {level}')

# create command to print stats experience per message and delta in experience
@tree.command(name='stats', description='Prints stats', guild=work_guild)
async def stats(interaction : discord.Interaction):
    if not check_role(interaction.user, 'stats', server_data):
        return
    await interaction.response.send_message(f'Experience per message: {bot.experience_per_message}\nDelta in experience: {bot.delta_in_experience.seconds} seconds\n')

# create command to print help
@tree.command(name='help', description='Prints help', guild=work_guild)
async def help(interaction : discord.Interaction):
    if not check_role(interaction.user, 'help', server_data):
        return
    await interaction.response.send_message(f'/level - Shows current level and experience\n/set_experience_per_message <amount> - Sets experience per message\n/set_delta_in_experience <amount> - Sets delta in experience\n/add_experience <user> <amount> - Adds experience to user\n/remove_experience <user> <amount> - Removes experience from user\n/set_experience <user> <amount> - Sets user experience\n/set_level <user> <level> - Sets user level\n/stats - Prints stats')

# create command to pause experience
@tree.command(name='pause', description='Pauses experience', guild=work_guild)
async def pause(interaction : discord.Interaction):
    if not check_role(interaction.user, 'pause', server_data):
        return
    bot.pause_experience = True
    await interaction.response.send_message('Experience paused')

# create command to resume experience
@tree.command(name='resume', description='Resumes experience', guild=work_guild)
async def resume(interaction : discord.Interaction):
    if not check_role(interaction.user, 'resume', server_data):
        return
    bot.pause_experience = False
    await interaction.response.send_message('Experience resumed')

# create command to set commands channel
@tree.command(name='set_commands_channel', description='Sets commands channel', guild=work_guild)
async def set_commands_channel(interaction : discord.Interaction, channel : discord.abc.GuildChannel = None):
    if not check_role(interaction.user, 'set_commands_channel', server_data):
        return
    if channel is None:
        server_data['channel_for_commands'] = None
    server_data['channel_for_commands'] = channel.id
    bot.channel_commands_id = server_data['channel_for_commands']
    save_data(server_data, 'server_data.json')
    await interaction.response.send_message(f'Commands channel set to {channel.mention}')

# create command to set level up channel
@tree.command(name='set_level_up_channel', description='Sets level up channel', guild=work_guild)
async def set_level_up_channel(interaction : discord.Interaction, channel : discord.abc.GuildChannel = None):
    if not check_role(interaction.user, 'set_level_up_channel', server_data):
        return
    if channel is None:
        server_data['channel_for_level_up'] = None
    server_data['channel_for_level_up'] = channel.id
    bot.channel_for_level_up = server_data['channel_for_level_up']
    save_data(server_data, 'server_data.json')
    
    await interaction.response.send_message(f'Level up channel set to {channel.mention}')

# create command to allow roles
@tree.command(name='allow_roles', description='Allows roles', guild=work_guild)
async def allow_roles(interaction : discord.Interaction, command_name : str, role1 : discord.Role, role2 : discord.Role = None, role3 : discord.Role = None, role4 : discord.Role = None, role5 : discord.Role = None):
    if not check_role(interaction.user, 'allow_roles', server_data):
        return
    if (command_name not in server_data['allowed_roles'].keys()) and (command_name not in ['sys']):
        await interaction.response.send_message('Command not found')
        return
    # add role to roles if role not None
    if role1 is not None:
        roles = [role1]
    else:
        roles = []
    if role2 is not None:
        roles.append(role2)
    if role3 is not None:
        roles.append(role3)
    if role4 is not None:
        roles.append(role4)
    if role5 is not None:
        roles.append(role5)
    if command_name == 'sys':
        for command in SYS_COMMANDS:
            if role1.id not in server_data['allowed_roles'][command]:
                server_data['allowed_roles'][command].append(role1.id)
    else:
        # add roles ids to allowed roles
        server_data['allowed_roles'][command_name].extend([role.id for role in roles])
        # save server data
        save_data(server_data, 'server_data.json')
    await interaction.response.send_message(f'Roles allowed for {command_name}')

# create command to disallow roles
@tree.command(name='disallow_roles', description='Disallows roles', guild=work_guild)
async def disallow_roles(interaction : discord.Interaction, command_name : str, role1 : discord.Role, role2 : discord.Role = None, role3 : discord.Role = None, role4 : discord.Role = None, role5 : discord.Role = None):
    if not check_role(interaction.user, 'disallow_roles', server_data):
        return
    if (command_name not in server_data['allowed_roles'].keys()) and (command_name not in ['sys']):
        await interaction.response.send_message('Command not found')
        return
    roles = [role1, role2, role3, role4, role5]
    # remove None roles
    roles = [role for role in roles if role is not None]
    if command_name == 'sys':
        for command in SYS_COMMANDS:
            for role in roles:
                if role.id in server_data['allowed_roles'][command]:
                    server_data['allowed_roles'][command].remove(role.id)
    else:
        for role in roles:
            if role.id in server_data['allowed_roles'][command_name]:
                server_data['allowed_roles'][command_name].remove(role.id)
    # save server data
    save_data(server_data, 'server_data.json')
    await interaction.response.send_message(f'Roles disallowed for {command_name}')

task_pool = []

# create command to give boost for some time
@tree.command(name='give_boost', description='Gives boost for some time', guild=work_guild)
async def give_boost(interaction : discord.Interaction, amount : float, time : int):
    if not check_role(interaction.user, 'give_boost', server_data):
        return
    if amount < 0:
        await interaction.response.send_message('Amount must be positive')
        return
    if time < 0:
        await interaction.response.send_message('Time must be positive')
        return
    create_task(time, multiplier=amount)
    task_pool[-1].start()
    await interaction.response.send_message(f'Boost given for {time} seconds')

# create command to stop boost
@tree.command(name='stop_boost', description='Stops boost', guild=work_guild)
async def stop_boost(interaction : discord.Interaction):
    if not check_role(interaction.user, 'stop_boost', server_data):
        return
    for task in task_pool:
        task.stop()
    task_pool.clear()
    await interaction.response.send_message('Boost stopped')

# create function to create tasks 
def create_task(seconds : int=0, minutes : int=0, hours : int=0, count : int=1, multiplier : float = 1):
    if not (seconds or minutes or hours):
        return False
    @tasks.loop(seconds=seconds, minutes=minutes, hours=hours, count=count)
    async def task():
        bot.experience_per_message = int(bot.experience_per_message * multiplier)
        # wait for seconds
        await asyncio.sleep(seconds + minutes * 60 + hours * 3600)
        bot.experience_per_message = 10
    task_pool.append(task)
    @task.after_loop
    async def after_loop():
        task_pool.remove(task)
    return True
        

bot.run(token)

save_data(bot.users_data, 'data.json')
save_data(server_data, 'server_data.json')
clear_temp_folder(TEMP_FOLDER_PATH)
