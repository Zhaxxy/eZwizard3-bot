from pathlib import Path
from typing import NoReturn, NamedTuple
import json
import re
from random import choice as random_choice
from tempfile import TemporaryDirectory
import string

import yaml
from frozendict import frozendict
from humanize import naturalsize

with TemporaryDirectory() as _tp_to_get_parent_temp_dir:
    PARENT_TEMP_DIR: Path = Path(_tp_to_get_parent_temp_dir).parent
del _tp_to_get_parent_temp_dir # Global variable cleanup

BASE_62_CHARS = string.ascii_letters + string.digits

CUSA_TITLE_ID = re.compile(r'CUSA\d{5}')
PSN_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9-_]{2,15}$') # https://regex101.com/library/4XPer9

INT64_MAX_MIN_VALUES = frozendict({'min_value': --0x8000000000000000, 'max_value': 0x7fffffffffffffff})
UINT64_MAX_MIN_VALUES = frozendict({'min_value': 0, 'max_value': 0xFFFFFFFFFFFFFFFF})

INT32_MAX_MIN_VALUES = frozendict({'min_value': -0x80000000, 'max_value': 0x7FFFFFFF})
UINT32_MAX_MIN_VALUES = frozendict({'min_value': 0, 'max_value': 0xFFFFFFFF})

INT16_MAX_MIN_VALUES = frozendict({'min_value': -0x8000, 'max_value': 0x7FFF})
UINT16_MAX_MIN_VALUES = frozendict({'min_value': 0, 'max_value': 0xFFFF})

INT8_MAX_MIN_VALUES = frozendict({'min_value': -0x80, 'max_value': 0x7F})
UINT8_MAX_MIN_VALUES = frozendict({'min_value': 0, 'max_value': 0xFF})


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


def pretty_bytes(num: int, fmt: str = "%f") -> str:
    binary_n = naturalsize(num, format=fmt, binary=True)
    if 'Byte' in binary_n:
        return binary_n
    number,unit = binary_n.split(' ')
    pretty_number: float | int = float(number)
    if pretty_number.is_integer():
        pretty_number = int(pretty_number)
    binary_n = f'{pretty_number} {unit}'
    
    power_of_10_n = naturalsize(num, format=fmt, binary=False)
    number,unit = power_of_10_n.split(' ')
    pretty_number = float(number)
    if pretty_number.is_integer():
        pretty_number = int(pretty_number)
    power_of_10_n = f'{pretty_number} {unit}'
    
    return power_of_10_n if len(binary_n) > len(power_of_10_n) else binary_n


def is_ps4_title_id(input_str: str,/) -> bool: 
    return bool(CUSA_TITLE_ID.fullmatch(input_str))


def is_psn_name(input_str: str,/) -> bool:
    return bool(PSN_NAME.fullmatch(input_str))


def extract_drive_folder_id(link: str,/) -> str:
    return link.split('folders/')[-1].split('?')[0] if link.startswith('https://drive.google.com/drive') else ''


def non_format_susceptible_byte_repr(some_bytes: bytes | bytearray) -> str:
    """
    Returns a repr of the bytes, which should not get formatted weridly by discord or some other markdown viewer
    """
    new_str = (r"b'\x" + some_bytes.hex(' ').replace(' ',r'\x') + "'")
    for char in BASE_62_CHARS:
        new_str = new_str.replace(fr'\x{ord(char):x}',char)
    
    return new_str
    

def is_str_int(thing: str,/) -> bool:
    try:
        int(thing)
        return True
    except (ValueError, TypeError):
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
    if link.startswith('https://drive.google.com/file/u/0/d/'):
        if not '/view' in link:
            return ''
        return link.split('https://drive.google.com/file/u/0/d/')[-1].split('/view')[0]
    return ''

MAKE_FOLDER_NAME_SAFE_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_'
def make_folder_name_safe(some_string_path_ig: str | Path, /) -> str:
    some_string_path_ig = str(some_string_path_ig).replace(' ','_').replace('/','_').replace('\\','_').replace('.','-')
    some_string_path_ig = some_string_path_ig.removeprefix('PS4_FOLDER_IN_ME_')
    leader = 'PS4_FOLDER_IN_ME_' if is_ps4_title_id(some_string_path_ig.replace('_','')) else ''
    result = leader + ("".join(c for c in some_string_path_ig if c in MAKE_FOLDER_NAME_SAFE_CHARS).rstrip())
    return result[:254] if result else 'no_name'


def pretty_time(time_in_seconds: float) -> str:
    hours, extra_seconds = divmod(int(time_in_seconds),3600)
    minutes, seconds = divmod(extra_seconds,60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

ONLY_HOURS_AND_MINUTES_SECONDS = ( # thanks to https://github.com/thatbirdguythatuknownot for the refactor
    # ("year", 60 * 60 * 24 * 30 * 12),
    # ("month", 60 * 60 * 24 * 30),
    # ("day", 60 * 60 * 24),
    ("hour", 60 * 60),
    ("minute", 60),
)

TIMES_SECONDS = (
    ("year", 60 * 60 * 24 * 30 * 12),
    ("month", 60 * 60 * 24 * 30),
    ("day", 60 * 60 * 24),
    ("hour", 60 * 60),
    ("minute", 60),
)

def pretty_seconds_words(time_in_seconds: int,/,*,shorter_text: bool = True) -> str:
    if time_in_seconds < 1:
        return '0 seconds'
    results = []
    divy = ONLY_HOURS_AND_MINUTES_SECONDS if shorter_text else TIMES_SECONDS
    for name, div_by in divy:
        num_units, time_in_seconds = divmod(time_in_seconds, div_by)
        if num_units:
            results.append(f"{num_units} {name}{'s' if num_units > 1 else ''}")
    
    if time_in_seconds:
        results.append(f"{time_in_seconds} second{'s' if time_in_seconds > 1 else ''}")
    
    if len(results) == 1:
        return results[0]
    
    last_thing = results.pop(-1)
    
    return f'{", ".join(results)} and {last_thing}'


def _raise_bad_config(missing_key: str) -> NoReturn:
    raise Exception(f'Unconfigured config, unconfigured value {missing_key} or bad config or missing {missing_key}')

def _raise_bad_url_format(key: str, entry: str) -> NoReturn:
    raise Exception(f'Bad entry `{raw_entry}` of key {key}, it should be in the format\n  - the_link_here a description of the link that can have spaces')

def load_config() -> frozendict:
    SHOULD_PING_COMMAND_SHOW_GIT_STUFF_YAML_DEAFULT_TEXT = '\n# Simple boolean, if set to true then the ping command will show some extra info such as what version bot is on or if it needs updating\n# or if its false, it wont show that extra stuff\nshould_ping_command_show_git_stuff:\n    true\n'
    BUILT_IN_SAVE_LINKS_YAML_DEAFULT_TEXT = '\n# links to saves that already exists (DO NOT USE DISCORD FILE LINKS AS THEY EXPIRE AND WONT WORK), and you can have them as a choice in save_files option on /quick commands\n# follow the format (without the hashtag of course)\n#  - the_link_here a description of the link that can have spaces\nbuilt_in_save_links:\n  - https://drive.google.com/drive/folders/1wCBA0sZumgBRr3cDJm5BADRA9mfq4NpR?usp=sharing LBP EU Level Backup\n'
    BUILT_IN_DL_LINKS_YAML_DEAFULT_TEXT = '\n# links to dl_link that already exists (DO NOT USE DISCORD FILE LINKS AS THEY EXPIRE AND WONT WORK), and you can have them as a choice in dl_link options option on /quick commands\n# such as decrypted saves or images\n# follow the format (without the hashtag of course)\n#  - the_link_here a description of the link that can have spaces\nbuilt_in_dl_links:\n  - https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/2880px-Cat_August_2010-4.jpg Cute cat image\n'
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
# Watch https://youtu.be/HCjAK0QA_3w on how to get this file!
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
# or if its false then people will not be able to use bot in dms, besides pinging the bot
# Some people may not want people using bot in dms soo
allow_bot_usage_in_dms:
    true
# saves already on the console put here to allow for quicker resigns and cheats
# follow the format
# - TITLEID SAVEDIRNAME a_unique_name_for_a_save some description that can have spaces
built_in_saves:
  - CUSA12345 LBPXSAVE bigfart some cool description here
""")
            f.write(SHOULD_PING_COMMAND_SHOW_GIT_STUFF_YAML_DEAFULT_TEXT)
            f.write(BUILT_IN_SAVE_LINKS_YAML_DEAFULT_TEXT[1:])
            f.write(BUILT_IN_DL_LINKS_YAML_DEAFULT_TEXT[1:])
            
        raise Exception(f'bad config file or missing, got error {type(e).__name__}: {e} Please edit the config.yaml file') from None
    
    key = 'should_ping_command_show_git_stuff'
    if (x := my_config.get(key)) is None:
        with open('config.yaml','a') as f:
            f.write(SHOULD_PING_COMMAND_SHOW_GIT_STUFF_YAML_DEAFULT_TEXT)
        raise Exception(f'config.yaml updated with a new value `{key}` please check it out')
    if not isinstance(x,bool):
        raise Exception(f'{key} value should ethier be true or false, not {x}')


    links_types_keys = ('built_in_save_links',BUILT_IN_SAVE_LINKS_YAML_DEAFULT_TEXT),('built_in_dl_links',BUILT_IN_DL_LINKS_YAML_DEAFULT_TEXT)
    for key,yaml_default_text in links_types_keys:
        if not (x := my_config.get(key)):
            with open('config.yaml','a') as f:
                f.write(yaml_default_text)
            raise Exception(f'config.yaml updated with a new value `{key}` please check it out')
        if not isinstance(x,list):
            raise Exception(f'Bad key {key}, it should be of a list not {x}: {type(x)}, please follow the comment or yaml syntax to make it a list')
       
        temp_list = []
        for raw_entry in x:
            built_in_save_links_entry = tuple(raw_entry.split(' ',1))
            if len(built_in_save_links_entry) != 2:
                _raise_bad_url_format(key,raw_entry)
            if not(built_in_save_links_entry[0] and built_in_save_links_entry[1]):
                _raise_bad_url_format(key,raw_entry)
            temp_list.append(built_in_save_links_entry)
        
        my_config[key] = tuple(temp_list)
    
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
what ever happened to eZwizard1, was there ever a eZwizard1?
thesoundsofchildrenbeingtoturedinhell.png
$Afx/ProcessorID
ben you are getting too close to me
Суперкот
LittleBigPlanet 7ny% - Full Series Speedrun! (8:46:26)
BD0CB701D6079614D54DF907A08CDB10
PR]-<Q9*WxHsV8rcW!JuH7k_ug:T5ApX and the iv is _Y7]mD1ziyH#Ar=0
Tammy!
ITZTHATPLAYER was here.
I am a retarded horse
Like a somebodyyyyyyy
one two buckel my shoe
three four buckle some more
five six YOU STU{IID NI
Рита и Барсик
slipin_jimmy.mp4
ご飯を待ちすぎてアクビが出る猫(^^♪ 
""".strip().split('\n')


def get_a_stupid_silly_random_string_not_unique() -> str:
    return random_choice(SILLY_RANDOM_STRINGS_NOT_UNIQUE)
