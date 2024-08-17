import asyncio
import sys
import re
from typing import NamedTuple, Callable, Generator, Any, Sequence, Coroutine, assert_never
from enum import Enum
from pathlib import Path
from traceback import format_exc
from io import BytesIO
import time
import zipfile
import os
from stat import S_IWRITE
from datetime import datetime
from zlib import crc32 # put modules you need at the bottom of list for custom cheats, in correct block
import struct
import gzip
from sqlite3 import connect as sqlite3_connect
from ftplib import FTP,error_reply 
_boot_start = time.perf_counter()

from async_lru import alru_cache
import ujson as json
import aioshutil as shutil
from aiopath import AsyncPath
from psnawp_api import PSNAWP
from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound
from aiofiles.tempfile import TemporaryDirectory, TemporaryFile
import interactions
from sqlitedict import SqliteDict
import aiohttp
import aioftp
from ps4debug import PS4Debug
from PIL import Image
from lbptoolspy import far4_tools,install_mods_to_bigfart # put modules you need at the bottom of list for custom cheats, in correct block

from string_helpers import INT64_MAX_MIN_VALUES, UINT64_MAX_MIN_VALUES, INT32_MAX_MIN_VALUES, UINT32_MAX_MIN_VALUES, INT16_MAX_MIN_VALUES, UINT16_MAX_MIN_VALUES, INT8_MAX_MIN_VALUES, UINT8_MAX_MIN_VALUES,extract_drive_folder_id, extract_drive_file_id, is_ps4_title_id, make_folder_name_safe,pretty_time, load_config, CUSA_TITLE_ID, chunker, is_str_int, get_a_stupid_silly_random_string_not_unique, is_psn_name, PARENT_TEMP_DIR, pretty_bytes, pretty_seconds_words
from archive_helpers import get_archive_info, extract_single_file, filename_valid_extension,SevenZipFile, extract_full_archive, filename_is_not_an_archive
from gdrive_helpers import get_gdrive_folder_size, list_files_in_gdrive_folder, gdrive_folder_link_to_name, get_valid_saves_out_names_only, download_file, get_file_info_from_id, GDriveFile, download_folder, google_drive_upload_file, make_gdrive_folder, get_folder_info_from_id, delete_google_drive_file_or_file_permentaly
from savemount_py import PatchMemoryPS4900,MountSave,ERROR_CODE_LONG_NAMES,unmount_save,send_ps4debug,SUPPORTED_MEM_PATCH_FW_VERSIONS
from savemount_py.firmware_getter_from_libc_ps4 import get_fw_version
from git_helpers import check_if_git_exists,run_git_command,get_git_url,is_modfied,is_updated,get_remote_count,get_commit_count
from custom_crc import custom_crc
from dry_db_stuff import ps3_level_backup_to_l0_ps4
try:
    from custom_cheats.xenoverse2_ps4_decrypt.xenoverse2_ps4_decrypt import decrypt_xenoverse2_ps4, encrypt_xenoverse2_ps4
    from custom_cheats.rdr2_enc_dec.rdr2_enc_dec import auto_encrypt_decrypt
except ModuleNotFoundError as e:
    msg = f'{e}, maybe you need to add the --recurse-submodules to the git clone command `git clone https://github.com/Zhaxxy/eZwizard3-bot.git --recurse-submodules`'
    raise ModuleNotFoundError(msg) from None

try:
    __file__ = sys._MEIPASS
except:
    pass
else:
    __file__ = str(Path(__file__) / 'huh.huh')

CANT_USE_BOT_IN_DMS = '*You are not special, get the F of my DMs right now*\n*If you would like to use me, go to* **ITZGHOSTY420s or OFFICIAL SAVEBOT SERVERS**.'
CANT_USE_BOT_IN_TEST_MODE = '*Unlucky for some! But ItzGhosty420\'s Savebot is in* **TEST MODE**\n*Only staff has permission*'
WARNING_COULD_NOT_UNMOUNT_MSG = 'WARNING WARNING SAVE DIDNT UNMOUNT, MANUAL ASSITENCE IS NEEDED!!!!!!!!'

FILE_SIZE_TOTAL_LIMIT = 1_173_741_920
DL_FILE_TOTAL_LIMIT = 50_000_000 # 50mb
ATTACHMENT_MAX_FILE_SIZE = 26_214_400-1 # 25mib
ZIP_LOOSE_FILES_MAX_AMT = 14567+1
MAX_RESIGNS_PER_ONCE = 99
DOWNLOAD_CHUNK_SIZE = 1024
AMNT_OF_CHUNKS_TILL_DOWNLOAD_BAR_UPDATE = 50_000
PS4_ICON0_DIMENSIONS = 228,128

LBP3_PS4_L0_FILE_MAX_SIZE = 0x2_000_000 # too me 30 - 60 mins straight to find this!

CONFIG = load_config()
BASE_TITLE_ID = 'YAHY40786'
BASE_SAVEDATA_FOLDER = f'/user/home/{CONFIG["user_id"]}/savedata'
SAVE_FOLDER_ENCRYPTED = f'{BASE_SAVEDATA_FOLDER}/{BASE_TITLE_ID}'
MOUNTED_POINT = Path('/mnt/sandbox/NPXS20001_000')

PS4_SAVE_KEYSTONES = {
    'CUSA05350':b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb5\xaa\xa6\xdd\x19*\xfd\xdd\x8dy\x93\x8eJ\xce\x13\x7f\xd4H\x1d\xf1\x11\xbd\x18\x8a\xf3\x02\xc5l6j\x91\x12K\xcbZe\x06tj\x9d\x08\xd53;\xc1\x9cD\x96h\xff\xef\xe2\x18$W\x96\x8fQ\xa1\xc8<\x0b\x18\x96',
    'CUSA05088':b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00&\xedp\x94\xb2\x94\xa3\x9bc\xbd\x94\x11;\x06l\x93x\x9d\xc2K\xe2\xed\xfc\xd78\xff\xdd\x8dU\x86\xab\xd8N\x1dx8q\xcf\xd3\x0b\xfc\x8cr<il\xbbd\xbd\x17\xbe(?\x85Xn\xa5\xf4T\xe8s\xdcu\xaa',
    'CUSA08767':b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0fmj\x91\x05\x0e\xa7"\x9e3I\x94\x12].2\xe1\xbd\xff\x86\xac9\x0b{\xf0\x13\\\xa8\x83\x04o\xf0\x9c\xda\x9e64\x07H\x90o\xeb\xed\x86\xdc\x9aA$x\xe3\xbfZe\xb0\x9d\t\x92\xfa\xa4\xe8x\xb6\x1d\x8a'
}

XENOVERSE_TITLE_IDS = frozenset(('CUSA12394', 'CUSA05088', 'CUSA12330', 'CUSA04904', 'CUSA10051', 'CUSA12358', 'CUSA06202', 'CUSA05774', 'CUSA05350', 'CUSA12390', 'CUSA06208', 'CUSA05085'))

PARAM_SFO_SPECIAL_STRINGS = (
    'EFA288', 'EF A2 88', # L1
    'EFA289', 'EF A2 89', # L2
    'EFA28A', 'EF A2 8A', # L3
    'EFA28B', 'EF A2 8B', # R1
    'EFA28C', 'EF A2 8C', # R2
    'EFA28D', 'EF A2 8D', # R3
    'EFA28F', 'EF A2 8F', # Start
    'EFA28E', 'EF A2 8E', # Select
    'EFA292', 'EF A2 92', # PS Button
    'EFA2B9', 'EF A2 B9', # LStick
    'EFA2BA', 'EF A2 BA', # RStick
    'EFA284', 'EF A2 84', # Up
    'EFA285', 'EF A2 85', # Down
    'EFA286', 'EF A2 86', # Left
    'EFA287', 'EF A2 87', # Right
    'EFA282', 'EF A2 82', # Square
    'EFA281', 'EF A2 81', # Xross
    'EFA280', 'EF A2 80', # Circle
    'EFA283', 'EF A2 83', # Triangle
    'EFA3A3', 'EF A3 A3', # Platinum
    'EFA3A2', 'EF A3 A2', # Gold
    'EFA3A1', 'EF A3 A1', # Silver
    'EFA3A0', 'EF A3 A0', # Bronze
    'EFA3A4', 'EF A3 A4', # Black PS3
    'EFA3A5', 'EF A3 A5', # Black PS4
    'EFA3A6', 'EF A3 A6', # Black PSVITA
    'EFA2BC', 'EF A2 BC', # PS2
    'EFA3AD', 'EF A3 AD', # PS3
    'EFA3AE', 'EF A3 AE', # PS4
    'EFA3AF', 'EF A3 AF', # PSN
    'EFA3B0', 'EF A3 B0', # PSP
    'EFA3B1', 'EF A3 B1', # PSVITA
    'EFA2BD', 'EF A2 BD', # Video
    'EFA3AA', 'EF A3 AA', # PS Logo
    'EFA2BB', 'EF A2 BB', # Sing
    'EFA2BE', 'EF A2 BE', # Picture
    'EFA3B9', 'EF A3 B9', # Arrow and Cross
    'EFA3B5', 'EF A3 B5', # NY
    'EFA2BF', 'EF A2 BF', # Lock
    'EFA3AC', 'EF A3 AC', # Shop
    'EFA3AB', 'EF A3 AB', # Shop Round
    'EFA3B7', 'EF A3 B7', # PS Logo Round
    'EFA3B8', 'EF A3 B8', # Shop White
    'EFA2B6', 'EF A2 B6', # PS Plus Logo
    'EFA2B7', 'EF A2 B7', # PS Plus Logo White
    'EFA3A9', 'EF A3 A9', # Volume Mute
    'EFA395', 'EF A3 95', # Volume Low
    'EFA396', 'EF A3 96', # Volume Mid
    'EFA397', 'EF A3 97', # Volume Full
    'EFA390', 'EF A3 90', # Battery Empty
    'EFA391', 'EF A3 91', # Battery Low
    'EFA392', 'EF A3 92', # Battery Mid
    'EFA393', 'EF A3 93', # Battery Full
    'EFA39E', 'EF A3 9E', # Thumbs Up
    'EFA39D', 'EF A3 9D', # Chat
    'EFA39B', 'EF A3 9B', # Speaker
    'EFA39F', 'EF A3 9F', # Head
    'EFA39C', 'EF A3 9C', # Blue Dot
    'EFA2B8', 'EF A2 B8', # Warning
    'EFA1BE', 'EF A1 BE', # Verification
    'EFA1BB', 'EF A1 BB', # Green Dot
    'EFA1AA', 'EF A1 AA', # Red Warning Dot
    'EFA1A7', 'EF A1 A7', # Pin
    'EFA1BD', 'EF A1 BD', # Tick
    'EFA1B5', 'EF A1 B5', # Heart
    'EFA1B8', 'EF A1 B8', # Star
    'EFA1B7', 'EF A1 B7', # Repeat
    'EFA1B8', 'EF A1 B8', # Twitter
    'EFA1B0', 'EF A1 B0', # Twitch
    'EFA1B6', 'EF A1 B6', # YouTube
    'EFA1A0', 'EF A1 A0', # Tiny Verification
    'EFA1B5', 'EF A1 B5', # File
    'EFA1B1', 'EF A1 B1', # TV
    'EFA1B2', 'EF A1 B2', # Add Game
)

HUH = "Connection terminated. I'm sorry to interrupt you Elizabeth, if you still even remember that name. But I'm afraid you've been misinformed. You are not here to receive a gift, nor have you been called here by the individual you assume. Although you have indeed been called. You have all been called here. Into a labyrinth of sounds and smells, misdirection and misfortune. A labyrinth with no exit, a maze with no prize. You don't even realize that you are trapped. Your lust for blood has driven you in endless circles, chasing the cries of children in some unseen chamber, always seeming so near, yet somehow out of reach. But you will never find them, none of you will. This is where your story ends. And to you, my brave volunter, who somehow found this job listing not intended for you. Although there was a way out planned for you, I have a feeling that's not what you want. I have a feeling that you are right where you want to be. I am remaining as well, I am nearby. This place will not be remembered, and the memory of everything that started this can finally begin to fade away. As the agony of every tragedy should. And to you monsters trapped in the corridors: Be still and give up your spirits, they don't belong to you. For most of you, I believe there is peace and perhaps more waiting for you after the smoke clears. Although, for one of you, the darkest pit of Hell has opened to swallow you whole, so don't keep the devil waiting, old friend. My daughter, if you can hear me, I knew you would return as well. It's in your nature to protect the innocent. I'm sorry that on that day, the day you were shut out and left to die, no one was there to lift you up into their arms the way you lifted others into yours. And then, what became of you. I should have known you wouldn't be content to disappear, not my daughter. I couldn't save you then, so let me save you now. It's time to rest. For you, and for those you have carried in your arms. This ends for all of us. End communication."
# class TemporaryDirectory():
#     def __enter__(self):
#         self.new_path = Path(str(time.perf_counter()).replace('.','_'))
#         self.new_path.mkdir()
#         self.new_path = self.new_path.resolve()
#         return self.new_path

#     def __exit__(self, exc_type=None, exc_value=None, traceback=None):
#         await shutil.rmtree(self.new_path)


def is_in_test_mode() -> bool:
    try:
        return sys.argv[1].casefold() == '-t'
    except IndexError:
        return False


def is_user_bot_admin(ctx_author_id: str,/) -> bool:
    return ctx_author_id in CONFIG['bot_admins']


_token_getter = asyncio.Lock()
async def get_time_as_string_token() -> str:
    async with _token_getter:
        return datetime.now().strftime("%d_%m_%Y__%H_%M_%S")


async def set_up_ctx(ctx: interactions.SlashContext,*,mode = 0) -> interactions.SlashContext:
    nth_time = 1
    try:
        ctx.ezwizard_setup_done += 1
        nth_time = ctx.ezwizard_setup_done
    except AttributeError:
        await ctx.defer()
    # t = await ctx.respond(content=get_a_stupid_silly_random_string_not_unique())
    # await ctx.delete(t)
    ctx.ezwizard_mode = mode
    await log_message(ctx,f'*Pleast wait, ItzGhosty420\'s Bot is currently in use!\nPlease retry the command in a few moments*\n*Your* **{nth_time}st** *time trying a command, Please do not try multiple times!*',_do_print = False)
    ctx.ezwizard_setup_done = 1
    return ctx


async def log_message(ctx: interactions.SlashContext, msg: str,*,_do_print: bool = True):
    if _do_print:
        print(msg)

    channel = ctx.channel or ctx.author
    try:
        msg = ctx.omljustusethe0optionsaccountid + msg
    except AttributeError:
        pass
    
    
    for msg_chunk in chunker(msg,2000-1-3):
        if ctx.expired:
            await channel.send(msg_chunk)
        else:
            await ctx.edit(content=msg_chunk)

async def log_message_tick_tock(ctx: interactions.SlashContext, msg: str):
    """
    Use this when you know its gonna wait for a while, MAKE SURE YOU USE `asyncio.create_task` and cancel the task as soon as long task is done
    """
    await log_message(ctx, msg)
    
    tick = 0
    while True:
        if ctx.expired:
            await log_message(ctx, f'{msg}, *over 15 minutes spent here, likely bot is stuck and needs reboot* (including the PS4)', _do_print=False)
            while True:
                await asyncio.sleep(10)
        await log_message(ctx, f'{msg} {tick} *seconds spent here*', _do_print=False)
        await asyncio.sleep(10)
        tick += 10
    
    
async def log_user_error(ctx: interactions.SlashContext, error_msg: str):
    # if error_msg == 'Theres too many people using the bot at the moment, please wait for a spot to free up':
        # # await ctx.send(get_a_stupid_silly_random_string_not_unique(),ephemeral=False)
        # return
    print(f'user bad ##################\n{error_msg}')
    channel = ctx.channel or ctx.author
    try:
        error_msg = ctx.omljustusethe0optionsaccountid + error_msg
    except AttributeError:
        pass
    full_msg = f'*Yo* <@{ctx.author_id}><a:pepesayshi:1272147595426271305>\n{error_msg}'
    
    first_time = True
    for msg_chunk in chunker(full_msg,2000-1-3):
        
        if ctx.expired:
            await channel.send(msg_chunk,ephemeral=False)
        else:
            if first_time:
                placeholder_meesage_to_allow_ping_to_actually_ping_the_user = await ctx.send(get_a_stupid_silly_random_string_not_unique(),ephemeral=False)
            await ctx.send(msg_chunk,ephemeral=False) 
            if first_time:
                await ctx.delete(placeholder_meesage_to_allow_ping_to_actually_ping_the_user)
        first_time = False
        

    await update_status()

async def log_user_success(ctx: interactions.SlashContext, success_msg: str, file: str | None = None):
    print(f'{ctx.user} id: {ctx.author_id} *Has started a new command* {success_msg}')
    channel = ctx.channel or ctx.author
    try:
        success_msg = ctx.omljustusethe0optionsaccountid + success_msg
    except AttributeError:
        pass
    full_msg = f'**Yo!** <@{ctx.author_id}> <a:pepesayshi:1272147595426271305>\n{success_msg}'
    
    first_time = True
    triple_backtick_start = False
    for msg_chunk in chunker(full_msg,2000-1-3):
        if not first_time:
            file = None
        if ctx.expired:
            await channel.send(msg_chunk,ephemeral=False, file=file)
        else:
            if first_time:
                placeholder_meesage_to_allow_ping_to_actually_ping_the_user = await ctx.send(get_a_stupid_silly_random_string_not_unique(),ephemeral=False)
            await ctx.send(msg_chunk,ephemeral=False, file=file) 
            if first_time:
                await ctx.delete(placeholder_meesage_to_allow_ping_to_actually_ping_the_user)
        first_time = False

    await update_status()


class ChangeSaveIconOption(Enum):
    KEEP_ASPECT_NEAREST_NEIGHBOUR = 1
    IGNORE_ASPECT_NEAREST_NEIGHBOUR = 2
    KEEP_ASPECT_BILINEAR = 3
    IGNORE_ASPECT_BILINEAR = 4 


class CleanEncryptedSaveOption(Enum):
    DONT_DELETE_ANYTHING = 0
    DELETE_ALL_BUT_KEEP_SCE_SYS = 1
    DELETE_ALL_INCLUDING_SCE_SYS = 2

class SpecialSaveFiles(Enum):
    MINECRAFT_CUSTOM_SIZE_MCWORLD = 0
    ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT = 1
    LBP3_LEVEL_BACKUP = 2
    LBP3_ADV_BACKUP = 3

class Lbp3BackupThing(NamedTuple):
    title_id: str
    start_of_file_name: str
    level_name: str
    level_desc: str
    is_adventure: bool
    new_blocks_size: int
    
class SaveMountPointResourceError(Exception):
    """
    Raised when theres no more free resources
    """


#


class _ResourceManager:
    def __init__(self, resources):
        self.resources = resources
        self.lock = asyncio.Lock()
        self.used_resources = set()

    async def acquire_resource(self):
        async with self.lock:
            available_resources = set(self.resources) - self.used_resources
            if not available_resources:
                raise SaveMountPointResourceError
            resource = next(iter(available_resources))
            self.used_resources.add(resource)
            return resource

    async def release_resource(self, resource):
        async with self.lock:
            if resource not in self.used_resources:
                raise SaveMountPointResourceError
            self.used_resources.remove(resource)

    async def get_free_resources_count(self):
        async with self.lock:
            return len(self.resources) - len(self.used_resources)
SAVE_DIRS = ('save0', 'save1', 'save2', 'save3', 'save4', 'save5', 'save6', 'save7', 'save8', 'save9', 'save10', 'save11')

_save_mount_points = _ResourceManager(SAVE_DIRS)

async def get_save_str() -> str:
    return await _save_mount_points.acquire_resource()

async def free_save_str(save_str: str,/) -> None:
    return await _save_mount_points.release_resource(save_str)

async def get_amnt_free_save_strs() -> int:
    return await _save_mount_points.get_free_resources_count()

mounted_saves_at_once = asyncio.Semaphore(12) # 3 i sadly got an unmount error, and with 2 too

class PS4AccountID:
    __slots__ = ('_account_id',)
    def __init__(self, account_id: str):
        if len(account_id) != 16:
            raise ValueError('Invalid account id, length is not 16')
        int(account_id,16)
        self._account_id = account_id.casefold()
    
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.account_id!r})'
    
    def __bytes__(self) -> bytes:
        return bytes.fromhex(self.account_id)[::-1]

    def __hash__(self) -> int:
        return hash(self.account_id)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value,PS4AccountID):
            return NotImplemented
        return self.account_id == value.account_id
    
    def __bool__(self) -> bool:
        return self.account_id != '0000000000000000'

    @property
    def to_2_uints32(self) -> tuple[bytes,bytes]:
        return bytes.fromhex(self.account_id[8:16])[::-1],bytes.fromhex(self.account_id[:8])[::-1]
    
    @property
    def account_id(self) -> str:
        return self._account_id

    @classmethod
    def from_bytes(cls,account_id_bytes: bytes):
        return cls(account_id_bytes[::-1].hex())

    @classmethod
    def from_account_id_number(cls, account_id_int: str | int):
        return cls(f'{int(account_id_int):016x}')

def remove_pc_user_from_path(the_path: object,/) -> object:
    if not isinstance(the_path,(Path,AsyncPath)):
        return the_path
    return the_path.relative_to(PARENT_TEMP_DIR)

class CheatFunc(NamedTuple):
    func: Coroutine[None, None, str | None]
    kwargs: dict[str,Any]

    def pretty(self) -> str:
        return f"```py\nawait {self.func.__name__}({', '.join(f'{a}={remove_pc_user_from_path(b)!r}' for a,b in self.kwargs.items())})```"

class CheatFuncResult(NamedTuple):
    savename: str | None
    gameid: str | None


class DecFunc(NamedTuple):
    func: Coroutine
    kwargs: dict[str,Any]

    def pretty(self) -> str:
        return f"```py\nawait {self.func.__name__}({', '.join(f'{a}={remove_pc_user_from_path(b)!r}' for a,b in self.kwargs.items())})```"

    @property
    def __doc__(self) -> str | None:
        return self.func.__doc__


def make_ps4_path(account_id: PS4AccountID, title_id: str | Path) -> Path:
    return Path('PS4/SAVEDATA',account_id.account_id,title_id)


def initialise_database():
    with SqliteDict("user_stuff.sqlite", tablename="total_amnt_used") as db:
        try:
            db["total_amnt_used_value"]
        except KeyError:
            db["total_amnt_used_value"] = 0
        db.commit()
    with SqliteDict("user_stuff.sqlite", tablename="total_runtime") as db:
        try:
            db["total_runtime"]
        except KeyError:
            db["total_runtime"] = 0
        db.commit()

def get_total_runtime() -> int:
    with SqliteDict("user_stuff.sqlite", tablename="total_runtime") as db:
        return db["total_runtime"]

def set_total_runtime(new_runtime_value: int ):
    with SqliteDict("user_stuff.sqlite", tablename="total_runtime") as db:
        db["total_runtime"] = new_runtime_value
        db.commit()

def get_user_account_id(author_id: str):
    with SqliteDict("user_stuff.sqlite", tablename="user_account_ids") as db:
        return db[author_id]

def add_user_account_id(author_id: str,new_account_id: str):
    author_id = str(author_id)
    new_account_id = str(new_account_id)
    with SqliteDict("user_stuff.sqlite", tablename="user_account_ids") as db:
        db[author_id] = new_account_id
        db.commit()

def add_1_total_amnt_used():
    with SqliteDict("user_stuff.sqlite", tablename="total_amnt_used") as db:
        db["total_amnt_used_value"] += 1
        db.commit()

def get_total_amnt_used() -> int:
    with SqliteDict("user_stuff.sqlite", tablename="total_amnt_used") as db:
        return db["total_amnt_used_value"]


def save_url(author_id: str, url: str, url_id: int):
    if (not isinstance(url_id,int)) or url_id <= 1:
        raise TypeError(f'Invalid url_id {url_id}')
    author_id = str(author_id)
    url_id = str(url_id)
    with SqliteDict("user_stuff.sqlite", tablename="user_saved_urls_ids") as db:
        try:
            a = db[author_id]
        except KeyError:
            db[author_id] = {url_id:url}
        else:
            a.update({url_id:url})
            db[author_id] = a
        db.commit()


def get_saved_url(author_id: str, url_id: int) -> str:
    if (not isinstance(url_id,int)) or url_id <= 1:
        raise TypeError(f'Invalid url_id {url_id}')
    author_id = str(author_id)
    url_id = str(url_id)
    with SqliteDict("user_stuff.sqlite", tablename="user_saved_urls_ids") as db:
        a = db[author_id]
        return a[url_id]


def delete_saved_urls(author_id: str):
    with SqliteDict("user_stuff.sqlite", tablename="user_saved_urls_ids") as db:
        try:
            del db[str(author_id)]
        except KeyError:
            pass
        db.commit()

def get_all_saved_urls(author_id: str) -> dict[str,str]:
    with SqliteDict("user_stuff.sqlite", tablename="user_saved_urls_ids") as db:
        try:
            return db[author_id]
        except KeyError:
            return {}


def is_user_verbose_mode(author_id: str) -> bool:
    author_id = str(author_id)
    with SqliteDict("user_stuff.sqlite", tablename="user_verbose_booleans") as db:
        try:
            return db[author_id]
        except KeyError:
            db[author_id] = False
            return False


def set_user_verbose_mode(author_id: str, verbose_mode: bool):
    author_id = str(author_id)
    with SqliteDict("user_stuff.sqlite", tablename="user_verbose_booleans") as db:
        db[author_id] = verbose_mode
        db.commit()


def make_error_message_if_verbose_or_not(ctx_author_id: str, message_1: str, message_2: str) -> str:
    if is_user_verbose_mode(ctx_author_id):
        leader = ''
        error_msg = f'```{format_exc().replace("Traceback (most recent call last):",get_a_stupid_silly_random_string_not_unique()+" (most recent call last):")}```'
    else:
        leader = '*Your save is basically fucked...\n'
        error_msg = f'```{sys.exc_info()[1]}```'
    
    if error_msg == '```' + '```':
        error_msg = f'```{sys.exc_info()[0].__name__}```'
    
    return leader + f'{message_1} reason:\n{error_msg}\n {message_2}'


user_cheat_chains = {}
def add_cheat_chain(author_id: str, cheat_function: CheatFunc):
    global user_cheat_chains
    author_id = str(author_id)
    user_cheat_chains.setdefault(author_id,[]).append(cheat_function)


def get_cheat_chain(author_id: str) -> list[CheatFunc]:
    global user_cheat_chains
    author_id = str(author_id)
    return user_cheat_chains.setdefault(author_id,[])

def delete_chain(author_id: str):
    author_id = str(author_id)
    global user_cheat_chains
    try:
        del user_cheat_chains[author_id]
    except KeyError:
        pass


def account_id_from_str(account_id: str, author_id: str,ctx: interactions.SlashContext) -> str | PS4AccountID:
    """
    Returns a PS4AccountID if success, else returns str as error message
    """
    if account_id == '0':
        try:
            return PS4AccountID(get_user_account_id(author_id))
        except KeyError:
            return '*You dont have any account id saved to the database!, try running the* `/my_account_id` again*'
    elif account_id == '1':
        return PS4AccountID('0000000000000000')

    try:
        my_account_id = PS4AccountID(account_id)
        try:
            my_account_id_for_my_acc = PS4AccountID(get_user_account_id(author_id))
        except KeyError: pass
        else:
            if my_account_id_for_my_acc == my_account_id:
                ctx.omljustusethe0optionsaccountid = '*You dont have to manually type in your account id, Put 0 in the Account ID option!*\n'
        return my_account_id
    except ValueError:
        return f'*Are you sure you spelled your PSN Username Correctly boss?*\n**{psn_name}** *is not a valid PSN username*<:whatthe:1272145776344305757>'


def list_ps4_saves(folder_containing_saves: Path,/) -> Generator[tuple[Path,Path],None,None]:
    for filename in folder_containing_saves.rglob('*'):
        if is_ps4_title_id(filename.parent.name) and filename.suffix == '.bin' and filename.is_file() and Path(filename.with_suffix('')).is_file():
            yield filename,Path(filename.with_suffix(''))


async def ps4_life_check(ctx: interactions.SlashContext | None = None):
    channel = ctx.channel or ctx.author
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    try:
        await ps4.notify('Hello hello ello, Bot Ping Motherfucka')
    except Exception:
        try:
            await channel.send(HUH) if ctx else None
        except Exception:
            pass
        await ctx.bot.stop()
        assert_never('bot should be ended')
    


async def extract_ps4_encrypted_saves_archive(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID, archive_name: Path) -> str:
        await log_message(ctx,f'*Checking* {link} *if valid archive*')
        try:
            zip_info = await get_archive_info(archive_name)
        except Exception as e:
            return f'*Invalid archive after downloading it* {link}, *error when unpacking* {type(e).__name__}: {e}'

        if zip_info.total_uncompressed_size > FILE_SIZE_TOTAL_LIMIT:
            return f'*The decompressed* {link} *is too big*\n*Please note the limit is* **{pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}**'
        
        await log_message(ctx,f'*Having a quick look for saves in* {link}')
        ps4_saves: list[tuple[Path,Path]] = []
        for zip_file in zip_info.files.values():
            if not zip_file.is_file: continue
            if not is_ps4_title_id(zip_file.path.parent.name): continue
            if zip_file.path.suffix != '.bin': continue
            if '__MACOSX' in zip_file.path.parts[:-1]: continue # if you do happen to have saves in this folder, then tough luck
            if zip_file.path.name.startswith('._'): continue
            
            white_file = zip_file.path.with_suffix('')
            if not zip_info.files.get(white_file): continue
            if zip_file.size != 96:
                return f'*Invalid bin file* {zip_file.path} *found in* {link}'

            ps4_saves.append((zip_file.path,white_file))
        if not ps4_saves:
            return f'*Oops, I couldnt find anything in your link*<:Cry:1272144629373997106>\n {link}\n*Please make sure your* **CUSAXXXX** *folder only has your* **Two** *Savefiles inside it!*\n*If there is multiple folders/savefiles inside your folder, I will not find your desired savefile!*'
        
        try:
            ctx.special_save_files_thing
        except AttributeError:
            pass
        else:
            if ctx.special_save_files_thing == SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT:#
                if len(ps4_saves) != 1:
                    return f'*The archive* {link} *has more then one save, we can only do 1 save at once for encrypt and import commands, please delete the other saves in this. If you want to upload the same decrypted save to mutiple encrypted saves (which you probably dont) set allow_mulit_enc to Yes*'
        
        if len(ps4_saves) > MAX_RESIGNS_PER_ONCE:
            return f'*The archive* {link} *has too many saves* {len(ps4_saves)}, *the max is* {MAX_RESIGNS_PER_ONCE} *remove* {len(ps4_saves) - MAX_RESIGNS_PER_ONCE} *saves and try again*'
        
        for bin_file,white_file in ps4_saves:
            pretty_dir_name = make_folder_name_safe(bin_file.parent)
            new_path = Path(output_folder,pretty_dir_name,make_ps4_path(account_id,bin_file.parent.name))
            new_path.mkdir(exist_ok=True,parents=True) # TODO look into parents=True
            await log_message(ctx,f'*Mc Booooming!!* {white_file} {link}')
            try:
                await extract_single_file(archive_name,white_file,new_path)
                await extract_single_file(archive_name,bin_file,new_path)
            except Exception as e:
                return f'*Oops.. Invalid archive after downloading it* {link}, *error when unpacking* {type(e).__name__}: {e}'
        return ''


async def get_direct_dl_link_from_mediafire_link(url: str) -> str:
    url_origin = url
    async with aiohttp.ClientSession() as session:
        for _ in range(10): # give it ten tries
            async with session.get(url) as response:
                if 'Content-Disposition' in response.headers:
                    # This is the file
                    break
                for line in (await response.text()).splitlines():
                    m = re.search(r'href="((http|https)://download[^"]+)', line)
                    if m:
                        url = m.groups()[0]
                        break
                else: # no break
                    raise Exception(f'Permission denied: {url_origin}. Maybe you need to change permission over Anyone with the link')
        else: # no break
            raise Exception(f'Too many tries on {url_origin} to get download link')
        return url


class ZapritFishKnownLinkError(str):
    def __new__(cls, value: object):
        obj = str.__new__(cls, value)
        return obj


async def download_direct_link(ctx: interactions.SlashContext,link: str, donwload_location: Path, validation: Callable[[str], str] = None, max_size: int = FILE_SIZE_TOTAL_LIMIT) -> Path | str | ZapritFishKnownLinkError:
    if not validation:
        validation = lambda x: ''

    new_link = extract_drive_file_id(link)
    if new_link:
        await log_message(ctx,f'*Working Magic gathering the file metadata from* {link}')
        try:
            zip_file = await get_file_info_from_id(new_link)
        except Exception as e:
            return f'**THIS LINK IS NOT PUBLIC** <a:pespepenotfunnyt:1272150300114944062>\n {link}\n*Please click share on your link* & **Give access to anybody with this link** <:Nice:1272144601033211924>'
        if validation_result := validation(zip_file.file_name_as_path):
            return f'{link} failed validation reason: {validation_result}'
        
        if zip_file.size > max_size:
            return f'The file {link} is too big, we only accept {pretty_bytes(max_size)}, if you think this is wrong please report it'
        if zip_file.size < 1:
            return f'The file {link} is too small lmao wyd'

        archive_name = Path(donwload_location,zip_file.file_name_as_path.name)
        try:
            await log_message(ctx,f'*Working Magic with your* {zip_file.file_name_as_path.name} *from* {link}')
            await download_file(zip_file.file_id,archive_name)
        except Exception:
            return f'blud thinks hes funny'
        return archive_name

    if extract_drive_folder_id(link):
        return f'For this option we do not take in folder urls {link}'
    
    link = link.replace('media.discordapp.net','cdn.discordapp.com')
    
    if 'mediafire.com' in link:
        await log_message(ctx,f'Getting direct download link from mediafire url {link}')
        try:
            link = await get_direct_dl_link_from_mediafire_link(link)
        except Exception as e:
            return f'Bad mediafire link {type(e).__name__}: {e} (we dont accept folders, if you passed in a folder)'
    # session_timeout = None
    # if link.startswith('https://zaprit.fish/dl_archive/'):
        # session_timeout = aiohttp.ClientTimeout(total=None,sock_connect=60*10,sock_read=60*10)
    # timeout=session_timeout in the aiohttp.ClientSession()
    async with aiohttp.ClientSession() as session:
        try:
            for try_attempt in range(6):
                async with session.get(link) as response:
                    if response.status == 200:
                        try:
                            filename = response.content_disposition.filename
                        except AttributeError:
                            filename = link.split('/')[-1].split('?')[0]
                        if not filename:
                            filename = link.split('/')[-1].split('?')[0]
                        if validation_result := validation(filename):
                            return f'{link} *failed validation reason:* {validation_result}'
                        file_size = response.headers.get('*Content-Length*')
                        if link.startswith('https://zaprit.fish/dl_archive/') or link.startswith('https://zaprit.fish/icon/'):
                            file_size = 3
                        if file_size is None:
                            return '*There was no Content-Length header*'
                        try:
                            file_size = int(file_size)
                        except ValueError:
                            return f'*Content-Length* {file_size!r} *was not a valid number*'
                        if file_size > max_size:
                            return f'*The file* {link} *is too big, I only accept* {pretty_bytes(max_size)}'
                        if file_size < 2:
                            return f'*The file {link} is too small man whats the fuck even is this lol*'
                        downloaded_size = 0
                        chunks_done = 0
                        direct_zip = Path(donwload_location,filename)
                        with open(direct_zip, 'wb') as f:
                            while True:
                                if not(chunks_done % AMNT_OF_CHUNKS_TILL_DOWNLOAD_BAR_UPDATE):
                                    await log_message(ctx,f'*Ive downloaded* {link} {pretty_bytes(downloaded_size)}')
                                chunk = await response.content.read(DOWNLOAD_CHUNK_SIZE)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded_size += DOWNLOAD_CHUNK_SIZE
                                chunks_done += 1
                                if downloaded_size > max_size:
                                    return f'*Oops* {link} *is too big,* *I only accept* {pretty_bytes(max_size)}'
                        await log_message(ctx,f'*Ive downloaded* {link} {pretty_bytes(downloaded_size)}')
                        break
                    elif (response.status == 524) and link.startswith('https://zaprit.fish/dl_archive/'):
                        await log_message(ctx,f'*Slot ID* {link} *has never been downloaded before, so waiting 2 minutes to try downloading it again*')
                        await asyncio.sleep(2*60)
                        continue
                    else:
                        if link.startswith('https://zaprit.fish/dl_archive/') and (b"Level not found" in (await response.content.read(10_000_000))):
                            return ZapritFishKnownLinkError(f'The slot id {link} doesn\'t exist')
                        return f'*Oops, Failed to download* {link}. **Status code:** {response.status}'
            else: # no break, or return in this case
                return ZapritFishKnownLinkError(f'*Took too many tries to download* {link},\n*Retry the command*')
        except Exception as e:
            return make_error_message_if_verbose_or_not(ctx.author_id,f'*Invalid url* {link}','*maybe you copied the wrong link?*')
    return direct_zip



async def download_decrypted_savedata0_folder(ctx: interactions.SlashContext,link: str, output_folder: Path, allow_any_folder: bool, unpack_first_root_folder: bool) -> str:
    """
    For now at least, we are only gonna allow one encryption at a time
    """
    new_link = extract_drive_folder_id(link)
    if new_link:
        await log_message(ctx,f'*Grabbing files metadata from folder* {link}')
        try:
            raw_files = await list_files_in_gdrive_folder(new_link,await gdrive_folder_link_to_name(new_link),False)
        except Exception as e:
            return f'**THIS LINK IS NOT PUBLIC**<a:pespepenotfunnyt:1272150300114944062>\n {link}\n*Please click share on your link* & **Give access to anybody with this link**<:Nice:1272144601033211924>'
        if not allow_any_folder:
            await log_message(ctx,f'*Looking for your savedata0 folder in* {link}')
            seen_savedata0_folders: set[GDriveFile] = {
                p
                for p in raw_files.values()
                if (not p.is_file) and (p.file_name_as_path.parts.count('savedata0') == 1) and ('__MACOSX' not in p.file_name_as_path.parts) and (not p.file_name_as_path.name.startswith('._'))
            }

            if not seen_savedata0_folders:
                return f'*Could not find any decrypted saves in* {link}, *make sure to put the decrypted save contents in a savedata0 folder and upload that, or use the /raw_encrypt_folder_type_2 command*'

            if len(seen_savedata0_folders) > 1:
                return f'*Too many decrypted saves in* {link},\n**Please note:**\n*Please make sure you have a* **Zipped CUSAXXXX & SaveData Folder** *If encrypting multiple files!\nOtherwise I only support encrypting* **1 ** *Save per command boss!*'
            for savedata0_folder in seen_savedata0_folders:
                pass
        else:
            savedata0_folder = await get_folder_info_from_id(new_link)
        await log_message(ctx,f'*Checking if* {link} *savedata0 folder is too big or not*')
        try:
            test = await get_gdrive_folder_size(savedata0_folder.file_id)
        except Exception:
            return 'blud thinks hes funny'
        if test[0] > FILE_SIZE_TOTAL_LIMIT:
            return f'*The decrypted save* {link} *is too big*\n*Maybe you uploaded a wrong file? max is* {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}'
        if test[1] > ZIP_LOOSE_FILES_MAX_AMT:
            return f'*The decrypted save* {link} *has too many loose files* ({test[1]}), *max is* {ZIP_LOOSE_FILES_MAX_AMT} *loose files*'

        await log_message(ctx,f'*I am downloading* {link} *savedata0 folder*')
        Path(output_folder,'savedata0').mkdir(parents=True,exist_ok=True)# TODO maybe i dont gotta do this, but i am
        new_savedata0_folder_made = Path(output_folder,'savedata0')
        try:
            await download_folder(savedata0_folder.file_id,new_savedata0_folder_made)
        except Exception:
            return 'blud thinks hes funny'
        if unpack_first_root_folder:
            await log_message(ctx,f'*Doing magic with the file management in your save* {link}')
            checker = AsyncPath(new_savedata0_folder_made)
            thing_count = 0
            async for thing in checker.iterdir():
                thing_count += 1
            if thing_count != 1:
                return ''

            if await thing.is_file(): # This is incase a user sends a folder with a single file
                return ''

            async for file_name in thing.iterdir():
                await shutil.move(file_name,new_savedata0_folder_made)
            
        return ''
    
    async with TemporaryDirectory() as tp:
        direct_zip = await download_direct_link(ctx,link,tp,filename_valid_extension)
        if isinstance(direct_zip,str):
            return direct_zip
        return await extract_savedata0_decrypted_save(ctx,link,output_folder,direct_zip,allow_any_folder,unpack_first_root_folder)



async def extract_savedata0_decrypted_save(ctx: interactions.SlashContext,link: str, output_folder: Path, archive_name: Path, allow_any_folder: bool, unpack_first_root_folder: bool) -> str:
    await log_message(ctx,f'*Checking* {link} *if valid archive*')
    try:
        a = await get_archive_info(archive_name)
    except Exception as e:
        return f'*Invalid archive after downloading it* {link}, *error when unpacking* {type(e).__name__}: {e}'

    if a.total_uncompressed_size > FILE_SIZE_TOTAL_LIMIT:
        return f'*The decompressed* {link} *is too big, the max is* {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}'

    if len(a.files) > ZIP_LOOSE_FILES_MAX_AMT:
        return f'*The decompressed* {link} *has too many loose files* ({len(a.files)}),\n **max is** {ZIP_LOOSE_FILES_MAX_AMT} **loose files**'
    if not allow_any_folder:
        await log_message(ctx,f'*Scanning for decrypted saves in* {link}')
        seen_savedata0_folders: set[SevenZipFile] = {
            p
            for p in a.files.values()
            if (not p.is_file) and (p.path.parts.count('savedata0') == 1) and ('__MACOSX' not in p.path.parts) and (not p.path.name.startswith('._'))
        }
        if not seen_savedata0_folders:
            return f'*Could not find any decrypted saves in* {link}, *make sure to put the decrypted save contents in a savedata0 folder and archive that, or use the /raw_encrypt_folder_type_2 command*'

        if len(seen_savedata0_folders) > 1:
            return f'*Too many decrypted saves in* {link}, *we only support encrypting one save per command*'

        for savedata0_folder in seen_savedata0_folders:
            pass
        
        await log_message(ctx,f'*Nearly done, Extracting savedata0* {link}')
        try:
            await extract_single_file(archive_name,savedata0_folder.path,output_folder,'x')
        except Exception as e:
            return f'*Invalid archive after downloading* {link}, **error** {type(e).__name__}: {e}'
        if not savedata0_folder.path == Path('savedata0'):
            await log_message(ctx,f'*Doing some file management with* {link}')
            await shutil.move(Path(output_folder, savedata0_folder.path),output_folder)
            if savedata0_folder.path.parts[0] != Path('savedata0'):
                await shutil.rmtree(Path(output_folder,savedata0_folder.path.parts[0]))

        return ''
    else:
        await log_message(ctx,f'*Extracting decrypted save from* {link}')
        new_savedata0_folder_made = Path(output_folder,'savedata0')
        new_savedata0_folder_made.mkdir(parents=True, exist_ok=True)
        await extract_full_archive(archive_name,new_savedata0_folder_made,'x')
        if unpack_first_root_folder:
            await log_message(ctx,f'*Doing some file management with* {link}')
            checker = AsyncPath(new_savedata0_folder_made)
            thing_count = 0
            async for thing in checker.iterdir():
                thing_count += 1
            if thing_count != 1:
                return ''
            
            if await thing.is_file(): # This is incase a user sends a zip with a single file
                return ''
            
            async for file_name in thing.iterdir():
                await shutil.move(file_name,new_savedata0_folder_made)
        
async def download_ps4_saves(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID) -> str:
    """\
    function to download ps4 encrypted saves from a user given link, if anything goes wrong then a string error is returned, otherwise empty string (falsely).
    the output_folder will contain the ps4 encrypted saves, itll be in a nice format that is ready for sending
    """
    new_link = extract_drive_folder_id(link)
    if new_link:
        await log_message(ctx,f'*Getting files metadata from folder*\n {link}')
        try:
            raw_files = await list_files_in_gdrive_folder(new_link,await gdrive_folder_link_to_name(new_link))
        except Exception as e:
            return f'**THIS LINK IS NOT PUBLIC**<a:pespepenotfunnyt:1272150300114944062>\n {link}\n*Please click share on your link* & **Give access to anybody with this link**<:Nice:1272144601033211924>'
        await log_message(ctx,f'*Looking for saves in the folder* {link}')
        ps4_saves = get_valid_saves_out_names_only(raw_files.values())
        
        if not ps4_saves:
            return f'*Oops, I couldnt find anything in your link*<:Cry:1272144629373997106>\n {link}\n*Please make sure your* **CUSAXXXX** *folder only has your* **Two** *Savefiles inside it!*\n*If there is multiple folders/savefiles inside your folder, I will not find your desired savefile!*'
        total_ps4_saves_size = sum(x.bin_file.size + x.white_file.size for x in ps4_saves)

        try:
            ctx.special_save_files_thing
        except AttributeError:
            pass
        else:
            if ctx.special_save_files_thing == SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT:#
                if len(ps4_saves) != 1:
                    return f'*The folder* {link} *has more then one save, we can only do 1 save at once for encrypt and import commands, if you want to upload the same decrypted save to mutiple encrypted saves set allow_mulit_enc to Yes*'

        if len(ps4_saves) > MAX_RESIGNS_PER_ONCE:
            return f'*The folder* {link} *has too many saves* {len(ps4_saves)}, *the max is* {MAX_RESIGNS_PER_ONCE} *remove* {len(ps4_saves) - MAX_RESIGNS_PER_ONCE} *saves and try again*'

        if total_ps4_saves_size > FILE_SIZE_TOTAL_LIMIT:
            return f'*The total number of saves in* {link} *is too big, the max size of saves is* {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}, {pretty_bytes(total_ps4_saves_size)} *is too big*'

        for bin_file,white_file in ps4_saves:
            if bin_file.size != 96:
                return f'*Invalid bin file* {bin_file.file_name_as_path} *found in* {link}'
            
            new_white_path = Path(output_folder, make_folder_name_safe(white_file.file_name_as_path.parent), make_ps4_path(account_id,white_file.file_name_as_path.parent.name),white_file.file_name_as_path.name)
            new_bin_path = Path(output_folder, make_folder_name_safe(bin_file.file_name_as_path.parent), make_ps4_path(account_id,bin_file.file_name_as_path.parent.name),bin_file.file_name_as_path.name)

            await log_message(ctx,f'*Downloading* {white_file.file_name_as_path} *from* {link}')
            try:
                await download_file(white_file.file_id,new_white_path)
                await download_file(bin_file.file_id,new_bin_path)
            except Exception:
                return 'blud thinks hes funny'
        return ''


    async with TemporaryDirectory() as tp:
        direct_zip = await download_direct_link(ctx,link,tp,filename_valid_extension)
        if isinstance(direct_zip,str):
            if 'failed validation reason:' in direct_zip: # TODO this method means if i change the error msg in download_direct_link and not this, then this if statement never happens
                return f'{direct_zip} \n**(do not put decrypted saves into the save_files option)**'
            return direct_zip
        return await extract_ps4_encrypted_saves_archive(ctx,link,output_folder,account_id,direct_zip)

async def _upload_encrypted_to_ps4(bin_file: Path, white_file: Path, ftp_bin: str, ftp_white: str):
    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
        # await log_message(ctx,f'Pwd to {SAVE_FOLDER_ENCRYPTED}')
        await ftp.change_directory(SAVE_FOLDER_ENCRYPTED)
        # await log_message(ctx,f'Uploading {pretty_save_dir} to PS4')
        await ftp.upload(bin_file,ftp_bin,write_into=True)
        await ftp.upload(white_file,ftp_white,write_into=True)
async def upload_encrypted_to_ps4(ctx: interactions.SlashContext, bin_file: Path, white_file: Path,parent_dir: Path, save_dir_ftp: str):
    ftp_bin = f'{save_dir_ftp}.bin'
    ftp_white = f'sdimg_{save_dir_ftp}'
    pretty_save_dir = white_file.relative_to(parent_dir)
    # await log_message(ctx,'Ensuring base save exists on PS4 before uploading')
    # async with MountSave(ps4,mem,int(CONFIG['user_id'],16),BASE_TITLE_ID,save_dir_ftp) as mp:
        # pass
    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,'*Please Wait*'))
    async with mounted_saves_at_once:
        tick_tock_task.cancel()
        await log_message(ctx,f'*Uploading* {pretty_save_dir} *to console*')
        custon_decss = lambda: asyncio.run(_upload_encrypted_to_ps4(bin_file, white_file, ftp_bin, ftp_white))
        await asyncio.get_running_loop().run_in_executor(None,custon_decss)


async def _download_encrypted_from_ps4(bin_file_out: Path, white_file_out: Path, ftp_bin: str, ftp_white: str):
    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
        # await log_message(ctx,f'Pwd to {SAVE_FOLDER_ENCRYPTED}')
        await ftp.change_directory(SAVE_FOLDER_ENCRYPTED)
        # await log_message(ctx,f'Downloading {pretty_save_dir} from PS4')
        await ftp.download(ftp_bin,bin_file_out,write_into=True)
        await ftp.download(ftp_white,white_file_out,write_into=True)
async def download_encrypted_from_ps4(ctx: interactions.SlashContext, bin_file_out: Path, white_file_out: Path,parent_dir: Path, save_dir_ftp: str):
    ftp_bin = f'{save_dir_ftp}.bin'
    ftp_white = f'sdimg_{save_dir_ftp}'
    pretty_save_dir = white_file_out.relative_to(parent_dir)
    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,'*Please Wait*'))
    async with mounted_saves_at_once:
        tick_tock_task.cancel()
        await log_message(ctx,f'*Downloading* {pretty_save_dir} *from PS4(')
        custon_decss = lambda: asyncio.run(_download_encrypted_from_ps4(bin_file_out, white_file_out, ftp_bin, ftp_white))
        await asyncio.get_running_loop().run_in_executor(None,custon_decss)


async def resign_mounted_save(ctx: interactions.SlashContext | None, ftp: aioftp.Client,new_mount_dir:str, account_id: PS4AccountID) -> PS4AccountID:
    old_account_id = PS4AccountID('0000000000000000')
    try:
        await ftp.change_directory(Path(new_mount_dir,'sce_sys').as_posix())
        async with TemporaryDirectory() as tp:
            tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
            await ftp.download('param.sfo',tp_param_sfo,write_into=True)
            with open(tp_param_sfo,'rb+') as f:
                f.seek(0x15c)
                old_account_id = PS4AccountID.from_bytes(f.read(8))
                f.seek(0x15c)
                if account_id: # you're welcome @b.a.t.a.n.g (569531198490279957)
                    f.write(bytes(account_id))
            await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)
    except Exception as e:
        if ctx:
            await log_message(ctx,f'*Something went wrong when resigning the save,* {type(e).__name__}: {e}, ignoring!')
    finally:
        return old_account_id


async def clean_base_mc_save(title_id: str, dir_name: str, blocks: int):
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    async with MountSave(ps4,mem,int(CONFIG['user_id'],16),title_id,dir_name,blocks=blocks) as mp:
        if not mp:
            raise ValueError(f'bad {title_id}/{dir_name} reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")})')

async def delete_base_save_just_ftp(title_id: str, dir_name: str):
    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
        await ftp.change_directory(f'{BASE_SAVEDATA_FOLDER}/{title_id}')
        await ftp.remove(f'sdimg_{dir_name}')
        await ftp.remove(f'{dir_name}.bin')
        
async def _apply_cheats_on_ps4(account_id: PS4AccountID, bin_file: Path, white_file: Path, parent_dir: Path, cheats: Sequence[CheatFunc], save_dir_ftp: str | tuple[str,str], pretty_save_dir: Path, mount_save_title_id: str, ctx_author_id: str, special_thing: SpecialSaveFiles | None) -> str | tuple[list | PS4AccountID | str]:
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    try:
        async with MountSave(ps4,mem,int(CONFIG['user_id'],16),mount_save_title_id,save_dir_ftp) as mp:
            savedatax = mp.savedatax
            new_mount_dir = (MOUNTED_POINT / savedatax).as_posix()
            if not mp:
                return f'*Nope.. I couldn\'t mount your save*\n {pretty_save_dir} \n Because: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")}) (base save {mount_save_title_id}/{save_dir_ftp}),\n*I see* ``SCE_SAVE_DATA_ERROR_BROKEN`` *Maybe, retry the command, if I give this you issue again, the save is fucked, Please find a new save!*'
            # input(f'{mp}\n {new_mount_dir}')
            # We need to get real filename as the white_file.name can be differnt (such as a ` (1)` subfixed to it)
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                try:
                    await ftp.change_directory(Path(new_mount_dir,'sce_sys').as_posix())
                    async with TemporaryDirectory() as tp:
                        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
                        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
                        with open(tp_param_sfo,'rb') as f:
                            f.seek(0x9F8)
                            real_name = b''.join(iter(lambda: f.read(1),b'\x00')).decode('ascii')
                except Exception:
                    return f'Bad save {pretty_save_dir} missing param.sfo or broken param.sfo'
            
            results = []
            for index, chet in enumerate(cheats):
                try:
                    # await log_message(ctx,'Connecting to PS4 ftp to do some cheats')
                    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                        await ftp.change_directory(new_mount_dir)
                        
                        # await log_message(ctx,f'Applying cheat {chet.pretty()} {index + 1}/{len(cheats)} for {pretty_save_dir}')
                        result = await chet.func(ftp,new_mount_dir,real_name,**chet.kwargs)
                    results.append(result) if result else None
                except Exception:
                    return make_error_message_if_verbose_or_not(ctx_author_id,f'Could not apply cheat {chet.pretty()}to {pretty_save_dir}','')
            # await log_message(ctx,'Connecting to PS4 ftp to do resign')
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                await ftp.change_directory(new_mount_dir) 
                # await log_message(ctx,f'Resigning {pretty_save_dir} to {account_id.account_id}')
                account_id_old = await resign_mounted_save(None,ftp,new_mount_dir,account_id)
            
            return_payload = results,account_id_old,real_name
            
            async with setting_global_image_lock:
                try:
                    extra_opt = ChangeSaveIconOption(int((Path(__file__).parent / 'DO_NOT_DELETE_OR_EDIT_global_image_watermark_option.txt').read_text()))
                except FileNotFoundError:
                    return return_payload
                
                img_path = (Path(__file__).parent / 'DO_NOT_DELETE_global_image_watermark.png')
                
                if not img_path.is_file():
                    return return_payload
                
                async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                    await ftp.change_directory(new_mount_dir) 
                    try:
                        await change_save_icon(ftp,new_mount_dir,real_name,dl_link_image_overlay=img_path,option=extra_opt)
                    except Exception:
                        return make_error_message_if_verbose_or_not(ctx_author_id,f'Could not apply global watermark to {pretty_save_dir}','')
            return return_payload
    finally:
        if savedatax:
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                try:
                    await ftp.change_directory(new_mount_dir) # check if we are still mounted
                except Exception:
                    pass#print(f'{type(e).__name__}: {e}')
                else:
                    await ftp.change_directory('/')
                    await ftp.change_directory(MOUNTED_POINT.as_posix())
                    try:
                        await ftp.remove(savedatax)
                    except Exception:
                        pass
                    await ftp.change_directory(savedatax)
                    await ftp.upload(Path(__file__).parent / 'savemount_py/backup_dec_save/sce_sys')
                    umount_p = await unmount_save(ps4,mem,mp)
                    if umount_p:
                        try:
                            await ftp.change_directory('/')
                            await ftp.change_directory(new_mount_dir) # check if we are still mounted
                        except Exception: pass
                        else:
                            # await log_user_error(ctx,WARNING_COULD_NOT_UNMOUNT_MSG)
                            # breakpoint()
                            return WARNING_COULD_NOT_UNMOUNT_MSG
                    return f'Could not unmount {pretty_save_dir} likley corrupted param.sfo or something went wrong with the bot, best to report it with the save you provided. If you did mcworld2ps4 try setting mc_encrypted_save_size higher'
async def apply_cheats_on_ps4(ctx: interactions.SlashContext,account_id: PS4AccountID, bin_file: Path, white_file: Path, parent_dir: Path, cheats: Sequence[CheatFunc], save_dir_ftp: str | tuple[str,str], special_thing: SpecialSaveFiles | str | None) -> str | tuple[list | PS4AccountID]:
    if isinstance(special_thing,str):
        special_thing = None
    pretty_save_dir = white_file.relative_to(parent_dir)
    mount_save_title_id = BASE_TITLE_ID if isinstance(save_dir_ftp,str) else save_dir_ftp[1]
    
    if special_thing == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
        for chet in cheats:
            if chet.kwargs.get('decrypted_save_folder'):
                await log_message(ctx,f'*doing magic with file management on your mc world*')
                savedata0hehe = chet.kwargs.get('decrypted_save_folder') / 'savedata0'

                if not (savedata0hehe / 'level.dat').is_file():
                    return 'The mcworld file you sent, is not a valid mcworld file (missing level.dat file) perhaps you sent a folder or zip containg a mcworld, send the mcworld directly'
                
                if (savedata0hehe / 'sce_sys').is_dir():
                    await shutil.rmtree(savedata0hehe / 'sce_sys')
                (savedata0hehe / 'sce_sys').unlink(missing_ok=True)
                
                await shutil.copytree(Path(__file__).parent / 'savemount_py/backup_dec_save/sce_sys', savedata0hehe / 'sce_sys')
                
                da_blocks = chet.kwargs.pop('mc_encrypted_save_size')
                desc_before_find = b'BedrockWorldben@P5456\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                with open(savedata0hehe / 'sce_sys/param.sfo','rb+') as f:
                    data = f.read()
                    desc_before_find_index = data.index(desc_before_find)
                    f.seek(desc_before_find_index - 8)
                    f.write(struct.pack('<q',da_blocks))
                    
                world_icon_jpeg_file = None
                
                if (savedata0hehe / 'world_icon.jpeg').is_file():
                    world_icon_jpeg_file = savedata0hehe / 'world_icon.jpeg'
                if (savedata0hehe / 'world_icon.jpg').is_file():
                    world_icon_jpeg_file = savedata0hehe / 'world_icon.jpg'
                if (savedata0hehe / 'world_icon.png').is_file():
                    world_icon_jpeg_file = savedata0hehe / 'world_icon.png'
                
                if world_icon_jpeg_file:
                    try:
                        with Image.open(world_icon_jpeg_file) as img:
                            pass
                    except Exception:
                        pass
                    else:
                        with Image.open(world_icon_jpeg_file) as img:
                            width, height = img.size
                            new_img = img.resize((int((width / height) * PS4_ICON0_DIMENSIONS[1]),PS4_ICON0_DIMENSIONS[1]),Image.Resampling.NEAREST)
                            new_img.save(savedata0hehe/'sce_sys/icon0.png')
                        
                new_name = None
                try:
                    with open(savedata0hehe / 'levelname.txt','r') as f:
                        new_name = f.read(0x80-1)
                except Exception:
                    pass
                
                if new_name:
                    pretty_save_dir = new_name
                    # desc_before_find = white_file.name.encode('ascii').ljust(0x24, b'\x00')
                    desc_before_find = b'BedrockWorldben@P5456\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                    with open(savedata0hehe / 'sce_sys/param.sfo','rb+') as f:
                        data = f.read()
                        desc_before_find_index = data.index(desc_before_find)
                        f.seek(desc_before_find_index + len(desc_before_find))
                        f.write(new_name.encode('utf-8'))
                        
                        f.seek(desc_before_find_index)
                        f.write(white_file.name.encode('ascii').ljust(0x24, b'\x00'))
                
                await log_message(ctx,f'Checking for any resource/behaviour packs not added to json files')
                
                async def fix_packs(packs_json: str, packs_folder: str, pretty_thing: str):
                    try:
                        with open(savedata0hehe / packs_json,'r') as f:
                            resource_packs_json_list = json.loads(f.read())
                    except Exception:
                        await log_message(ctx,f'Could not load {packs_json} file, ignoring {pretty_thing} packs')
                    else:
                        if not (savedata0hehe / packs_folder).is_dir():
                            return await log_message(ctx,f'{packs_folder} doesnt exist')
                        for resource_folder in (savedata0hehe / packs_folder).iterdir():
                            try:
                                with open(resource_folder / 'manifest.json','r') as f:
                                    manifest = json.loads(f.read())
                            except Exception:
                                await log_message(ctx,f'Could not load manifest.json file for {resource_folder.name}, ignoring it')
                                continue
                            
                            try:
                                manifest_uuid = manifest['header']['uuid']
                            except Exception:
                                await log_message(ctx,f'Could not get uuid from manifest.json file for {resource_folder.name}, perhaps older or newer mcworld?')
                                continue
                            
                            try:
                                manifest_version = manifest['header']['version']
                            except Exception:
                                await log_message(ctx,f'Could not get version from manifest.json file for {resource_folder.name}, perhaps older or newer mcworld?')
                                continue
                            
                            for item in resource_packs_json_list:
                                if manifest_uuid == item['pack_id']:
                                    break
                            else: # no break
                                resource_packs_json_list.append({"pack_id":manifest_uuid,"version":manifest_version})
                                await log_message(ctx,f'Added {resource_folder.name} to {packs_json}')
                        try:
                            os.chmod(savedata0hehe / packs_json, S_IWRITE) # 7-Zip for some reason making extracted files read only, here we make it read and write for pack_json
                        except Exception:
                            pass
                        with open(savedata0hehe / packs_json,'w') as f:
                            f.write(json.dumps(resource_packs_json_list))
                
                await fix_packs('world_behavior_packs.json','behavior_packs','behaviour')
                await fix_packs('world_resource_packs.json','resource_packs','resource')
                cheats.append(CheatFunc(re_region,{'gameid':chet.kwargs.pop('gameid')}))

    await log_message(ctx,f'*Working Magic with your* {"".join(chet.pretty() for chet in cheats)} *to* {pretty_save_dir}')
    custon_decss = lambda: asyncio.run(_apply_cheats_on_ps4(account_id,bin_file,white_file,parent_dir,cheats,save_dir_ftp,pretty_save_dir,mount_save_title_id,ctx.author_id,special_thing))
    res = await asyncio.get_running_loop().run_in_executor(None,custon_decss)
    return res


async def _decrypt_saves_on_ps4(bin_file: Path, white_file: Path, parent_dir: Path,decrypted_save_ouput: Path, save_dir_ftp: str,decrypt_fun: DecFunc | None, pretty_save_dir: Path, ctx_author_id: str) -> str | None:
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    try:
        async with MountSave(ps4,mem,int(CONFIG['user_id'],16),BASE_TITLE_ID,save_dir_ftp) as mp:
            savedatax = mp.savedatax
            new_mount_dir = (MOUNTED_POINT / savedatax).as_posix()
            if not mp:
                return f'Could not mount {pretty_save_dir}, reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")}) (base save {BASE_TITLE_ID}/{save_dir_ftp}), if you get SCE_SAVE_DATA_ERROR_BROKEN please try the command again, this is a known issue to sometimes happen, if happens consistently, then the save may really is broken'
            if decrypt_fun:
                # await log_message(ctx,f'Doing custom decryption {decrypt_fun.pretty()} for {pretty_save_dir}')
                async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                    await ftp.change_directory(new_mount_dir)
                    try:
                        await decrypt_fun.func(ftp,new_mount_dir,white_file.name,decrypted_save_ouput,**decrypt_fun.kwargs)
                    except Exception:
                        return make_error_message_if_verbose_or_not(ctx_author_id,f'*I couldn\'t custom decrypt your save* {pretty_save_dir}.','')
            else:
                # await log_message(ctx,f'Downloading savedata0 folder from decrypted {pretty_save_dir}')
                async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                    await ftp.change_directory(MOUNTED_POINT.as_posix())
                    await ftp.download(savedatax,decrypted_save_ouput / 'savedata0',write_into=True)
    finally:
        if savedatax:
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                try:
                    await ftp.change_directory(new_mount_dir) # check if we are still mounted
                except Exception:
                    pass#print(f'{type(e).__name__}: {e}')
                else:
                    await ftp.change_directory('/')
                    await ftp.change_directory(MOUNTED_POINT.as_posix())
                    try:
                        await ftp.remove(savedatax)
                    except Exception:
                        pass
                    await ftp.change_directory(savedatax)
                    await ftp.upload(Path(__file__).parent / 'savemount_py/backup_dec_save/sce_sys')
                    umount_p = await unmount_save(ps4,mem,mp)
                    if umount_p:
                        try:
                            await ftp.change_directory('/')
                            await ftp.change_directory(new_mount_dir) # check if we are still mounted
                        except Exception: pass
                        else:
                            # await log_user_error(ctx,WARNING_COULD_NOT_UNMOUNT_MSG)
                            # breakpoint()
                            return WARNING_COULD_NOT_UNMOUNT_MSG
                    return f'Could not unmount {pretty_save_dir} likley corrupted param.sfo or something went wrong with the bot, best to report it with the save you provided. If you did mcworld2ps4 try setting mc_encrypted_save_size higher'
async def decrypt_saves_on_ps4(ctx: interactions.SlashContext, bin_file: Path, white_file: Path, parent_dir: Path,decrypted_save_ouput: Path, save_dir_ftp: str,decrypt_fun: DecFunc | None = None) -> str | None:
    pretty_save_dir = white_file.relative_to(parent_dir)

    # await log_message(ctx,f'Attempting to mount {pretty_save_dir}')
    if decrypt_fun:
        await log_message(ctx,f'*Adding custom decryption* {decrypt_fun.pretty()} *for* {pretty_save_dir}')
    else:
        await log_message(ctx,f'*Attemping to download savedata0 folder from decrypted* {pretty_save_dir}')
    custon_decss = lambda: asyncio.run(_decrypt_saves_on_ps4(bin_file, white_file, parent_dir, decrypted_save_ouput, save_dir_ftp, decrypt_fun, pretty_save_dir,ctx.author_id))
    res = await asyncio.get_running_loop().run_in_executor(None,custon_decss)
    return res

def _zipping_time(ctx: interactions.SlashContext,link_for_pretty: str,results: Path, parent_dir: Path, new_zip_name: Path, custom_msg):
    with zipfile.ZipFile(new_zip_name,'w') as zp:
        for file in results.rglob('*'):
            zp.write(file,file.relative_to(parent_dir))


async def send_result_as_zip(ctx: interactions.SlashContext,link_for_pretty: str,results: Path, parent_dir: Path, new_zip_name: Path, custom_msg: str):
    global amnt_used_this_session
    await log_message(ctx,f'*Big mf files that takes extra steps lol, Nearly done, Please wait* **(2 more steps left)**\n {link_for_pretty}')
    await asyncio.to_thread(_zipping_time,ctx,link_for_pretty,results,parent_dir,new_zip_name,custom_msg)
    
    real_file_size = new_zip_name.stat().st_size
    if real_file_size > ATTACHMENT_MAX_FILE_SIZE:
        await log_message(ctx,f'*Finally on the* **(last step!)**\n*This mf savefile is.. lol* ({pretty_bytes(real_file_size)} file)')
        try:
            google_drive_uploaded_user_zip_download_link = await google_drive_upload_file(new_zip_name,UPLOAD_SAVES_FOLDER_ID)
        except Exception as e:
            if 'storageQuotaExceeded' in str(e):
                pingers = ' '.join(f'<@{id}>' for id in CONFIG['bot_admins'])
                await log_message(ctx,f'oh no the bots owner gdrive is full, im giving you 2 minutes to ask {pingers} to clear some space')
                await asyncio.sleep(2*60)
                await log_message(ctx,f'*Finally on the* **(last step!)**\n*This mf savefile is.. lol* ({pretty_bytes(real_file_size)} file)')
                try:
                    google_drive_uploaded_user_zip_download_link = await google_drive_upload_file(new_zip_name,UPLOAD_SAVES_FOLDER_ID)
                except Exception as e2:
                    if 'storageQuotaExceeded' in str(e2):
                        await log_user_error(ctx,f'You were too late, owners gdrive is full! ask {pingers} to clear some space')
                        return
                    else:
                        raise
            else:
                raise
        await log_user_success(ctx,f'<:j_:1272151363530522655>*Hope you have Fun!!*<:Nice:1272144601033211924>\n<:labs_down:1272152021398454366>**Here is your resigned save!**<:labs_down:1272152021398454366>\n{google_drive_uploaded_user_zip_download_link}\n*Big ass savefile was* **({pretty_bytes(real_file_size)})**<:j_:1272151363530522655>')
    else:
        # await shutil.move(new_zip_name,new_zip_name.name)
        await log_message(ctx,f'*Finally uploading to Discord, Please wait!* **(last step!)**\n*This mf savefile is.. lol* ({pretty_bytes(real_file_size)} file)')
        await log_user_success(ctx,f'<:75271arrowcat3:1272162166203617353>*Hope you have Fun!!*<:Nice:1272144601033211924>\n<:labs_down:1272152021398454366>**Here is your resigned save!**<:labs_down:1272152021398454366>',file=str(new_zip_name))
        # os.remove(new_zip_name.name)
    amnt_used_this_session += 1
    if not is_in_test_mode():
        add_1_total_amnt_used()

############################00 Real commands stuff
def dec_enc_save_files(func):
    return interactions.slash_option(
    name="save_files",
    description="a google drive folder link containing your encrypted saves to be decrypted",
    required=True,
    opt_type=interactions.OptionType.STRING
    )(func)
def account_id_opt(func):
    return interactions.slash_option(
    name="account_id",
    description="The account id to resign the saves to, put in 0 for account id in database and 1 for no resign",
    required=True,
    max_length=16,
    min_length=1,
    opt_type=interactions.OptionType.STRING
    )(func)
def filename_p_opt(func):
    return interactions.slash_option(name='filename_p',description='If multiple files are found, it will look for a file with this name, put path if in folder',opt_type=interactions.OptionType.STRING,required=False)(func)# (like man4/mysave.sav)')
def verify_checksum_opt(func):
    return interactions.slash_option(name='verify_checksum',description='If set to true, then the command will fail if save has bad checksum (corrupted), default is True',required=False,opt_type=interactions.OptionType.BOOLEAN)(func)
def allow_mulit_enc_opt(func):
    return interactions.slash_option(
    name="allow_mulit_enc",
    description="Upload the same decrypted save to multiple encrypted saves? This is likely not what you want.",
    required=False,
    opt_type=interactions.OptionType.INTEGER,
    choices=[ 
        interactions.SlashCommandChoice(name="Yes i do, i know what im doing", value=True),
        interactions.SlashCommandChoice(name="No", value=False),
    ]
    )(func)

async def pre_process_cheat_args(ctx: interactions.SlashContext,cheat_chain: Sequence[CheatFunc | DecFunc],chet_files_custom: Path, savedata0_folder:Path) -> bool:
    await log_message(ctx,f'Looking for any `dl_link`s or `savedata0`s to download')
    for cheat in cheat_chain:
        for arg_name,link in cheat.kwargs.items():
            if arg_name.startswith('dl_link'):
                if is_str_int(link) and int(link) > 1:
                    try:
                        link = get_saved_url(ctx.author_id,int(link))
                    except KeyError:
                        await log_user_error(ctx,f'You dont have any url saved for {link}, try running the file2url command again!')
                        return False
                await log_message(ctx,f'*Downloading* {link} {arg_name}')
                result = await download_direct_link(ctx,link,chet_files_custom,max_size=DL_FILE_TOTAL_LIMIT,validation=filename_is_not_an_archive)
                if isinstance(result,str):
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = result
            if isinstance(link,interactions.Attachment):
                await log_message(ctx,f'*Downloading attachment* {arg_name}')
                result = await download_direct_link(ctx,link.url,chet_files_custom,max_size=DL_FILE_TOTAL_LIMIT)
                if isinstance(result,str):
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = result
            if arg_name in ('decrypted_save_file','decrypted_save_folder'):
                if isinstance(link,Path):
                    continue
                if is_str_int(link) and int(link) > 1:
                    try:
                        link = get_saved_url(ctx.author_id,int(link))
                    except KeyError:
                        await log_user_error(ctx,f'*You dont have any url saved for* {link}, *try running the file2url command again!*')
                        return False
                await log_message(ctx,f'*Downloading* {link} *savedata0 folder*')
                result = await download_decrypted_savedata0_folder(ctx,link,savedata0_folder,arg_name=='decrypted_save_folder',cheat.kwargs['unpack_first_root_folder'])
                if result:
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = savedata0_folder
            if arg_name == 'gameid' and (not is_ps4_title_id(link)):
                await log_user_error(ctx,f'*Invalid gameid* {link}')
                return False
            if arg_name.startswith('psstring'):
                link = link.encode('utf-8')
                for specparemcodelol in PARAM_SFO_SPECIAL_STRINGS:
                    link = link.replace(specparemcodelol.encode('ascii'),bytes.fromhex(specparemcodelol))
                    link = link.replace(specparemcodelol.encode('ascii').lower(),bytes.fromhex(specparemcodelol))
                if arg_name in ('psstring_new_name','psstring_new_desc') and len(link) >= 0x80:
                    await log_user_error(ctx,f'your string {link} is too long, max is 127 characters')
                    return False
                    
                cheat.kwargs[arg_name] = link
            if arg_name.endswith('_p'):
                cheat.kwargs[arg_name] = link.replace('\\','/')
    return True

async def base_do_dec(ctx: interactions.SlashContext,save_files: str, decrypt_fun: DecFunc | None = None):
    ctx = await set_up_ctx(ctx)
    await ps4_life_check(ctx)
    
    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return
    
    if is_str_int(save_files) and int(save_files) > 1:
        try:
            save_files = get_saved_url(ctx.author_id,int(save_files))
        except KeyError:
            await log_user_error(ctx,f'*You dont have any url saved for* {save_files}, *try running the file2url command again!*')
            return
    
    try:
        save_dir_ftp = await get_save_str()
    except SaveMountPointResourceError:
        await log_user_error(ctx,'*Ghosty\'s Bot is Coooooking!!!*, \n**please wait for a spot to free up**')
        return
    try:
        my_token = await get_time_as_string_token()
        async with TemporaryDirectory() as tp:
            enc_tp = Path(tp, 'enc_tp')
            enc_tp.mkdir()
            dec_tp = Path(tp, 'dec_tp')
            dec_tp.mkdir()

            if decrypt_fun:
                chet_files_custom = Path(tp, 'chet_files_custom')
                chet_files_custom.mkdir()
                savedata0_folder = Path(tp,'savedata0_folder')
                savedata0_folder.mkdir()
                if not await pre_process_cheat_args(ctx,(decrypt_fun,),chet_files_custom,savedata0_folder):
                    return

            download_ps4_saves_result = await download_ps4_saves(ctx,save_files,enc_tp,PS4AccountID('0000000000000000'))
            if download_ps4_saves_result:
                await log_user_error(ctx,download_ps4_saves_result)
                return
            for bin_file, white_file in list_ps4_saves(enc_tp):
                await upload_encrypted_to_ps4(ctx,bin_file,white_file,enc_tp,save_dir_ftp)
                pretty_folder_thing = white_file.relative_to(enc_tp).parts[0] + white_file.name
                new_dec = (dec_tp / pretty_folder_thing)
                new_dec.mkdir()
                tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'*Getting ready to mount* {pretty_folder_thing} /n'))
                async with mounted_saves_at_once:
                    tick_tock_task.cancel()
                    a = await decrypt_saves_on_ps4(ctx,bin_file,white_file,enc_tp,new_dec,save_dir_ftp,decrypt_fun)
                if a:
                    await log_user_error(ctx,a)
                    if a == WARNING_COULD_NOT_UNMOUNT_MSG:
                        breakpoint()
                    return
            your_saves_msg = '*savedata0 decrypted save*\n**(Please use /advanced_mode_export command instead)**'
            if decrypt_fun:
               your_saves_msg = (decrypt_fun.func.__doc__ or f'ItzGhosty420 ({decrypt_fun.func.__name__})').strip()
            await send_result_as_zip(ctx,save_files,dec_tp,dec_tp,Path(tp,my_token + '.zip'),your_saves_msg)
            return
    finally:
        await free_save_str(save_dir_ftp)


async def base_do_cheats(ctx: interactions.SlashContext, save_files: str,account_id: str, cheat: CheatFunc):
    ctx = await set_up_ctx(ctx)
    await ps4_life_check(ctx)

    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return

    if is_str_int(save_files) and int(save_files) > 1:
        try:
            save_files = get_saved_url(ctx.author_id,int(save_files))
        except KeyError:
            await log_user_error(ctx,f'*You dont have any url saved for* {save_files}, *try running the file2url command again!*')
            return

    account_id: str | PS4AccountID = account_id_from_str(account_id,ctx.author_id,ctx)
    if isinstance(account_id,str):
        await log_user_error(ctx,account_id)
        return

    if save_files == '0':
        add_cheat_chain(ctx.author_id,cheat)
        await log_user_success(ctx,f'*Added the cheat* {cheat.pretty()} *to your chain!*')
        return
        
    try:
        save_dir_ftp = await get_save_str()
    except SaveMountPointResourceError:
        await log_user_error(ctx,'*Ghosty\'s Bot is Cooooking*, **please wait for a spot to free up**')
        return
    try:
        my_token = await get_time_as_string_token()
        if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
            mc_filename = f'BedrockWorld{my_token.replace("_","")}@P547'
            mc_base_title_id = 'CUSA00265'
            real_save_dir_ftp = mc_filename
            tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'*Getting ready to make base mc world* {real_save_dir_ftp}'))
            async with mounted_saves_at_once:
                tick_tock_task.cancel()
                await log_message(ctx,f'**Making base mc world** {real_save_dir_ftp}')
                owner_of_blocks_blocks = cheat.kwargs.get('mc_encrypted_save_size',None)
                assert isinstance(owner_of_blocks_blocks,int)
                custon_decss1 = lambda: asyncio.run(clean_base_mc_save(BASE_TITLE_ID,real_save_dir_ftp,blocks=owner_of_blocks_blocks))
                await asyncio.get_running_loop().run_in_executor(None,custon_decss1)
        elif isinstance(save_files,Lbp3BackupThing):
            mc_filename = save_files.start_of_file_name + my_token.replace("_","")
            mc_base_title_id = save_files.title_id
            real_save_dir_ftp = mc_filename
            tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'*Getting ready to make base lbp3 level backup* {real_save_dir_ftp} '))
            async with mounted_saves_at_once:
                tick_tock_task.cancel()
                await log_message(ctx,f'*Making base lbp3 level backup* {real_save_dir_ftp}')
                custon_decss1 = lambda: asyncio.run(clean_base_mc_save(BASE_TITLE_ID,real_save_dir_ftp,blocks=save_files.new_blocks_size))
                await asyncio.get_running_loop().run_in_executor(None,custon_decss1)
            await log_message(ctx,f'*Setting level filename to* {mc_filename}')
            temp_savedata0 = cheat.kwargs['decrypted_save_file']
            with open(temp_savedata0 / 'savedata0/sce_sys/param.sfo','rb+') as f:
                desc_before_find = b'BedrockWorldben@P5456\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                data = f.read()
                desc_before_find_index = data.index(desc_before_find)
                f.seek(desc_before_find_index)
                f.write(mc_filename.encode('ascii'))
                
        else:
            real_save_dir_ftp = save_dir_ftp
        async with TemporaryDirectory() as tp:
            chet_files_custom = Path(tp, 'chet_files_custom')
            chet_files_custom.mkdir()
            enc_tp = Path(tp, 'enc_tp')
            enc_tp.mkdir()
            savedata0_folder = Path(tp,'savedata0_folder')
            savedata0_folder.mkdir()
            my_cheats_chain = get_cheat_chain(ctx.author_id) + [cheat]
            
            if not await pre_process_cheat_args(ctx,my_cheats_chain,chet_files_custom,savedata0_folder):
                return
            
            if False:
                await log_message(ctx,'doing special built in save thing')
                await log_user_error(ctx,'unimplemented')
                return
            else:
                if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD or isinstance(save_files,Lbp3BackupThing):
                    mc_new_white_path = Path(enc_tp, make_ps4_path(account_id,mc_base_title_id),mc_filename)
                    mc_new_bin_path = Path(enc_tp , make_ps4_path(account_id,mc_base_title_id),mc_filename+'.bin')
                    
                    mc_new_white_path.parent.mkdir(parents=True)

                    mc_new_white_path.write_bytes(b'\xFF')
                    mc_new_bin_path.write_bytes(b'\xFF')
                else:
                    download_ps4_saves_result = await download_ps4_saves(ctx,save_files,enc_tp,account_id)
                    if download_ps4_saves_result:
                        await log_user_error(ctx,download_ps4_saves_result)
                        return
                real_names = []
                results_big = []
                for bin_file, white_file in (done_ps4_saves := list(list_ps4_saves(enc_tp))):
                    if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
                        pass
                    elif isinstance(save_files,Lbp3BackupThing):
                        pass
                    else:
                        await upload_encrypted_to_ps4(ctx,bin_file,white_file,enc_tp,real_save_dir_ftp)
                    pretty_folder_thing = white_file.relative_to(enc_tp).parts[0] + white_file.name
                    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'*Getting ready to mount* {pretty_folder_thing}'))
                    async with mounted_saves_at_once:
                        tick_tock_task.cancel()
                        a: tuple[list[CheatFuncResult],PS4AccountID] = await apply_cheats_on_ps4(ctx,account_id,bin_file,white_file,enc_tp,my_cheats_chain,real_save_dir_ftp,save_files)
                    if isinstance(a,str):
                        await log_user_error(ctx,a)
                        if a == WARNING_COULD_NOT_UNMOUNT_MSG:
                            breakpoint()
                        return
                    results_small,old_account_id,real_name = a
                    await download_encrypted_from_ps4(ctx,bin_file,white_file,enc_tp,real_save_dir_ftp)
                    real_names.append(real_name)
                    results_big.append(results_small)
            
            await log_message(ctx,f'*Making sure file names in* {save_files} *are all correct*')
            found_fakes = False
            for real_name, (bin_file, white_file) in zip(real_names, done_ps4_saves, strict=True):
                if white_file.name != real_name:
                    await log_message(ctx,f'*Renaming* **{white_file.name}**\n *To* **{real_name}**')
                    try:
                        white_file.rename(white_file.parent / real_name)
                    except FileExistsError:
                        ben_white: Path = white_file.parent / real_name
                        ben_bin: Path = bin_file.parent / (real_name + '.bin')
                        
                        if not ben_white.is_file():
                            raise AssertionError(f'{white_file} -> {ben_white}')
                        if not ben_bin.is_file():
                            raise AssertionError(f'{bin_file} -> {ben_bin}')
                        
                        folder_above_ps4 = white_file.parent.parent.parent.parent.parent
                        for _ in range(20):
                            cooler_folder_above_ps4 = folder_above_ps4.parent / (f'RENAMED_SAVE_NUM{os.urandom(4).hex()}_{folder_above_ps4.name}')
                            if cooler_folder_above_ps4.is_file():
                                raise AssertionError(f'{cooler_folder_above_ps4 = } should not be a file at this moment')
                            if not cooler_folder_above_ps4.is_dir():
                                break
                        else: # no break
                            raise AssertionError('wtf extremely bad luck')


                        (cooler_folder_above_ps4 / white_file.parent.relative_to(folder_above_ps4)).mkdir(parents=True)

                        white_file = white_file.rename(cooler_folder_above_ps4 / white_file.relative_to(folder_above_ps4))
                        bin_file = bin_file.rename(cooler_folder_above_ps4 / bin_file.relative_to(folder_above_ps4))
                        
                        white_file.rename(white_file.parent / real_name)

                    bin_file.rename(bin_file.parent / (real_name + '.bin'))
                    found_fakes = True
            
            if found_fakes:
                await log_message(ctx,f'Refreshing {save_files} internal list 1/2')
                done_ps4_saves = list(list_ps4_saves(enc_tp))
                
            await log_message(ctx,f'*looking through results to do some renaming for* {save_files}')
            for results, (bin_file, white_file) in zip(results_big, done_ps4_saves, strict=True):
                for savename, gameid in results:
                    if savename:
                        try:
                            white_file = white_file.rename(white_file.parent / savename)
                        except FileExistsError:
                            ben_white: Path = white_file.parent / savename
                            ben_bin: Path = bin_file.parent / (savename + '.bin')
                            
                            if not ben_white.is_file():
                                raise AssertionError(f'{white_file} -> {ben_white}')
                            if not ben_bin.is_file():
                                raise AssertionError(f'{bin_file} -> {ben_bin}')
                            
                            folder_above_ps4 = white_file.parent.parent.parent.parent.parent
                            for _ in range(20):
                                cooler_folder_above_ps4 = folder_above_ps4.parent / (f'RE_REGIONED_SAVE_NUM{os.urandom(4).hex()}_{folder_above_ps4.name}')
                                if cooler_folder_above_ps4.is_file():
                                    raise AssertionError(f'{cooler_folder_above_ps4 = } should not be a file at this moment')
                                if not cooler_folder_above_ps4.is_dir():
                                    break
                            else: # no break
                                raise AssertionError('wtf extremely bad luck')


                            (cooler_folder_above_ps4 / white_file.parent.relative_to(folder_above_ps4)).mkdir(parents=True)

                            white_file = white_file.rename(cooler_folder_above_ps4 / white_file.relative_to(folder_above_ps4))
                            bin_file = bin_file.rename(cooler_folder_above_ps4 / bin_file.relative_to(folder_above_ps4))
                            
                            white_file = white_file.rename(white_file.parent / savename)

                        bin_file = bin_file.rename(bin_file.parent / (savename + '.bin'))
                        print(f'{white_file = }')
                    if gameid:
                        new_gameid_folder = white_file.parent.parent / gameid
                        new_gameid_folder.mkdir(exist_ok=True)
                        
                        white_file = white_file.rename(new_gameid_folder / white_file.name)
                        bin_file = bin_file.rename(new_gameid_folder / bin_file.name)
            
            if not account_id:
                have_not_done_at_least_1_account_id_change = False
                await log_message(ctx,f'*Refreshing* {save_files} internal list 2/2')
                done_ps4_saves = list(list_ps4_saves(enc_tp))
                for bin_file, white_file in done_ps4_saves:
                    try:
                        white_file.parent.parent.rename(white_file.parent.parent.parent / old_account_id.account_id)
                    except FileNotFoundError:
                        if not have_not_done_at_least_1_account_id_change:
                            raise
                    have_not_done_at_least_1_account_id_change = True
            if False:
                await log_message(ctx,'*cleaning up the things you did*')
                await log_user_error(ctx,'*unimplemented*')
                return
            
            await log_message(ctx,f'Deleting empty folders in {save_files}')
            async for x in AsyncPath(enc_tp).rglob('*'):
                try:
                    await x.rmdir()
                except Exception:
                    pass

            await send_result_as_zip(ctx,save_files,enc_tp,enc_tp,Path(tp,my_token + '.zip'),(cheat.func.__doc__ or f'ItzGhosty420 ({cheat.func.__name__})').strip())
            return
    finally:
        await free_save_str(save_dir_ftp)
        delete_chain(ctx.author_id)
        if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD or isinstance(save_files,Lbp3BackupThing):
            custon_decss1 = lambda: asyncio.run(delete_base_save_just_ftp(BASE_TITLE_ID,real_save_dir_ftp))
            await asyncio.get_running_loop().run_in_executor(None,custon_decss1)  # TODO could be dangerous we are not using the mounted_saves_at_once sempahore

############################01 Custom decryptions
@interactions.slash_command(name="raw_decrypt_folder",description=f"use /advanced_mode_export instead (max {MAX_RESIGNS_PER_ONCE} save per command)")
@dec_enc_save_files
async def do_raw_decrypt_folder(ctx: interactions.SlashContext,save_files: str):
    await base_do_dec(ctx,save_files)

# @interactions.slash_command(name="ps4saves_to_mcworlds",description=f"use /advanced_mode_export instead (max {MAX_RESIGNS_PER_ONCE} save per command)")
# @dec_enc_save_files
# async def do_raw_decrypt_folder(ctx: interactions.SlashContext,save_files: str):
    # await base_do_dec(ctx,save_files)
# ctx.special_save_files_thing

async def export_dl2_save(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None):
    """
    Exported dl2 file
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    await ftp.download(ftp_save[0],decrypted_save_ouput)
    
    downloaded_ftp_save: Path = decrypted_save_ouput / ftp_save[0]
    
    with gzip.open(downloaded_ftp_save, 'rb') as f_in:
        with open(downloaded_ftp_save.with_suffix('.gz'), 'wb') as f_out: # its not a gz file but i dont care i just want it to work
            await shutil.copyfileobj(f_in, f_out)
    os.replace(downloaded_ftp_save.with_suffix('.gz'),downloaded_ftp_save)


async def export_xenoverse_2_sdata000_dat_file(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None,verify_checksum: bool = True):
    """
    Exported xenoverse 2 SDATAXXX.DAT file
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    await ftp.download(ftp_save[0],decrypted_save_ouput)
    
    downloaded_ftp_save: Path = decrypted_save_ouput / ftp_save[0]

    with open(downloaded_ftp_save, 'rb') as f_in:
        with open(downloaded_ftp_save.with_suffix('.bin'), 'wb') as f_out: # its not a gz file but i dont care i just want it to work
            decrypt_xenoverse2_ps4(f_in,f_out,check_hash=verify_checksum)
    os.replace(downloaded_ftp_save.with_suffix('.bin'),downloaded_ftp_save)
# @interactions.slash_option(name='verify_checksum',description='If set to true, then the command will fail if save has bad checksum (corrupted), default is True',required=False,opt_type=interactions.OptionType.BOOLEAN)


async def export_red_dead_redemption_2_or_gta_v_file(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None):
    """
    Exported Red Dead Redemption 2 or Grand Theft Auto V savedata
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    await ftp.download(ftp_save[0],decrypted_save_ouput)
    
    downloaded_ftp_save: Path = decrypted_save_ouput / ftp_save[0]
    
    with open(downloaded_ftp_save,'rb') as f:
        decrypted_rdr2_data = auto_encrypt_decrypt(f)
    with open(downloaded_ftp_save,'wb') as f:
        f.write(decrypted_rdr2_data)


async def export_single_file_any_game(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None):
    """
    Exported file (if it dont work please report to Zhaxxy what game it is)
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    await ftp.download(ftp_save[0],decrypted_save_ouput)


game_dec_functions = { # Relying on the dict ordering here, "Game not here (might not work)" should be at bottom
    'Dying Light 2 Stay Human': export_dl2_save,
    'Grand Theft Auto V': export_red_dead_redemption_2_or_gta_v_file,
    'Red Dead Redemption 2': export_red_dead_redemption_2_or_gta_v_file,
    'DRAGON BALL XENOVERSE 2': export_xenoverse_2_sdata000_dat_file,
    'Game not here (might not work)': export_single_file_any_game,
}


@interactions.slash_command(name='advanced_mode_export',description="This is Save Wizard Advanced Mode! Easily Export/decrypt your save!")
@dec_enc_save_files
@interactions.slash_option(name='game',
    description='The game you want to export/decrypt saves of',
    opt_type=interactions.OptionType.STRING,
    required=True,
    choices=[
        interactions.SlashCommandChoice(name=gamenamey, value=gamenamey) for gamenamey in game_dec_functions.keys()
    ])
@filename_p_opt
async def do_multi_export(ctx: interactions.SlashContext,save_files: str,**kwargs): # TODO allow custom args for differnt dec functions, like verify_checksum
    export_func = game_dec_functions[kwargs.pop('game')]
    await base_do_dec(ctx,save_files,DecFunc(export_func,kwargs))
###########################0 Custom cheats
cheats_base_command = interactions.SlashCommand(name="cheats", description="Commands for custom cheats for some games")

async def do_nothing(ftp: aioftp.Client, mount_dir: str, save_name: str): """Resigned Saves"""
DUMMY_CHEAT_FUNC = CheatFunc(do_nothing,{})
@interactions.slash_command(name="resign", description=f"Resign any PS4 save to your account!")
@interactions.slash_option('save_files','The save files to resign too',interactions.OptionType.STRING,True)
@account_id_opt
async def do_resign(ctx: interactions.SlashContext,save_files: str,account_id: str):
    await base_do_cheats(ctx,save_files,account_id,DUMMY_CHEAT_FUNC)

async def install_mods_for_lbp3_ps4(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,ignore_plans = False, **mod_files: Path):
    """
    LittleBigPlanet .mod files encrypted
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        raise ValueError('Too many files in the save, likley not a lbp3 big save or level backup') from None
    
    if ftp_save[0].name.startswith('bigfart'):
        is_l0 = False
    elif ftp_save[0].name == ('L0'):
        is_l0 = True
    else:
        raise ValueError(f'Invalid bigfart or level backup file {ftp_save[0].name}')
        
    async with TemporaryDirectory() as tp:
        sa = Path(tp,'bigfart_or_l0_level_backup')
        await ftp.download(ftp_save[0],sa,write_into=True)
        
        def _do_the_install_lbp3_ps4_mods_lcoal(): install_mods_to_bigfart(sa,mod_files.values(),install_plans = not ignore_plans, is_ps4_level_backup = is_l0)
        await asyncio.get_running_loop().run_in_executor(None, _do_the_install_lbp3_ps4_mods_lcoal)
        await ftp.upload(sa,ftp_save[0],write_into=True)


littlebigplanet_3 = cheats_base_command.group(name="littlebigplanet_3", description="Cheats for LittleBigPlanet 3")
@littlebigplanet_3.subcommand(sub_cmd_name="install_mods", sub_cmd_description="Install .mod files to a level backup or LBPxSAVE (bigfart)")
@interactions.slash_option('save_files','The level backup or profile backup to install the mods too',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option(
    name = 'ignore_plans',
    description='Do you want to ignore .plan files in the mods? default is False',
    required=False,
    opt_type=interactions.OptionType.BOOLEAN
)
@interactions.slash_option(
    name = 'dl_link_mod_file1',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file2',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file3',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file4',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file5',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file6',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file7',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file8',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file9',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
    name = 'dl_link_mod_file10',
    description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
    required=False,
    opt_type=interactions.OptionType.STRING
)
async def do_lbp3_install_mods(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    if not any(key.startswith('dl_link_mod_file') for key in kwargs.keys()):
        ctx = await set_up_ctx(ctx)
        return await log_user_error(ctx,'Please give at least 1 dl_link_mod_file')
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(install_mods_for_lbp3_ps4,kwargs))

async def strider_change_difficulty(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,difficulty: str):
    """
    strider saves with difficulty changed
    """
    assert difficulty in ('0','1','2'), f'invalid difficulty {difficulty}, should be a choice in bot so idk wyd'
    await ftp.change_directory(mount_dir)
    async with TemporaryDirectory() as tp:
        sa = Path(tp,'SaveData')
        await ftp.download('SaveData',sa,write_into=True)
        with open(sa,'rb+') as f:
            where = f.read().index(b'GameDifficulty="')
            f.seek(where + len(b'GameDifficulty="'))
            f.write(difficulty.encode('ascii'))
            
            f.seek(4)
            new_hash1 = struct.pack('<I',crc32(f.read(0x7800 - 4))) # 4 away for the hash
            f.seek(0)
            f.write(new_hash1)
            
            f.seek(0x7800 + 4)
            new_hash2 = struct.pack('<I',crc32(f.read()))
            f.seek(0x7800)
            f.write(new_hash2)
            
        await ftp.upload(sa,'SaveData',write_into=True)


strider = cheats_base_command.group(name="strider", description="Cheats for Strider")
@strider.subcommand(sub_cmd_name="change_difficulty", sub_cmd_description="Change the games difficulty! (i never played this game in my life)")
@interactions.slash_option('save_files','The save files to change difficulty of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('difficulty','The difficulty ya want',interactions.OptionType.STRING,True,choices=[
        interactions.SlashCommandChoice(name="Easy mode", value='0'),
        interactions.SlashCommandChoice(name="Normal mode", value='1'),
        interactions.SlashCommandChoice(name="Hard mode", value='2')
    ])
async def do_strider_change_difficulty(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(strider_change_difficulty,kwargs))

def make_cheat_func(base_cheat_applier, the_real_cheat, /, kwargs) -> CheatFunc:
    async def some_cheaty(ftp: aioftp.Client, mount_dir: str, save_name: str, /, **kwargs):
        kwargs.setdefault('verify_checksum', True)
        kwargs.setdefault('filename_p', None)
        kwargs['the_real_cheat'] = the_real_cheat
        await base_cheat_applier(ftp, mount_dir, save_name, **kwargs)
    
    some_cheaty.__name__ = f'do_the_{the_real_cheat.__name__}'
    some_cheaty.__doc__ = the_real_cheat.__doc__
    return CheatFunc(some_cheaty, kwargs)

async def _base_xenoverse2_cheats(ftp: aioftp.Client, mount_dir: str, save_name: str,/,**kwargs):
    the_real_cheat = kwargs.pop('the_real_cheat')
    verify_checksum = kwargs.pop('verify_checksum')
    filename_p = kwargs.pop('filename_p')
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    async with TemporaryDirectory() as tp:
        xeno_save = Path(tp,ftp_save[0])
        await ftp.download(ftp_save[0],xeno_save,write_into=True)
        
        with open(xeno_save, 'rb') as f_in:
            with open(xeno_save.with_suffix('.dec'), 'wb') as f_out:
                decrypt_xenoverse2_ps4(f_in,f_out,check_hash=verify_checksum)
        
        await the_real_cheat(xeno_save.with_suffix('.dec'),**kwargs)
        
        with open(xeno_save.with_suffix('.dec'),'rb') as f, open(xeno_save,'wb') as f_out:
            encrypt_xenoverse2_ps4(f,f_out)
        
        await ftp.upload(xeno_save,ftp_save[0],write_into=True)


def make_xenoverse2_cheat_func(the_real_cheat, /, kwargs) -> CheatFunc:
    return make_cheat_func(_base_xenoverse2_cheats, the_real_cheat, kwargs)
    
    
async def xenoverse2_change_tp_medals(dec_save: Path,/,*,tp_medals: int):
    """
    DRAGON BALL XENOVERSE 2 save with changed TP medals
    """
    with open(dec_save,'rb+') as f:
        f.seek(0x158) # Lucky the offset is not a mutiple of 0x20
        f.write(struct.pack('<i',tp_medals))

dragonball_xenoverse_2 = cheats_base_command.group(name="dragonball_xenoverse_2", description="Cheats for DRAGON BALL XENOVERSE 2")
@dragonball_xenoverse_2.subcommand(sub_cmd_name="change_tp_medals", sub_cmd_description="Change the TP medals of your save")
@interactions.slash_option('save_files','The save files to change TP medals of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('tp_medals','The amount of TP medals you want',interactions.OptionType.INTEGER,True,**INT32_MAX_MIN_VALUES)
@filename_p_opt
@verify_checksum_opt
async def do_xenoverse2_change_tp_medals(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,make_xenoverse2_cheat_func(xenoverse2_change_tp_medals,kwargs))

async def _base_rayman_legend_cheats(ftp: aioftp.Client, mount_dir: str, save_name: str,/,**kwargs):
    the_real_cheat = kwargs.pop('the_real_cheat')
    verify_checksum = kwargs.pop('verify_checksum')
    filename_p = kwargs.pop('filename_p')
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    async with TemporaryDirectory() as tp:
        savefile_rayman_legends = Path(tp,ftp_save[0])
        await ftp.download(ftp_save[0],savefile_rayman_legends,write_into=True)

        if verify_checksum:
            with open(savefile_rayman_legends, 'rb+') as f:
                # Read from end up untill we reach as FF FF FF FF block
                f.seek(0,2)
                end_of_file_offset = f.tell()
                if end_of_file_offset > 10_000_000:
                    raise ValueError('save too big, is likley not a Rayman Legends save')
                f.seek(0)
                data = f.read()
                last_fffff_block_index = data.rfind(b'\xFF\xFF\xFF\xFF')
                if last_fffff_block_index == -1:
                    raise ValueError('can not find last ff block')
                last_fffff_block_index += 4
                checksum_offset = last_fffff_block_index + 0x10
                main_data_blob_size = last_fffff_block_index + (0x10 - 4) # 4 bytes before checksum
                f.seek(0)
                
                new_checksum = struct.pack('<I',custom_crc(f.read(main_data_blob_size)))
                f.seek(checksum_offset)
                old_cheksum = f.read(4)
                if not old_cheksum == new_checksum:
                    old_cheksum = old_cheksum.hex()
                    new_checksum = new_checksum.hex()
                    raise ValueError(f'Checksum missmatch {old_cheksum = } != {new_checksum = }')


        await the_real_cheat(savefile_rayman_legends,**kwargs)

        with open(savefile_rayman_legends, 'rb+') as f:
            # Read from end up untill we reach as FF FF FF FF block
            f.seek(0,2)
            end_of_file_offset = f.tell()
            if end_of_file_offset > 10_000_000:
                raise ValueError('save too big, is likley not a Rayman Legends save')
            f.seek(0)
            data = f.read()
            last_fffff_block_index = data.rfind(b'\xFF\xFF\xFF\xFF')
            if last_fffff_block_index == -1:
                raise ValueError('can not find last ff block')
            last_fffff_block_index += 4
            checksum_offset = last_fffff_block_index + 0x10
            main_data_blob_size = last_fffff_block_index + (0x10 - 4) # 4 bytes before checksum
            f.seek(0)
            
            new_checksum = struct.pack('<I',custom_crc(f.read(main_data_blob_size)))
            f.seek(checksum_offset)
            f.write(new_checksum)


        await ftp.upload(savefile_rayman_legends,ftp_save[0],write_into=True)


def make_rayman_legend_cheat_func(the_real_cheat, /, kwargs) -> CheatFunc:
    return make_cheat_func(_base_rayman_legend_cheats, the_real_cheat, kwargs)
    
    
async def rayman_legends_change_lums(dec_save: Path,/,*,lums: int):
    """
    Rayman Legends with changed Lums
    """
    with open(dec_save,'rb+') as f:
        start_struct = bytes.fromhex('FB 5A 99 A7')
        struct_i_think_offset = f.read().index(start_struct) + len(start_struct)
        f.seek(struct_i_think_offset + 0x54)
        
        prev_user_of_save = b''.join(iter(lambda: f.read(1),b'\x00')).decode('ascii')
        
        if not is_psn_name(prev_user_of_save):
            raise ValueError(f'Expected to find a psn username at {struct_i_think_offset + 0x54}')
        
        f.seek(struct_i_think_offset + 0x34)
        f.write(struct.pack('>I',lums))

rayman_legends = cheats_base_command.group(name="rayman_legends", description="Cheats for Rayman Legends")
@rayman_legends.subcommand(sub_cmd_name="change_lums", sub_cmd_description="Change the Lums of your save")
@interactions.slash_option('save_files','The save files to change Lums of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('lums','The amount of Lums you want',interactions.OptionType.INTEGER,True,**UINT32_MAX_MIN_VALUES)
@filename_p_opt
@verify_checksum_opt
async def do_rayman_legends_change_lums(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,make_rayman_legend_cheat_func(rayman_legends_change_lums,kwargs))

async def rayman_legends_change_jump_count(dec_save: Path,/,*,jump_count: int):
    """
    Rayman Legends with changed jump count
    """
    with open(dec_save,'rb+') as f:
        start_struct = bytes.fromhex('00 00 00 2A 00 00 00 00 00 00 00 00 00 00 00 00')
        struct_i_think_offset = f.read().index(start_struct) + len(start_struct)

        f.seek(struct_i_think_offset + 0x64)
        f.write(struct.pack('>f',jump_count))


@rayman_legends.subcommand(sub_cmd_name="change_jump_count", sub_cmd_description="Change the jump count of your save")
@interactions.slash_option('save_files','The save files to change jump count of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('jump_count','The jump count you want',interactions.OptionType.INTEGER,True)
@filename_p_opt
@verify_checksum_opt
async def do_rayman_legends_change_jump_count(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,make_rayman_legend_cheat_func(rayman_legends_change_jump_count,kwargs))
###########################0 some base folder things idk
async def upload_savedata0_folder(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,clean_encrypted_file: CleanEncryptedSaveOption, decrypted_save_file: Path = None, decrypted_save_folder: Path = None, unpack_first_root_folder: bool = False):
    """
    Encrypted save (use /advanced_mode_import instead)
    """
    if decrypted_save_file and decrypted_save_folder:
        raise TypeError('cannot have both decrypted_save_file and decrypted_save_folder')
    if decrypted_save_folder:
        decrypted_save_file = decrypted_save_folder
    parent_mount, mount_last_name = Path(mount_dir).parent.as_posix(), Path(mount_dir).name
    
    if clean_encrypted_file.value:
        await ftp.change_directory(mount_dir)
        for path,info in (await ftp.list(recursive=True)):
            if path.parts[0] == 'sce_sys' and clean_encrypted_file == CleanEncryptedSaveOption.DELETE_ALL_BUT_KEEP_SCE_SYS:
                continue
            await ftp.remove(path)
    

    await ftp.change_directory(parent_mount)
    print('cato!')
    await ftp.upload(decrypted_save_file / 'savedata0',mount_last_name,write_into=True)
@interactions.slash_command(name="raw_encrypt_folder", description=f"use /advanced_mode_import instead (max 1 save per command) only jb PS4 decrypted save")
@interactions.slash_option('save_files','The save file orginally decrypted',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('decrypted_save_file','A link to a folder or zip of your decrypted savedata0 folder',interactions.OptionType.STRING,True)
@interactions.slash_option(
    name="clean_encrypted_file",
    description="Delete all in encrypted file; only use when decrypted folder has all files",
    required=False,
    opt_type=interactions.OptionType.INTEGER,
    choices=[ # TODO make theese choices stick out from each other more
        interactions.SlashCommandChoice(name="Delete all in encrypted file but *keep sce_sys folder*; only use when decrypted folder has all files", value=1),
        interactions.SlashCommandChoice(name="Delete all in encrypted file **INCLUDING sce_sys folder**; only use if decrypted folder has al files", value=2),
    ]
    )
@allow_mulit_enc_opt
async def do_encrypt(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    if not kwargs.pop('allow_mulit_enc',None):
        ctx.special_save_files_thing = SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT

    kwargs['clean_encrypted_file'] = CleanEncryptedSaveOption(kwargs.get('clean_encrypted_file',0))
    kwargs['unpack_first_root_folder'] = False
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_savedata0_folder,kwargs))

@interactions.slash_command(name="raw_encrypt_folder_type_2", description=f"use /advanced_mode_import instead (max 1 save per command) only jb PS4 decrypted save")
@interactions.slash_option('save_files','The save file orginally decrypted',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('decrypted_save_folder','A link to a folder or zip containing your decrypted',interactions.OptionType.STRING,True)
@interactions.slash_option(
    name="unpack_first_root_folder",
    description="If Yes, then it move contents of top most folder to root, otherwise it wont, default is Yes",
    required=False,
    opt_type=interactions.OptionType.INTEGER,
    choices=[
        interactions.SlashCommandChoice(name="Yes", value=True),
        interactions.SlashCommandChoice(name="No", value=False),
    ]
    )
@interactions.slash_option(
    name="clean_encrypted_file",
    description="Delete all in encrypted file; only use when decrypted folder has all files",
    required=False,
    opt_type=interactions.OptionType.INTEGER,
    choices=[ # TODO make theese choices stick out from each other more
        interactions.SlashCommandChoice(name="Delete all in encrypted file but *keep sce_sys folder*; only use when decrypted folder has all files", value=1),
        interactions.SlashCommandChoice(name="Delete all in encrypted file **INCLUDING sce_sys folder**; only use if decrypted folder has al files", value=2),
    ]
    )
@allow_mulit_enc_opt
async def do_raw_encrypt_folder_type_2(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    if not kwargs.pop('allow_mulit_enc',None):
        ctx.special_save_files_thing = SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT

    kwargs['clean_encrypted_file'] = CleanEncryptedSaveOption(kwargs.get('clean_encrypted_file',0))
    kwargs['unpack_first_root_folder'] = kwargs.get('unpack_first_root_folder',True)
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_savedata0_folder,kwargs))

@interactions.slash_command(name="mcworld2ps4", description=f".mcworld file to a PS4 encrypted minecraft save")
@account_id_opt
@interactions.slash_option('mcworld_file','A link to your mcworld file, NOT a folder!',interactions.OptionType.STRING,True)
@interactions.slash_option(
    name="mc_encrypted_save_size",
    description="The size of the result encrypted save, if issue happens use a larger mc_encrypted_save_size",
    required=True,
    opt_type=interactions.OptionType.INTEGER,
    choices=[
        interactions.SlashCommandChoice(name="1GB (Safest)", value=32768),
        interactions.SlashCommandChoice(name="512mb (can fail at apply cheats step)", value=32768//2),
        interactions.SlashCommandChoice(name="256mb (can fail at apply cheats step)", value=(32768//2)//2),
        interactions.SlashCommandChoice(name="128mb (can fail at apply cheats step)", value=((32768//2)//2)//2),
        interactions.SlashCommandChoice(name="64mb (can fail at apply cheats step)", value=(((32768//2)//2)//2)//2),
        interactions.SlashCommandChoice(name="32mb (can fail at apply cheats step)", value=((((32768//2)//2)//2)//2)//2),
        interactions.SlashCommandChoice(name="25mb (can fail at apply cheats step)", value=26_214_400//32768),
    ]
    )
@interactions.slash_option(
    name="gameid",
    description="The region you want of the save",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=[
        interactions.SlashCommandChoice(name="CUSA00265 (EU)", value='CUSA00265'),
        interactions.SlashCommandChoice(name="CUSA00744 (US)", value='CUSA00744'),
        interactions.SlashCommandChoice(name="CUSA00283 (JP)", value='CUSA00283'),
        interactions.SlashCommandChoice(name="CUSA44267 (US Preview)", value='CUSA44267'),
    ]
    )
async def do_mcworld2ps4(ctx: interactions.SlashContext, account_id: str, **kwargs):
    if account_id == '1':
        return await log_user_error(ctx,'Cannot get original account id of save, perhaps you didnt mean to put 1 in account_id')
    kwargs['clean_encrypted_file'] = CleanEncryptedSaveOption.DELETE_ALL_INCLUDING_SCE_SYS
    kwargs['unpack_first_root_folder'] = True
    kwargs['decrypted_save_folder'] = kwargs.pop('mcworld_file')
    await base_do_cheats(ctx,SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD,account_id,CheatFunc(upload_savedata0_folder,kwargs))


@interactions.slash_command(name="lbp_level_archive2ps4", description=f"Gets the level from the lbp archive backup (dry.db) and turns it into a ps4 levelbackup")
@account_id_opt
@interactions.slash_option('slotid_from_drydb','The slot id from dry.db of the level you want, you can search for it on https://maticzpl.xyz/lbpfind',interactions.OptionType.INTEGER,True,min_value=56,max_value=100515565)
@interactions.slash_option(
    name="gameid",
    description="The region you want of the save",
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=[
        interactions.SlashCommandChoice(name="CUSA00063 (EU)", value='CUSA00063'),
        interactions.SlashCommandChoice(name="CUSA00473 (US)", value='CUSA00473'),
        interactions.SlashCommandChoice(name="CUSA00693 (AS asia)", value='CUSA00693'),
        interactions.SlashCommandChoice(name="CUSA00762 (GB UK)", value='CUSA00762'),
        interactions.SlashCommandChoice(name="CUSA00810 (US LATAM)", value='CUSA00810'),
    ]
    )
async def do_lbp_level_archive2ps4(ctx: interactions.SlashContext, account_id: str, **kwargs):
    ctx = await set_up_ctx(ctx)
    if account_id == '1':
        return await log_user_error(ctx,'Cannot get original account id of save, perhaps you didnt mean to put 1 in account_id')
    if not ZAPRIT_FISH_IS_UP:
        return await log_user_error(ctx,'Sorry, but zaprit.fish is down')
    slotid_from_drydb = kwargs.pop('slotid_from_drydb')
    gameid = kwargs.pop('gameid')
    async with TemporaryDirectory() as tp:
        tp = Path(tp)
        await log_message(ctx,f'*Downloading slot* `{slotid_from_drydb}`')
        result = await download_direct_link(ctx,f'https://zaprit.fish/dl_archive/{slotid_from_drydb}',tp)
        if isinstance(result,str):
            if not isinstance(result,ZapritFishKnownLinkError):
                await log_user_error(ctx,result + ' This could be because the level failed to load on official servers or a dynamic thermometer level (this is an issue with https://zaprit.fish itself)')
                return 
            await log_user_error(ctx,result)
            return 
        await extract_full_archive(result,tp,'x')
        for level_backup_folder in tp.iterdir():
            if level_backup_folder.is_dir():
                break
        else: # no break
            return await log_user_error(ctx,'the zip the zaprit fish gave had no level backup (this should never happen, defo report this)')
        
        savedata0_folder = tp / 'savedata0_folder' / 'savedata0'
        savedata0_folder.mkdir(parents=True)
        
        await log_message(ctx,f'Converting slot `{slotid_from_drydb}` to L0 file')
        with open(savedata0_folder / 'L0','wb') as f:
            level_name, level_desc,is_adventure,icon0_path = await asyncio.get_event_loop().run_in_executor(None, ps3_level_backup_to_l0_ps4,level_backup_folder,f)
            l0_size = f.tell()
        
        if l0_size > LBP3_PS4_L0_FILE_MAX_SIZE:
            await log_user_error(ctx,f'The slot `{slotid_from_drydb}` is too big ({pretty_bytes(l0_size)}), the max lbp3 ps4 level backup can only be {pretty_bytes(LBP3_PS4_L0_FILE_MAX_SIZE)}')
            return 
        
        await log_message(ctx,f'Doing some file management for slot `{slotid_from_drydb}` ')
        await shutil.copytree(Path(__file__).parent / 'savemount_py/backup_dec_save/sce_sys', savedata0_folder / 'sce_sys')
        
        lbp3_keystone = b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb7/\xad\xc3\xf9\xc7\xfc\xfaAR\xca\x82{\xcfo\xac\xcf\xd2m\x1f\x8f\x80!%[MK\xbc\x02\xb7\x04_\x91L\x99\xfc\xb3\xde^\x87\xc0\x9c\xdb\x90\xaf\xdb\xba\xde\xf3\x80L\xee\xa9\x11w9E\x9a\xa7y[O\xc9\xaa'
        
        await AsyncPath(savedata0_folder / 'sce_sys/keystone').write_bytes(lbp3_keystone)
        if isinstance(icon0_path,Path):
            await shutil.move(icon0_path,savedata0_folder / 'sce_sys/icon0.png')
        elif isinstance(icon0_path,str):
            result = await download_direct_link(ctx,f'https://zaprit.fish/icon/{icon0_path}',tp)
            if isinstance(result,str):
                await log_user_error(ctx,result)
                return 
            await shutil.move(result,savedata0_folder / 'sce_sys/icon0.png')
            
        base_name = f'{gameid}x00ADV' if is_adventure else f'{gameid}x00LEVEL'
        seeks = (0x61C,0x62C,0xA9C)
        tp_param_sfo = savedata0_folder / 'sce_sys/param.sfo'
        with open(tp_param_sfo,'rb+') as f:
            for seek in seeks:
                f.seek(seek)
                f.write(gameid.encode('ascii'))
        psstring_new_name = f'lbp3PS4: {level_name}'.encode('utf-8')[:0x79]
        with open(tp_param_sfo,'rb+') as f:
            data = f.read()
            obs_index = data.index(b'obs\x00')
            f.seek(obs_index + len(b'obs\x00'))
            assert f.read(1) != b'\x00', 'found a null byte, no existing save name?'
            f.seek(-1, 1)
            assert len(psstring_new_name) < 0x80, f'{psstring_new_name} is too long!'
            f.write(psstring_new_name)
        psstring_new_desc = f'{level_desc}'.encode('utf-8')[:0x79]
        desc_before_find = b'BedrockWorldben@P5456\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        with open(tp_param_sfo,'rb+') as f:
            data = f.read()
            desc_before_find_index = data.index(desc_before_find)
            f.seek(desc_before_find_index + len(desc_before_find))
            # assert f.read(1) != b'\x00', 'found a null byte, no existing save name?'
            # f.seek(-1, 1)
            assert len(psstring_new_desc) < 0x80, f'{psstring_new_desc} is too long!'
            f.write(psstring_new_desc)
        
        
        await log_message(ctx,f'Getting decrypted save size for slot `{slotid_from_drydb}`')
        
        # new_blocks_size = sum((x.stat()).st_size for x in savedata0_folder.rglob('*'))
        async_savedata0_folder = AsyncPath(savedata0_folder)
        new_blocks_size = 0
        async for x in async_savedata0_folder.rglob('*'):
            new_blocks_size += (await x.stat()).st_size


        new_blocks_size = (new_blocks_size//32768) + (3_145_728//32768) # min save is 3mb
        with open(tp_param_sfo,'rb+') as f:
            f.seek(0x9F8-8)
            f.write(struct.pack('<q',new_blocks_size))
        await base_do_cheats(ctx,Lbp3BackupThing(gameid,base_name,level_name,level_desc,is_adventure,new_blocks_size),account_id,CheatFunc(upload_savedata0_folder,{'decrypted_save_file':savedata0_folder.parent,'clean_encrypted_file':CleanEncryptedSaveOption.DELETE_ALL_INCLUDING_SCE_SYS}))


async def re_region(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,gameid: str) -> CheatFuncResult:
    """
    re regioned save
    """
    # is_xenoverse = gameid in XENOVERSE_TITLE_IDS
   
    # if is_xenoverse:
        # seeks = (0x61C,0xA9C,0x9F8)
    # else:
    found_titleids = tuple(m.start() + 0x9F8 for m in CUSA_TITLE_ID.finditer(save_name))
    seeks = (0x61C,0x62C,0xA9C) + found_titleids
    
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            for seek in seeks:
                f.seek(seek)
                f.write(gameid.encode('ascii'))
        await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)

        if new_param := PS4_SAVE_KEYSTONES.get(gameid):
            tp_keystone = Path(tp,'keystone')
            tp_keystone.write_bytes(new_param)
            await ftp.upload(tp_keystone,'keystone',write_into=True)
    # if is_xenoverse:
        # savename = gameid + save_name[9:]
    # else:
    savename = None
    for x in found_titleids:
        x -= 0x9F8
        savename = save_name.replace(save_name[x:x+9],gameid)
        save_name = savename
    return CheatFuncResult(savename,gameid)
@interactions.slash_command(name="re_region", description=f"Re region your save files!")
@interactions.slash_option('save_files','The save files to be re regioned',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('gameid','The gameid of the region you want, in format CUSAXXXXX',interactions.OptionType.STRING,True,max_length=9,min_length=9)
async def do_re_region(ctx: interactions.SlashContext,save_files: str,account_id: str, gameid: str):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(re_region,{'gameid':gameid.upper()}))

async def change_save_icon(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_image_overlay: Path, option: ChangeSaveIconOption):
    """
    Changed save icon
    """
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        og_icon0_path = Path(tp,'icon0.png')
        await ftp.download('icon0.png',og_icon0_path,write_into=True)
        with Image.open(dl_link_image_overlay).convert("RGBA") as icon_overlay:
            width, height = icon_overlay.size
            if option == ChangeSaveIconOption.KEEP_ASPECT_NEAREST_NEIGHBOUR:
                icon_overlay = icon_overlay.resize((int((width / height) * PS4_ICON0_DIMENSIONS[1]),PS4_ICON0_DIMENSIONS[1]),Image.Resampling.NEAREST)
            elif option == ChangeSaveIconOption.IGNORE_ASPECT_NEAREST_NEIGHBOUR:
                icon_overlay = icon_overlay.resize(PS4_ICON0_DIMENSIONS,Image.Resampling.NEAREST)
            elif option == ChangeSaveIconOption.KEEP_ASPECT_BILINEAR:
                icon_overlay = icon_overlay.resize((int((width / height) * PS4_ICON0_DIMENSIONS[1]),PS4_ICON0_DIMENSIONS[1]))
            elif option == ChangeSaveIconOption.IGNORE_ASPECT_BILINEAR:
                icon_overlay = icon_overlay.resize(PS4_ICON0_DIMENSIONS)
            else:
                raise TypeError(f'Unrecongised option {option}')
            with Image.open(og_icon0_path) as im:
                im.paste(icon_overlay,(0,0),icon_overlay)
                im.save(og_icon0_path)
        await ftp.upload(og_icon0_path,'icon0.png',write_into=True)
@interactions.slash_command(name="change_icon",description=f"Add a picture to customise your modded save!")
@interactions.slash_option('save_files','The save files to change the icon of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_image_overlay','The link to an image overlay you want, check out file2url!',interactions.OptionType.STRING,True)
@interactions.slash_option(
    name="option",
    description="Some options you might want",
    required=True,
    opt_type=interactions.OptionType.INTEGER,
    choices=[
        interactions.SlashCommandChoice(name="Keep aspect ratio and use nearest neighbour for resizing", value=1),
        interactions.SlashCommandChoice(name="Ignore aspect ratio and use nearest neighbour for resizing", value=2),
        interactions.SlashCommandChoice(name="Keep aspect ratio and use bilnear for resizing", value=3),
        interactions.SlashCommandChoice(name="Ignore aspect ratio and use bilnear for resizing", value=4),
    ]
    )
async def do_change_save_icon(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    kwargs['option'] = ChangeSaveIconOption(kwargs['option'])
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(change_save_icon,kwargs))

async def change_save_name(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,psstring_new_name: bytes) -> None:
    """
    save with new name in menu
    """
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            data = f.read()
            obs_index = data.index(b'obs\x00')
            f.seek(obs_index + len(b'obs\x00'))
            assert f.read(1) != b'\x00', 'found a null byte, no existing save name?'
            f.seek(-1, 1)
            assert len(psstring_new_name) < 0x80, f'{psstring_new_name} is too long!'
            f.write(psstring_new_name)
        await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)


@interactions.slash_command(name="change_save_name", description=f"Customise the title of your modded save")
@interactions.slash_option('save_files','The save files to change the name of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('psstring_new_name','the name you want, put hex code for symbols (eg this is a checkmark -> EFA1BE)',interactions.OptionType.STRING,True,min_length=1,max_length=0x80*3)
async def do_change_save_name(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(change_save_name,kwargs))


async def change_save_desc(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,psstring_new_desc: bytes) -> None:
    """
    save with new name in menu
    """
    desc_before_find = save_name.encode('ascii').ljust(0x24, b'\x00')
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            data = f.read()
            desc_before_find_index = data.index(desc_before_find)
            f.seek(desc_before_find_index + len(desc_before_find))
            # assert f.read(1) != b'\x00', 'found a null byte, no existing save name?'
            # f.seek(-1, 1)
            assert len(psstring_new_desc) < 0x80, f'{psstring_new_desc} is too long!'
            f.write(psstring_new_desc)
        await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)


@interactions.slash_command(name="change_save_desc", description=f"Customise the description of your modded save")
@interactions.slash_option('save_files','The save files to change the description of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('psstring_new_desc','the description you want, put hex code for symbols (eg this is a TV -> EFA1B1)',interactions.OptionType.STRING,True,min_length=1,max_length=0x79*6)
async def do_change_save_desc(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(change_save_desc,kwargs))
############################03 Custom imports

async def rayman_legends_upload_fix_checksum(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path, filename_p: str | None = None):
    """
    Rayman Legends with fixed checksum
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    with open(dl_link_single, 'rb+') as f:
        # Read from end up untill we reach as FF FF FF FF block
        f.seek(0,2)
        end_of_file_offset = f.tell()
        if end_of_file_offset > 10_000_000:
            raise ValueError('save too big, is likley not a Rayman Legends save')
        f.seek(0)
        data = f.read()
        last_fffff_block_index = data.rfind(b'\xFF\xFF\xFF\xFF')
        if last_fffff_block_index == -1:
            raise ValueError('can not find last ff block')
        last_fffff_block_index += 4
        checksum_offset = last_fffff_block_index + 0x10
        main_data_blob_size = last_fffff_block_index + (0x10 - 4) # 4 bytes before checksum
        f.seek(0)
        
        new_checksum = struct.pack('<I',custom_crc(f.read(main_data_blob_size)))
        f.seek(checksum_offset)
        f.write(new_checksum)
        
    await ftp.upload(dl_link_single,ftp_save[0],write_into=True)


async def upload_dl2_sav_gz_decompressed(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path, filename_p: str | None = None):
    """
    Encrypted dying light 2 save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    with open(dl_link_single, 'rb') as f_in:
        with gzip.open(dl_link_single.with_suffix('.gz'), 'wb') as f_out: # its not a gz file but i dont care i just want it to work
            await shutil.copyfileobj(f_in, f_out)
    os.replace(dl_link_single.with_suffix('.gz'),dl_link_single)
    
    await ftp.upload(dl_link_single,ftp_save[0],write_into=True)


async def upload_xenoverse_2_save(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path, filename_p: str | None = None):
    """
    Xenoverse 2 encrypted save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None

    with open(dl_link_single,'rb') as f, open(dl_link_single.with_suffix('.enc'),'wb') as f_out:
        encrypt_xenoverse2_ps4(f,f_out)
    await ftp.upload(dl_link_single.with_suffix('.enc'),ftp_save[0],write_into=True)


async def upload_red_dead_redemption_2_or_gta_v_save(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path, filename_p: str | None = None):
    """
    Red Dead Redemption 2 or Grand Theft Auto V encrypted save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None

    with open(dl_link_single,'rb+') as f:
        encrypted_rdr2_data = auto_encrypt_decrypt(f)
    
    with open(dl_link_single,'wb') as f:
        f.write(encrypted_rdr2_data)
    
    await ftp.upload(dl_link_single,ftp_save[0],write_into=True)


async def import_bigfart(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path):
    """
    Encrypted bigfart
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        raise ValueError('Too many files in the save, likley not a lbp3 big save, did you upload the 500mb+ one?') from None

    if not ftp_save[0].name.startswith('bigfart'):
        raise ValueError(f'Invalid bigfart {ftp_save[0].name}, not a lbp3 big save, did you upload the 500mb+ one?')

    with open(dl_link_single,'rb+') as f:
        savkey = far4_tools.SaveKey(f)
        savkey.is_ps4_endian = True
        savkey.write_to_far4(f)
    
    await ftp.upload(dl_link_single,ftp_save[0],write_into=True)


async def upload_single_file_any_game(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path, filename_p: str | None = None):
    """
    Imported save (if it dont work please report to Zhaxxy what game it is)
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        if filename_p is None:
            raise ValueError(f'we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
        
        for path,info in files:
            if str(path).replace('\\','/').casefold() == filename_p.casefold():
                ftp_save = (path,info)
                break
        else: # nobreak
            raise ValueError(f'we could not find the {filename_p} file, we found \n{chr(10).join(str(e[0]) for e in files)}\n\ntry putting one of these in the filename_p option') from None
    
    await ftp.upload(dl_link_single,ftp_save[0],write_into=True)

game_enc_functions = { # Relying on the dict ordering here, "Game not here (might not work)" should be at bottom
    'Dying Light 2 Stay Human': upload_dl2_sav_gz_decompressed,
    'Grand Theft Auto V': upload_red_dead_redemption_2_or_gta_v_save,
    'Red Dead Redemption 2': upload_red_dead_redemption_2_or_gta_v_save,
    'DRAGON BALL XENOVERSE 2': upload_xenoverse_2_save,
    'Rayman Legends': rayman_legends_upload_fix_checksum,
    'LittleBigPlanet bigfart (just not from Vita)': import_bigfart,
    'Game not here (might not work)': upload_single_file_any_game,
}


@interactions.slash_command(name="advanced_mode_import",description=f"This is Save Wizard Advanced Mode! Easily Import/encrypt your exported/decrypted save!")
@interactions.slash_option('save_files','The save file to import the decrypted save to',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_single','The file link you wanna import YOU SHOULD GET THIS FROM SAVEWIZARD OR advanced_mode_export',interactions.OptionType.STRING,True)
@interactions.slash_option(name='game',
    description='The game you want to import/encrypt saves of',
    opt_type=interactions.OptionType.STRING,
    required=True,
    choices=[
        interactions.SlashCommandChoice(name=gamenamey, value=gamenamey) for gamenamey in game_enc_functions.keys()
    ])
@filename_p_opt
@allow_mulit_enc_opt
async def do_upload_single_file_any_game(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs): # TODO allow custom args for differnt enc functions
    if not kwargs.pop('allow_mulit_enc',None):
        ctx.special_save_files_thing = SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT

    import_func = game_enc_functions[kwargs.pop('game')]
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(import_func,kwargs))
############################04 Cool bot features
_did_first_boot = True
@interactions.listen()
async def ready():
    global _did_first_boot
    global total_runtime
    total_runtime = get_total_runtime()
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    await update_status()
    _update_status.start()
    await ps4.notify('eZwizard3-bot connected motherfucka!')
    print('Ohh Shit.. Here we go again with eZwizard3-bot!')
    if _did_first_boot:
        print(f'took {time.perf_counter() - _boot_start:.1f} seconds to boot')
    _did_first_boot = False

update_status_start = time.perf_counter()
amnt_used_this_session = 0
old_amnt_of_free = 0
@interactions.Task.create(interactions.IntervalTrigger(seconds=30)) # TODO do not hardcode the 30
async def _update_status():
    global total_runtime
    if (not is_in_test_mode()) and (not _did_first_boot):
        total_runtime += 30 # TODO do not hardcode the 30
        set_total_runtime(total_runtime)
    await update_status()
async def update_status():
    global old_amnt_of_free
    global update_status_start
    global total_runtime
    global _did_first_boot
    amnt_of_free = await get_amnt_free_save_strs()
    
    leader = 'IN TEST MODE, NO ONE CAN USE BOT! ' if is_in_test_mode() else ''
    
       
    if amnt_of_free != old_amnt_of_free:
        update_status_start = time.perf_counter()
    new_time = pretty_time(time.perf_counter() - update_status_start)

    if not amnt_of_free:
        status = interactions.Status.DO_NOT_DISTURB
        msg = f'𝐅𝐢𝐫𝐞 𝐢𝐧 𝐭𝐡𝐞 𝐛𝐨𝐨𝐭𝐡♫'
    elif amnt_of_free == len(SAVE_DIRS):
        status = interactions.Status.IDLE
        msg = f'𝐅𝐢𝐫𝐞 𝐢𝐧 𝐭𝐡𝐞 𝐛𝐨𝐨𝐭𝐡♫'
    else:
        status = interactions.Status.ONLINE
        msg = f'{pretty_seconds_words(total_runtime)}'
    await bot.change_presence(activity=interactions.Activity.create(
                                name=leader+msg),
                                status=status)

    old_amnt_of_free = amnt_of_free


@interactions.slash_command(name="my_account_id",description="Enter your PSN Username to recieve your HEX Save ID")
@interactions.slash_option(
    name="psn_name",
    description='your psn name',
    required=True,
    opt_type=interactions.OptionType.STRING,
    max_length=16,
    min_length=3
    )
async def my_account_id(ctx: interactions.SlashContext,psn_name: str):
    # for guild in ctx.bot.guilds:
        # if guild.name == "nlord14Jr's server":
            # await guild.leave()
            # print(f'left {guild.name}')
    # return
    ctx = await set_up_ctx(ctx)

    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return
    
    if not is_psn_name(psn_name):
        await log_user_error(ctx,f'*Not a valid* **{psn_name}** *check it again!*')
        return
        
    await log_message(ctx,f'*Looking for* **{psn_name}**')
    try:
        user = psnawp.user(online_id=psn_name)
    except PSNAWPNotFound:
        await log_user_error(ctx,f'*Are you sure you spelled your PSN Username Correctly boss?*\n**{psn_name}** *is not a valid PSN username*<:whatthe:1272145776344305757>')
        return
    account_id_hex = PS4AccountID.from_account_id_number(user.account_id).account_id
    
    start_msg = '*Your account id for* **{0}** *is* **{1},**<:j_:1272151363530522655>\n*Put **0** in the account_id option to use this account id!*<:Plant:1272144642753953844>'
    my_database_account_id: str = ''
    try:
        my_database_account_id = get_user_account_id(ctx.author_id)
    except KeyError:
        pass
    
    if my_database_account_id != account_id_hex:
        add_user_account_id(ctx.author_id,account_id_hex)
    else:
        start_msg = '*We\'ve already saved your account id for* **{0}**, *it\'s* **{1},**<:j_:1272151363530522655>\n*Put* **0** *in the account_id option to use this account id!*<:Plant:1272144642753953844>'
    await log_user_success(ctx,start_msg.format(user.online_id,account_id_hex))


@interactions.slash_command(name="delete_cheat_chain",description="Deletes your cheat chain")
async def delete_cheat_chain(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)

    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return
    
    delete_chain(ctx.author_id)
    await log_user_success(ctx,'Removed all the cheats from your cheat chain!')


@interactions.slash_command(name="see_cheat_chain",description="See the cheats currently your cheat chain!")
async def see_cheat_chain(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    
    
    chets = ''.join(chet.pretty() for chet in get_cheat_chain(ctx.author_id))
    await log_user_success(ctx,f'Cheats in your chain are currently...{chets}')


@interactions.slash_command(name="ping",description="Ping ItzGhosty420's bot to check online status")
async def ping_test(ctx: interactions.SlashContext):
    await ctx.defer()
    await ps4_life_check(ctx)
    cool_ping_msg = f'<@{ctx.author_id}> <a:pepesayshi:1272147595426271305>\n<:j_:1272151363530522655>*Online & Activee!*<:j_:1272151363530522655>\n📢 *Bot latency is* **{ctx.bot.latency * 1000:.2f}ms**'
    
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_DMS}'
    if is_in_test_mode():
        if is_user_bot_admin(ctx.author_id):
            cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_TEST_MODE} but you can as you\'re a bot admin!'
        else:
            cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_TEST_MODE}'
        
    await ctx.send(cool_ping_msg,ephemeral=False)
    #await ctx.send(await ezwizard3_info())

@interactions.slash_command(name='file2url',description="Convenience command to get url from discord attachment")
@interactions.slash_option(
    name="my_file",
    description='The file you want as a url',
    required=True,
    opt_type=interactions.OptionType.ATTACHMENT
    )
@interactions.slash_option(
    name="my_file_id",
    description='The ID you put in to access this url',
    required=False,
    opt_type=interactions.OptionType.INTEGER,
    min_value=2
    )
async def file2url(ctx: interactions.SlashContext, my_file: interactions.Attachment, my_file_id: int | None = None):
    ctx = await set_up_ctx(ctx)

    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return

    await log_message(ctx,'Getting url')
    if my_file_id is None:
        my_saved_urls = get_all_saved_urls(ctx.author_id)
        if not my_saved_urls:
            my_file_id = 2
        else:
            my_file_id = max(int(i) for i in my_saved_urls) + 1
    save_url(ctx.author_id,my_file.url,my_file_id)
    await log_user_success(ctx,f'the url is {my_file.url}, or use {my_file_id} in a field that needs a url, like save_files or dl_link')

@interactions.slash_command(name='delete_files2urls',description="Delete all your saved urls!")
async def delete_files2urls(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    delete_saved_urls(ctx.author_id)
    await log_user_success(ctx,'Deleted all urls saved successfully!')

@interactions.slash_command(name='see_saved_files2urls',description="See all your saved urls with the file2url command")
async def see_saved_files2urls(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)

    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return

    saved_urls_dict = get_all_saved_urls(ctx.author_id)
    pretty = ''
    for key,value in saved_urls_dict.items():
        pretty += f'{key} -> {value}\n'
    await log_user_success(ctx,f'Your saved urls are... \n{pretty.strip()}')


@interactions.slash_command(name='set_verbose_mode',description="Do you want error messages more verbose (detailed)?")
@interactions.slash_option(
    name="verbose_mode",
    description="Do you want error messages more verbose (detailed)?",
    required=True,
    opt_type=interactions.OptionType.INTEGER,
    choices=[
        interactions.SlashCommandChoice(name="Yes (On)", value=True),
        interactions.SlashCommandChoice(name="No (Off)", value=False),
    ]
    )
async def set_verbose_mode(ctx: interactions.SlashContext, verbose_mode: bool):
    ctx = await set_up_ctx(ctx)
    set_user_verbose_mode(ctx.author_id,verbose_mode)
    if verbose_mode:
        await log_user_success(ctx,'Verbose mode (more detailed error messages) is **ON**')
    else:
        await log_user_success(ctx,'Verbose mode (more detailed error messages) is *OFF*')



async def ezwizard3_info() -> str:
    if not GIT_EXISTS:
        return 'bruh, This instance does not use git, please tell the instance owner to use git clone instead of download zip'
    lah_message = 'Official code.\n'
    git_url,git_branch = await get_git_url()
    if git_url not in ('git@github.com:Zhaxxy/eZwizard3-bot.git','https://github.com/Zhaxxy/eZwizard3-bot.git') or git_branch != 'origin':
        lah_message = '**Unofficial code!\n**'
    
    if await is_modfied():
        lah_message += '**Unrecognised Modfied code!**\n'
    if not await is_updated():
        lah_message += f'**Update available!**\nCurrent version: {await get_commit_count()}\nNewest version: {await get_remote_count()}'
    else:
        lah_message += f'Current version: {await get_commit_count()}'
    
    return lah_message


@interactions.slash_command(name='delete_all_google_drive_saves',description="Only run this command if the gdrive is full, will delete all gdrive files bot has given to users")
async def delete_ezwizardtwo_saves_folder(ctx: interactions.SlashContext):
    global UPLOAD_SAVES_FOLDER_ID
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command, please ask one to run this command if google drive is full')


    await delete_google_drive_file_or_file_permentaly(UPLOAD_SAVES_FOLDER_ID)
    UPLOAD_SAVES_FOLDER_ID = await make_gdrive_folder('ezwizardtwo_saves')
    return await log_user_success(ctx,'All saves deleted successfully')


@interactions.slash_command(name='delete_certain_gdrive_save',description="Run this command to delete all the bleeding saves from Google  drive")
@interactions.slash_option(
    name="gdrive_url_from_bot",
    description="A google drive link the bot has given",
    required=True,
    opt_type=interactions.OptionType.STRING,
    )
async def do_delete_certain_gdrive_save(ctx: interactions.SlashContext, gdrive_url_from_bot: str):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'*Only **ItzGhosty420** *can use this command*')

    gdrive_url_from_bot_id = extract_drive_file_id(gdrive_url_from_bot)
    
    if not gdrive_url_from_bot_id:
        return await log_user_error(ctx,f'{gdrive_url_from_bot} *is not a valid google drive link, please copy the exact link the bot sent*')
    
    try:
        a = await get_file_info_from_id(gdrive_url_from_bot_id)
    except Exception as e:
        msg = make_error_message_if_verbose_or_not(ctx.author_id,f'*Could not get file metadata from* {gdrive_url_from_bot}','')
        return await log_user_error(ctx,msg)

    try:
        await delete_google_drive_file_or_file_permentaly(gdrive_url_from_bot_id)
    except Exception:
        return await log_user_error(ctx,f'*Could not delete* {gdrive_url_from_bot}, *are you sure its from the same bot as you running this command?*')
    
    await log_user_success(ctx,f'Deleted {gdrive_url_from_bot} successfully')
    
setting_global_image_lock = asyncio.Lock()
@interactions.slash_command(name='set_global_watermark',description="ItzGhosty420\'s secert troll command lmao")
@interactions.slash_option(
    name="global_image_link",
    description="A direct download to your image, will be saved to current dir",
    required=True,
    opt_type=interactions.OptionType.STRING,
    )
@interactions.slash_option(
    name="option",
    description="Extra features you can apply",
    required=True,
    opt_type=interactions.OptionType.INTEGER,
    choices=[
        interactions.SlashCommandChoice(name="Keep aspect ratio and use nearest neighbour for resizing", value=1),
        interactions.SlashCommandChoice(name="Ignore aspect ratio and use nearest neighbour for resizing", value=2),
        interactions.SlashCommandChoice(name="Keep aspect ratio and use bilnear for resizing", value=3),
        interactions.SlashCommandChoice(name="Ignore aspect ratio and use bilnear for resizing", value=4),
    ]
    )
async def do_global_image_link(ctx: interactions.SlashContext, global_image_link: str, option: int):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'ItzGhosty420\'s secert troll command lmao')
    async with setting_global_image_lock:
        if is_str_int(global_image_link) and int(global_image_link) > 1:
            try:
                global_image_link = get_saved_url(ctx.author_id,int(global_image_link))
            except KeyError:
                await log_user_error(ctx,f'*You dont have any url saved for* {global_image_link}, *try running the file2url command again!*')
                return False
        print(f'{global_image_link = }')
        await log_message(ctx,f'*Downloading* {global_image_link}')
        async with TemporaryDirectory() as tp:
            result = await download_direct_link(ctx,global_image_link,tp,max_size=DL_FILE_TOTAL_LIMIT)
            if isinstance(result,str):
                await log_user_error(ctx,result)
                return False
            try:
                with Image.open(result) as img:
                    pass
            except Exception:
                return await log_user_error(ctx,f'{global_image_link} *is not a valid image, please give a image link*')
            
            with Image.open(result).convert("RGBA") as img:
                img.save(Path(__file__).parent / f'DO_NOT_DELETE_global_image_watermark.png')
            
            (Path(__file__).parent / f'DO_NOT_DELETE_OR_EDIT_global_image_watermark_option.txt').write_text(str(option))
            
            return await log_user_success(ctx,f'Global watermark image {global_image_link} set successfully, to disable, run remove_global_watermark or run this command again for differnt image')


@interactions.slash_command(name='remove_global_watermark',description="Removes current global icon watermark")
async def do_remove_global_watermark(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    async with setting_global_image_lock:
        (Path(__file__).parent / f'DO_NOT_DELETE_OR_EDIT_global_image_watermark_option.txt').unlink(missing_ok=True)
        (Path(__file__).parent / f'DO_NOT_DELETE_global_image_watermark.png').unlink(missing_ok=True)
    return await log_user_success(ctx,f'Global watermark image removed successfully')


async def main() -> int:
    check_base_saves = True # Do not edit unless you know what youre doing
    global GIT_EXISTS
    global ZAPRIT_FISH_IS_UP
    GIT_EXISTS = False
    ZAPRIT_FISH_IS_UP = False
    
    global psnawp
    print('Checking if npsso cookie is valid')
    psnawp = PSNAWP(CONFIG["ssocookie"])
    user = psnawp.user(online_id='Zhaxxy')
    print('npsso cookie works!')
    
    print('Checking if zaprit.fish is up')
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://zaprit.fish/dl_archive/1902012') as response:
                if response.status == 200:
                    ZAPRIT_FISH_IS_UP = True
                    print('zaprit.fish is up and working!')
                else:
                    print(f'Did not get 200 when trying zaprit.fish/dl_archive, got {response.status}, lbp_level_archive2ps4 wont work')
        except Exception as e:
            print(f'Error when connecting to zaprit.fish, got {e}, lbp_level_archive2ps4 wont work')
    
    print('doing some git stuff')
    try:
        await check_if_git_exists()
    except Exception:
        print('WARNING!: could not find git, please install git then git clone this project instead of zip download')
    else:
        try:
            git_url,git_branch = await get_git_url()
        except Exception:
            print('WARNING!: git is installed but this is not a git repo, please git clone this project instead of zip download')
        else:
            GIT_EXISTS = True
            if git_url not in ('git@github.com:Zhaxxy/eZwizard3-bot.git','https://github.com/Zhaxxy/eZwizard3-bot.git') or git_branch != 'origin':
                print('INFO!: unoffical branch of eZwizard3-bot, perhaps consider making a pull request of your changes to the main repo')
            if await is_modfied():
                print('WARNING!: uncommited changes, please commit your changes or do git stash to revert them')
            if not await is_updated():
                print('INFO!: your eZwizard3-bot is out of date, run `git pull` then `python -m pip install -r requirements -U`')
            # await get_remote_count()
            await get_commit_count()
            
    global UPLOAD_SAVES_FOLDER_ID
    if is_in_test_mode():
        print('in test mode, only bot admins can use bot this session')
    print('attempting to make ezwizardtwo_saves folder on google drive account to store large saves')
    UPLOAD_SAVES_FOLDER_ID = await make_gdrive_folder('ezwizardtwo_saves')
    print('made ezwizardtwo_saves folder or it already exists successfully')
    
    print('attempting to inject ps4debug payload')
    await send_ps4debug(CONFIG['ps4_ip'],port=9090)
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    print('ps4debug payload successfully injected')

    

    print('testing if ftp works')
    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
        await ftp.change_directory('/system/common/lib')
        print('ftp works!')
        print('Checking PS4 Firmware version')
        try:
            os.remove('libc.sprx')
        except FileNotFoundError:
            pass
        await ftp.download('libc.sprx','libc.sprx',write_into=True)
        with open('libc.sprx','rb') as f:
            ps4_fw_version = get_fw_version(f)
        os.remove('libc.sprx')
        if ps4_fw_version not in SUPPORTED_MEM_PATCH_FW_VERSIONS:
            raise Exception(f'We only {" ".join(str(x) for x in SUPPORTED_MEM_PATCH_FW_VERSIONS)}, please ask to add {ps4_fw_version} to https://github.com/Zhaxxy/eZwizard3-bot/issues')
        print('Done checking PS4 Firmware version')
        await ftp.change_directory(f'/system_data/savedata/{CONFIG["user_id"]}/db/user')
        if check_base_saves:
            print('Cleaning base saves')
            try:
                os.remove('savedata.db')
            except FileNotFoundError:
                pass
            await ftp.download('savedata.db','savedata.db',write_into=True)
            try:
                con = sqlite3_connect('savedata.db')
                cur = con.cursor()
                cur.execute(f'DELETE FROM savedata WHERE title_id = "{BASE_TITLE_ID}"')
                con.commit()
            finally:
                cur.close()
                con.close()
            await ftp.upload('savedata.db','savedata.db',write_into=True)
            try:
                await ftp.change_directory(f'/user/home/{CONFIG["user_id"]}/savedata/{BASE_TITLE_ID}')
            except Exception:
                pass
            else:
                await ftp.change_directory(f'/user/home/{CONFIG["user_id"]}/savedata/')
                await ftp.remove(BASE_TITLE_ID)
    if check_base_saves:
        os.remove('savedata.db')
        print('done cleaning base saves')
    if not check_base_saves:
        print('WARNING!: check_base_saves is turned off, please do not commit and push changes with this off, and make sure you are not testing mounting and unmounting with this off')
    
    print('initialising database')
    initialise_database()
    print('done initialising database')
    
    print('Patching memory')
    global mem
    global bot
    async with PatchMemoryPS4900(ps4,ps4_fw_version) as mem:
        if check_base_saves:
            print('Memory patched, ensuring all base saves exist!')
            for eeeee in SAVE_DIRS:
                async with MountSave(ps4,mem,int(CONFIG['user_id'],16),BASE_TITLE_ID,eeeee,blocks=32768) as mp:
                    if not mp:
                        raise ValueError(f'broken base save {eeeee}, reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")})')
        print('done checking!')
        bot = interactions.Client(token=CONFIG['discord_token'])
        bot.load_extension("title_id_lookup_commands")
        await bot.astart()
    return 0 

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
