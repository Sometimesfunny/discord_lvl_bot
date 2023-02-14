import os
from PIL import Image
import json
import copy
from discord import Member
# get experience for a level
def get_exp(level : int):
    if level < 0:
        return 0
    return 50 * int((level+1) ** 2) - int((level+1)*50)

# get level for experience
def get_level(exp : int):
    if exp <= 0:
        return 0
    level = 0
    while get_exp(level+1) <= exp:
        level += 1
    return level

def load_templates(templates_folder_path : str):
    templates = {}
    for template in os.listdir(templates_folder_path):
        if template.endswith('.png'):
            templates[template[:-4]] = Image.open(f'{templates_folder_path}{template}')
    print(f'Loaded {len(templates)} templates')
    return templates

# save data
def save_data(data, filename : str):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
        print(f'Saved data to {filename}')
        print('------')

# if file exists, load data
def load_data(filename : str):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            new_data = {}
            old_data_keys = copy.copy(list(data.keys()))
            for user_id in old_data_keys:
                new_data[int(user_id)] = data.pop(user_id)
        return new_data
    except FileNotFoundError:
        return {}
    finally:
        print(f'Loaded data from {filename}')

def load_server_data(filename : str):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'guild_id': None,
            'channel_for_commands': None,
            'channel_for_level_up': None,
            'delta_in_experience': 10,
            'experience_per_message': 10,
            'allowed_roles': {
                'level' : [],
                'set_experience_per_message' : [],
                'set_delta_in_experience' : [],
                'add_experience' : [],
                'remove_experience' : [],
                'set_experience' : [],
                'set_level' : [],
                'stats' : [],
                'help' : [],
                'pause' : [],
                'resume' : [],
                'set_commands_channel' : [],
                'set_level_up_channel' : [],
                'allow_roles' : [],
                'disallow_roles' : [],
                'give_boost' : [],
                'stop_boost' : []
            }
        }
    finally:
        print(f'Loaded data from {filename}')

def check_role(user : Member, command_name : str, server_data : dict):
    if user.guild_permissions.administrator:
        return True
    if command_name in server_data['allowed_roles'].keys():
        if server_data['allowed_roles'][command_name] == []:
            return False
        roles_hierarchy = [role.id for role in user.guild.roles]
        command_role_index = roles_hierarchy.index(server_data['allowed_roles'][command_name][0])
        user_role_index = roles_hierarchy.index(user.top_role.id)
        if user_role_index >= command_role_index:
            return True
    else:
        print(f'{command_name} is not a valid command, added to allowed_roles')
        server_data['allowed_roles'][command_name] = []
        save_data('server_data.json')
        return True
    return False

def check_channel(channel_id : int, server_data : dict):
    if server_data['channel_for_commands'] is None:
        return True
    if channel_id == server_data['channel_for_commands']:
        return True
    return False

def clear_user_temp_files(user_id : int, temp_folder_path : str):
    user_id = str(user_id)
    for file in os.listdir(temp_folder_path):
        if user_id in file:
            os.remove(f'{temp_folder_path}{file}')

def clear_temp_folder(temp_folder_path : str):
    for file in os.listdir(temp_folder_path):
        os.remove(f'{temp_folder_path}{file}')
