from pathlib import Path
from typing import NoReturn, NamedTuple
import json
import re
from random import choice as random_choice

import yaml
from frozendict import frozendict

CUSA_TITLE_ID = re.compile(r'CUSA\d{5}')


class BuiltInSave(NamedTuple):
    on_ps4_title_id: str
    on_ps4_save_dir: str
    unique_name: str
    desc: str
    
    @classmethod
    def from_yaml_entry(cls,yaml_entry: str,/):
        on_ps4_title_id, on_ps4_save_dir, unique_name, *descc = yaml_entry.split(' ')
        return cls(on_ps4_title_id, on_ps4_save_dir, unique_name, ' '.join(descc))

    def as_entry_str(self) -> str:
        return ' '.join(self)

def is_ps4_title_id(input_str: str,/) -> bool: 
    return bool(CUSA_TITLE_ID.fullmatch(input_str))


def extract_drive_folder_id(link: str,/) -> str:
    return link.split('folders/')[-1].split('?')[0] if link.startswith('https://drive.google.com/drive') else ''


def is_str_int(thing: str,/) -> bool:
    try:
        int(thing)
        return True
    except ValueError:
        return False


def chunker(seq, size):
    """
    https://stackoverflow.com/questions/434287/how-to-iterate-over-a-list-in-chunks
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def extract_drive_file_id(link: str,/) -> str:
    if link.startswith('https://drive.google.com/file/d/'):
        return link.split('https://drive.google.com/file/d/')[-1].split('?')[0].split('/')[0]
    if link.startswith('https://drive.google.com/uc?id='):
        return link.split('https://drive.google.com/uc?id=')[-1].split('&')[0]
    
    return ''


def make_folder_name_safe(some_string_path_ig: str, /) -> str:
    some_string_path_ig = str(some_string_path_ig)
    some_string_path_ig = some_string_path_ig.replace(' ','_').replace('/','_').replace('\\','_')
    result = 'PS4_FOLDER_IN_ME_'+("".join(c for c in some_string_path_ig if c.isalnum() or c in ('_','-')).rstrip())
    return result[:254] if result else 'no_name'

def pretty_time(time_in_seconds: float) -> str:
    hours, extra_seconds = divmod(int(time_in_seconds),3600)
    minutes, seconds = divmod(extra_seconds,60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

def _raise_bad_config(missing_key: str) -> NoReturn:
    raise Exception(f'Unconfigured config, unconfigured value {missing_key} or bad config or missing {missing_key}')


def load_config() -> frozendict:

    try:
        with open('config.yaml','r') as f:
            my_config: dict = yaml.load(f,yaml.Loader)
            
    except Exception as e:
        with open('config.yaml','w') as f:
            f.write("""\
# Watch https://youtu.be/GvK-ZigEV4Q on how to get your bot token! 
discord_token: 
    MTIxMzAQk2APdMtqdXTtSfJcD2.GaxeZo.SLW6IWM7qdSxyQhCvClXINFJF4AIbF6oJVahrb
# Go to https://ca.account.sony.com/api/v1/ssocookie while signed into psn and put the string here
ssocookie: 
    glgagbgcSDh3t50ABpfwINS9kfugLPqDY8Lzfz3UabgE2w3OAhss6tWEJCOH54Sm 
# :shrug: Watch https://youtu.be/fkWM7A-MxR0 up untill you get your credentials.json, make sure file in same folder as the program
google_credentials_file: 
    credentials.json 
# This one is easy, you can get it by looking at View Connection Status in Network settings (IP Address)
ps4_ip:
    192.168.1.256 
# This is the user_id of your local account. NOT ACCOUNT ID! (i should be able to grab this automatically but idk why it no work)
# you can get this by going to /user/home on a ftp client and the folder name will be your user_id.
# also in each folder there is a username.dat file with the local username, so you can open this to find your user
# eg for me in /user/home/1eb71bbd the username.dat has SaveBy_Zhaxxy in it, which is my local username so my will be 1eb71bbd
user_id: 
    1ej71bbd
# The admins of the bot's ids. You can get this by enabling developer mode in discord and click user profile and 3 dots Copy User ID
# each line here starts with "  - " because of yaml syntax
bot_admins:
  - l147836464353247343
  - l207983219845103687
# Simple boolean, if set to true then people will be able to use the bot in dms,
# or if its false then people will not be able to use bot in dms, besides pinging the bot and my_account_id command
# Some people may not want people using bot in dms soo
allow_bot_usage_in_dms:
    true
# saves already on the console put here to allow for quicker resigns and cheats
# follow the format
# - TITLEID SAVEDIRNAME a_unique_name_for_a_save some description that can have spaces
built_in_saves:
  - CUSA12345 LBPXSAVE bigfart some cool description here
""")
        raise Exception(f'bad config file or missing, got error {type(e).__name__}: {e} Please edit the config.yaml file') from None

    key = 'discord_token'
    if not (x := my_config.get(key)) or x == 'MTIxMzAQk2APdMtqdXTtSfJcD2.GaxeZo.SLW6IWM7qdSxyQhCvClXINFJF4AIbF6oJVahrb':
        _raise_bad_config(key)

    key = 'ssocookie'
    if not (x := my_config.get(key)) or x == 'glgagbgcSDh3t50ABpfwINS9kfugLPqDY8Lzfz3UabgE2w3OAhss6tWEJCOH54Sm':
        _raise_bad_config(key)

    key = 'google_credentials_file'
    if not (x := my_config.get(key)):
        _raise_bad_config(key)

    try:
        json.loads(Path(x).read_text())
    except Exception as e:
        raise Exception(f'Could not open {key}: {x} or not valid google_credentials_file, got error {type(e).__name__}: {e}') from None

    key = 'ps4_ip'
    if not (x := my_config.get(key)) or x == '192.168.1.256':
        _raise_bad_config(key)

    key = 'save_dirs'
    if (x := my_config.get(key)):
        raise Exception(f'{key} in your config is no longer needed, please delete it as well as its values')

    key = 'title_id'
    if (x := my_config.get(key)):
        raise Exception(f'{key} in your config is no longer needed, please delete it as well as its value')

    key = 'user_id'
    if not (x := my_config.get(key)) or x == '1ej71bbd':
        _raise_bad_config(key)

    key = 'bot_admins'
    if not (x := my_config.get(key)):
        _raise_bad_config(key)
    
    if not all(isinstance(a,int) for a in x):
        _raise_bad_config(key)

    my_config[key] = tuple(x)
    
    key = 'allow_bot_usage_in_dms'
    if (x := my_config.get(key)) is None:
        _raise_bad_config(key)
    
    if not isinstance(x,bool):
        raise Exception(f'{key} value should ethier be true or false, not {x}')

    key = 'built_in_saves'
    if (x := my_config.get(key)) is None:
        raise Exception(f'Unconfigured config, unconfigured value {key} or bad config or missing {key}, you can just put the key and no saves if you dont want any built in saves')
    
    if my_config[key] is None:
        del my_config[key]
    
    for i, value in enumerate(my_config[key]):
        try:
            newish_value = my_config[key][i] = BuiltInSave.from_yaml_entry(value)
        except Exception as e:
            raise ValueError(f'Invalid {key} entry `{value}`, got error {type(e).__name__}: {e}') from None


        for i2, sub_value in enumerate(my_config[key]):
            if i2 == i:
                continue
            try:
                newish_sub_value = BuiltInSave.from_yaml_entry(sub_value)
            except Exception:
                continue # this is gonna error out later, lets just let that happen when it comes to the time
            
            if newish_sub_value.unique_name == newish_value.unique_name:
                raise ValueError(f'Entries `{value}` and `{sub_value}` cannot have the save unique_name')
            
            if (newish_sub_value.on_ps4_title_id == newish_value.on_ps4_title_id) and \
            (newish_sub_value.on_ps4_save_dir == newish_value.on_ps4_save_dir):
                raise ValueError(f'Entries `{value}` and `{sub_value}` are duplicate saves, maybe you made a mistake?')


    my_config[key] = frozendict({ben.unique_name:ben for ben in my_config[key]})
    return frozendict(my_config)


SILLY_RANDOM_STRINGS_NOT_UNIQUE = """
You can add any more strings here you want, just put in your strings in theese triple quotes for each string choice new line
ben
BENNY ben BENNY
benny, oh benny!
I HATE NI
hush little piggy
feel free do donate me anything to paypal eboot.bin@protonmail.com
SHAT AP
C plas plas
Donald_trump_talks_about_trucks.mp4
rip littlebigplanet 2024 april
Samoji & Hotane's Daily Life
**this text is bold.** *this text is in italics.* `this text has a dark grey box behind it.` __this text is underlined.__ ~~this text is crossed out.~~
90.237.164.177, this your ip lil bro?
I don't know what the cat says
Mu wants something.
モドキやんの要求は？(^^♪
どうした？ お腹は空いてなさそうし･･･｡何が欲しいの？何をして欲しいの？
My jaw is itchy and itchy. (^^♪
Die Katze bellt die Fliege an
where ever happened to eZwizard1, was there ever a eZwizard1?
thesoundsofchildrenbeingtoturedinhell.png
$Afx/ProcessorID
RuntimeError: coroutine ignored GeneratorExit, more like kys: kys ignored kys (keep yourself safe)
ben you are getting too close to me
Суперкот
LittleBigPlanet 7ny% - Full Series Speedrun! (8:46:26)
BD0CB701D6079614D54DF907A08CDB10
PR]-<Q9*WxHsV8rcW!JuH7k_ug:T5ApX and the iv is _Y7]mD1ziyH#Ar=0
Tammy!
ITZTHATPLAYER was here.
""".strip().split('\n')

def get_a_stupid_silly_random_string_not_unique() -> str:
    return random_choice(SILLY_RANDOM_STRINGS_NOT_UNIQUE)
