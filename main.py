import asyncio
import sys
from typing import NamedTuple, Callable, Generator, Any, Sequence, Coroutine, assert_never
from enum import Enum
from pathlib import Path
import shutil
from traceback import format_exc
from io import BytesIO
import time
import zipfile
import os
from datetime import datetime
from zlib import crc32 # put modules you need at the bottom of list for custom cheats, in correct block
import struct
import gzip

from psnawp_api import PSNAWP
from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound
from aiofiles.tempfile import TemporaryDirectory, TemporaryFile
import interactions
from sqlitedict import SqliteDict
import aiohttp
import aioftp
from ps4debug import PS4Debug
from PIL import Image
from lbptoolspy import far4_tools as f4 # put modules you need at the bottom of list for custom cheats, in correct block

from string_helpers import extract_drive_folder_id, extract_drive_file_id, is_ps4_title_id, make_folder_name_safe,pretty_time, load_config, CUSA_TITLE_ID, chunker
from archive_helpers import get_archive_info, extract_single_file, filename_valid_extension,SevenZipFile
from gdrive_helpers import get_gdrive_folder_size, list_files_in_gdrive_folder, gdrive_folder_link_to_name, get_valid_saves_out_names_only, download_file, get_file_info_from_id, GDriveFile, download_folder, google_drive_upload_file, make_gdrive_folder
from savemount_py import PatchMemoryPS4900,MountSave,ERROR_CODE_LONG_NAMES,unmount_save,send_ps4debug
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

CANT_USE_BOT_IN_DMS = 'Sorry, but the owner of this instance has disabled commands in dms'

FILE_SIZE_TOTAL_LIMIT = 967_934_048
DL_FILE_TOTAL_LIMIT = 50_000_000 # 50mb
ATTACHMENT_MAX_FILE_SIZE = 24_000_000 # 24mb
ZIP_LOOSE_FILES_MAX_AMT = 100
MAX_RESIGNS_PER_ONCE = 99
DOWNLOAD_CHUNK_SIZE = 1024
AMNT_OF_CHUNKS_TILL_DOWNLOAD_BAR_UPDATE = 50_000
PS4_ICON0_DIMENSIONS = 228,128

CONFIG = load_config()
SAVE_FOLDER_ENCRYPTED = f'/user/home/{CONFIG["user_id"]}/savedata/YAHY40786'
MOUNTED_POINT = Path('/mnt/sandbox/NPXS20001_000')

PS4_SAVE_KEYSTONES = {
    'CUSA05350':b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb5\xaa\xa6\xdd\x19*\xfd\xdd\x8dy\x93\x8eJ\xce\x13\x7f\xd4H\x1d\xf1\x11\xbd\x18\x8a\xf3\x02\xc5l6j\x91\x12K\xcbZe\x06tj\x9d\x08\xd53;\xc1\x9cD\x96h\xff\xef\xe2\x18$W\x96\x8fQ\xa1\xc8<\x0b\x18\x96',
    'CUSA05088':b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00&\xedp\x94\xb2\x94\xa3\x9bc\xbd\x94\x11;\x06l\x93x\x9d\xc2K\xe2\xed\xfc\xd78\xff\xdd\x8dU\x86\xab\xd8N\x1dx8q\xcf\xd3\x0b\xfc\x8cr<il\xbbd\xbd\x17\xbe(?\x85Xn\xa5\xf4T\xe8s\xdcu\xaa'
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
#         shutil.rmtree(self.new_path)


_token_getter = asyncio.Semaphore(1)
async def get_time_as_string_token() -> str:
    async with _token_getter:
        return datetime.now().strftime("%d_%m_%Y__%H_%M_%S")


async def set_up_ctx(ctx: interactions.SlashContext,*,mode = 0) -> interactions.SlashContext:
    await ctx.defer()
    # t = await ctx.respond(content='...')
    # await ctx.delete(t)
    ctx.mode = mode
    return ctx


async def log_message(ctx: interactions.SlashContext, msg: str,*,_do_print: bool = True):
    if _do_print:
        print(msg)

    channel = ctx.channel or ctx.author
    try:
        msg = ctx.omljustusethe0optionsaccountid + msg
    except AttributeError:
        pass
    
    
    for msg_chunk in chunker(msg,1999):
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
        await log_message(ctx, f'{msg} {tick} seconds spent here', _do_print=False)
        await asyncio.sleep(10)
        tick += 10

async def log_user_error(ctx: interactions.SlashContext, error_msg: str):
    # if error_msg == 'Theres too many people using the bot at the moment, please wait for a spot to free up':
        # # await ctx.send('...',ephemeral=False)
        # return
    print(f'user bad ##################\n{error_msg}')
    channel = ctx.channel or ctx.author
    try:
        error_msg = ctx.omljustusethe0optionsaccountid + error_msg
    except AttributeError:
        pass
    full_msg = f'<@{ctx.author_id}> Uh oh: {error_msg}'
    first_time = True
    
    for msg_chunk in chunker(full_msg,1999):
        if ctx.expired:
            await channel.send(msg_chunk,ephemeral=False)
        else:
            if first_time:
                placeholder_meesage_to_allow_ping_to_actually_ping_the_user = await ctx.send('...',ephemeral=False)
            await ctx.send(msg_chunk,ephemeral=False) 
            if first_time:
                await ctx.delete(placeholder_meesage_to_allow_ping_to_actually_ping_the_user)
        first_time = False
            
    await update_status()

async def log_user_success(ctx: interactions.SlashContext, success_msg: str, file: str | None = None):
    print(f'{ctx.user} id: {ctx.author_id} sucesfully did a command with msg: {success_msg}')
    channel = ctx.channel or ctx.author
    try:
        success_msg = ctx.omljustusethe0optionsaccountid + success_msg
    except AttributeError:
        pass
    full_msg = f'<@{ctx.author_id}>: {success_msg}'
    first_time = True
    
    for msg_chunk in chunker(full_msg,1999):
        if ctx.expired:
            await channel.send(full_msg,ephemeral=False, file=file)
        else:
            if first_time:
                placeholder_meesage_to_allow_ping_to_actually_ping_the_user = await ctx.send('...',ephemeral=False)
            await ctx.send(full_msg,ephemeral=False, file=file) 
            if first_time:
                await ctx.delete(placeholder_meesage_to_allow_ping_to_actually_ping_the_user)
        first_time = False

    await update_status()

class ChangeSaveIconOption(Enum):
    KEEP_ASPECT_NEAREST_NEIGHBOUR = 1
    IGNORE_ASPECT_NEAREST_NEIGHBOUR = 2
    KEEP_ASPECT_BILINEAR = 3
    IGNORE_ASPECT_BILINEAR = 4 

class SaveMountPointResourceError(Exception):
    """
    Raised when theres no more free resources
    """


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

mounted_saves_at_once = asyncio.Semaphore(1) # 3 i sadly got an unmount error, and with 2 too

class PS4AccountID:
    __slots__ = ('_account_id',)
    def __init__(self, account_id: str):
        if len(account_id) != 16:
            raise ValueError('Invalid account id, lenght is not 16')
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


class CheatFunc(NamedTuple):
    func: Coroutine[None, None, str | None]
    kwargs: dict[str,Any]

    def pretty(self): # TODO make this not expose username in Path objects, make it just print name string instead ig
        return f"```py\nawait {self.func.__name__}({', '.join(f'{a}={b!r}' for a,b in self.kwargs.items())})```"

class CheatFuncResult(NamedTuple):
    savename: str | None
    gameid: str | None


class DecFunc(NamedTuple):
    func: Coroutine
    kwargs: dict[str,Any]

    def pretty(self): # TODO make this not expose username in Path objects, make it just print name string instead ig
        return f"```py\nawait {self.func.__name__}({', '.join(f'{a}={b!r}' for a,b in self.kwargs.items())})```"

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

def get_total_amnt_used():
    with SqliteDict("user_stuff.sqlite", tablename="total_amnt_used") as db:
        return db["total_amnt_used_value"]


def save_url(author_id: str, url: str, url_id: int):
    if type(url_id) != int or url_id <= 1:
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
    if type(url_id) != int or url_id <= 1:
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
    if account_id == '0':
        try:
            return PS4AccountID(get_user_account_id(author_id))
        except KeyError:
            return 'You dont have any account id saved to the database!, try running the `/my_account_id` again'
    elif account_id == '1':
        return PS4AccountID('0000000000000000')

    try:
        my_account_id = PS4AccountID(account_id)
        try:
            my_account_id_for_my_acc = PS4AccountID(get_user_account_id(author_id))
        except KeyError: pass
        else:
            if my_account_id_for_my_acc == my_account_id:
                ctx.omljustusethe0optionsaccountid = '**Remember, you dont have to manually type in your account id, just put 0 in the field!**\n\n'
        return my_account_id
    except ValueError:
        return f'{account_id} is not a valid account id, it should be the one in your SAVEDATA folder! Or get it from the `/my_account_id` command'


def list_ps4_saves(folder_containing_saves: Path,/) -> Generator[tuple[Path,Path],None,None]:
    for filename in folder_containing_saves.rglob('*'):
        if is_ps4_title_id(filename.parent.name) and filename.suffix == '.bin' and filename.is_file() and Path(filename.with_suffix('')).is_file():
            yield filename,Path(filename.with_suffix(''))


async def ps4_life_check(ctx: interactions.SlashContext | None = None):
    channel = ctx.channel or ctx.author
    try:
        await ps4.notify('life check!')
    except Exception:
        try:
            await channel.send(HUH) if ctx else None
        except Exception:
            pass
        await ctx.bot.stop()
        assert_never('bot should be ended')
    


async def extract_ps4_encrypted_saves_archive(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID, archive_name: Path) -> str:
        await log_message(ctx,f'Checking {link} if valid archive')
        try:
            a = await get_archive_info(archive_name)
        except Exception as e:
            return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'

        if a.total_uncompressed_size > FILE_SIZE_TOTAL_LIMIT:
            return f'The decompressed {link} is too big, the max is {FILE_SIZE_TOTAL_LIMIT/1_048_576}mb'
        
        await log_message(ctx,f'Looking for saves in {link}')
        ps4_saves: list[tuple[Path,Path]] = []
        for zip_file in a.files.values():
            if not zip_file.is_file: continue
            if not is_ps4_title_id(zip_file.path.parent.name): continue
            if not zip_file.path.suffix == '.bin': continue

            white_file = zip_file.path.with_suffix('')
            if not a.files.get(white_file): continue
            if zip_file.size != 96:
                return f'Invalid bin file {zip_file.path} found in {link}'

            ps4_saves.append((zip_file.path,white_file))
        if not ps4_saves:
            return f'Could not find any saves in {link}, maybe you forgot to pack the whole CUSAXXXXX folder?'

        if len(ps4_saves) > MAX_RESIGNS_PER_ONCE:
            return f'The archive {link} has too many saves {len(ps4_saves)}, the max is {MAX_RESIGNS_PER_ONCE} remove {len(ps4_saves) - MAX_RESIGNS_PER_ONCE} saves and try again'
        
        for bin_file,white_file in ps4_saves:
            pretty_dir_name = make_folder_name_safe(bin_file.parent)
            new_path = Path(output_folder,pretty_dir_name,make_ps4_path(account_id,bin_file.parent.name))
            new_path.mkdir(exist_ok=True,parents=True) # TODO look into parents=True
            await log_message(ctx,f'Extracting {white_file} from {link}')
            try:
                await extract_single_file(archive_name,white_file,new_path)
                await extract_single_file(archive_name,bin_file,new_path)
            except Exception as e:
                return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
        return ''


async def download_direct_link(ctx: interactions.SlashContext,link: str, donwload_location: Path, validation: Callable[[str], str] = None, max_size: int = FILE_SIZE_TOTAL_LIMIT) -> Path | str:
    if not validation:
        validation = lambda x: ''

    new_link = extract_drive_file_id(link)
    if new_link:
        await log_message(ctx,f'Getting file metadata from {link}')
        try:
            zip_file = await get_file_info_from_id(new_link)
        except Exception as e:
            return f'Could not get file metadata from {link}, got error {type(e).__name__}: {e}, maybe its not public?'
        if validation_result := validation(zip_file.file_name_as_path):
            return f'invalid file {link} reason: {validation_result}'
        
        if zip_file.size > max_size:
            return f'The file {link} is too big, we only accept {max_size}bytes, if you think this is wrong please report it'
        if zip_file.size < 1:
            return f'The file {link} is too small lmao wyd'

        archive_name = Path(donwload_location,zip_file.file_name_as_path.name)
        try:
            await log_message(ctx,f'Downloading {zip_file.file_name_as_path.name} from {link}')
            await download_file(zip_file.file_id,archive_name)
        except Exception:
            return f'blud thinks hes funny'
        return archive_name

    if extract_drive_folder_id(link):
        return f'For this option we do not take in folder urls {link}'
    
    link = link.replace('media.discordapp.net','cdn.discordapp.com')
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(link) as response:
                if response.status == 200:
                    try:
                        filename = response.headers.get('Content-Disposition','').split('filename=')[1].strip().replace('"','').replace("'",'')
                    except IndexError:
                        filename = link.split('/')[-1].split('?')[0]
                    if validation_result := validation(filename):
                        return f'invalid file {link} reason: {validation_result}'
                    file_size = int(response.headers.get('Content-Length', 0))
                    if file_size > max_size:
                        return f'The file {link} is too big, we only accept {max_size/1_048_576}mb, if you think this is wrong please report it'
                    if file_size < 1:
                        return f'The file {link} is too small lmao, or there was no Content-Length header'
                    downloaded_size = 0
                    chunks_done = 0
                    direct_zip = Path(donwload_location,filename)
                    with open(direct_zip, 'wb') as f:
                        while True:
                            if not(chunks_done % AMNT_OF_CHUNKS_TILL_DOWNLOAD_BAR_UPDATE):
                                await log_message(ctx,f'Downloaded {link} {downloaded_size/1_048_576}mb')
                            chunk = await response.content.read(DOWNLOAD_CHUNK_SIZE)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_size += DOWNLOAD_CHUNK_SIZE
                            chunks_done += 1
                            if downloaded_size > FILE_SIZE_TOTAL_LIMIT:
                                return f'YOU LIED! {link} is too big, we only accept {max_size/1_048_576}mb, if you think this is wrong please report it'
                    await log_message(ctx,f'Downloaded {link} {downloaded_size/1_048_576}mb')
                else:
                    return f'Failed to download {link}. Status code: {response.status}'
        except Exception as e:
            return f'Invalid url {link} ({type(e).__name__}: {e}), maybe you copied the wrong link?'
    return direct_zip



async def download_decrypted_savedata0_folder(ctx: interactions.SlashContext,link: str, output_folder: Path) -> str:
    """
    For now at least, we are only gonna allow one encryption at a time
    """
    new_link = extract_drive_folder_id(link)
    if new_link:
        await log_message(ctx,f'Getting files metadata from folder {link}')
        try:
            raw_files = await list_files_in_gdrive_folder(new_link,await gdrive_folder_link_to_name(new_link),False)
        except Exception as e:
            return f'Could not get files metadata from folder {link}, got error {type(e).__name__}: {e}, maybe its not public?'
        await log_message(ctx,f'Looking for a savedata0 folder in {link}')
        seen_savedata0_folders: set[GDriveFile] = {
            raw_files[Path(*(p.file_name_as_path.parts[:p.file_name_as_path.parts.index('savedata0')+1]))]
            for p in raw_files.values()
            if not p.is_file and 'savedata0' in p.file_name_as_path.parts
        }

        if not seen_savedata0_folders:
            return f'Could not find any decrypted saves in {link}, make sure to put the decrypted save contents in a savedata0 folder and upload that'

        if len(seen_savedata0_folders) > 1:
            return f'Too many decrypted saves in {link}, we only support encrypting one save per command'

        for x in seen_savedata0_folders:
            savedata0_folder = x
        await log_message(ctx,f'Checking if {link} savedata0 folder is too big or not')
        try:
            test = await get_gdrive_folder_size(savedata0_folder.file_id)
        except Exception:
            return 'blud thinks hes funny'
        if test[0] > FILE_SIZE_TOTAL_LIMIT:
            return f'The decrypted save {link} is too big, maybe you uploaded a wrong file to it? max is {FILE_SIZE_TOTAL_LIMIT/1_048_576}mb'
        if test[1] > ZIP_LOOSE_FILES_MAX_AMT:
            return f'The decrypted save {link} has too many loose files, max is {ZIP_LOOSE_FILES_MAX_AMT} loose files'

        await log_message(ctx,f'Downloading {link} savedata0 folder')
        Path(output_folder,'savedata0').mkdir(parents=True,exist_ok=True)# TODO maybe i dont gotta do this, but i am
        try:
            await download_folder(savedata0_folder.file_id,Path(output_folder,'savedata0'))
        except Exception:
            return 'blud thinks hes funny'
        return ''
    
    async with TemporaryDirectory() as tp:
        direct_zip = await download_direct_link(ctx,link,tp,filename_valid_extension)
        if isinstance(direct_zip,str):
            return direct_zip
        return await extract_savedata0_decrypted_save(ctx,link,output_folder,direct_zip)



async def extract_savedata0_decrypted_save(ctx: interactions.SlashContext,link: str, output_folder: Path, archive_name: Path) -> str:
    await log_message(ctx,f'Checking {link} if valid archive')
    try:
        a = await get_archive_info(archive_name)
    except Exception as e:
        return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'

    if a.total_uncompressed_size > FILE_SIZE_TOTAL_LIMIT:
        return f'The decompressed {link} is too big, the max is {FILE_SIZE_TOTAL_LIMIT} bytes'

    if len(a.files) > ZIP_LOOSE_FILES_MAX_AMT:
        return f'The decompressed {link} has too many loose files, max is {ZIP_LOOSE_FILES_MAX_AMT} loose files'

    await log_message(ctx,f'Looking for decrypted saves in {link}')
    seen_savedata0_folders: set[SevenZipFile] = {
        a.files[Path(*(p.path.parts[:p.path.parts.index('savedata0')+1]))]
        for p in a.files.values()
        if not p.is_file and 'savedata0' in p.path.parts
    }
    if not seen_savedata0_folders:
        return f'Could not find any decrypted saves in {link}, make sure to put the decrypted save contents in a savedata0 folder and archive that'

    if len(seen_savedata0_folders) > 1:
        return f'Too many decrypted saves in {link}, we only support encrypting one save per command'

    for x in seen_savedata0_folders:
        savedata0_folder = x
    
    await log_message(ctx,f'Extracting savedata0 from {link}')
    try:
        await extract_single_file(archive_name,savedata0_folder.path,output_folder,'x')
    except Exception as e:
        return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
    if not savedata0_folder.path == Path('savedata0'):
        await log_message(ctx,f'Doing some file management with {link}')
        shutil.move(Path(output_folder, savedata0_folder.path),output_folder)
        if savedata0_folder.path.parts[0] != Path('savedata0'):
            shutil.rmtree(Path(output_folder,savedata0_folder.path.parts[0]))

    return ''


async def download_ps4_saves(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID) -> str:
    """\
    function to download ps4 encrypted saves from a user given link, if anything goes wrong then a string error is returned, otherwise empty string (falsely).
    the output_folder will contain the ps4 encrypted saves, itll be in a nice format that is ready for sending
    """
    new_link = extract_drive_folder_id(link)
    if new_link:
        await log_message(ctx,f'Getting files metadata from folder {link}')
        try:
            raw_files = await list_files_in_gdrive_folder(new_link,await gdrive_folder_link_to_name(new_link))
        except Exception as e:
            return f'Could not get files metadata from folder {link}, got error {type(e).__name__}: {e}, maybe its not public?'
        await log_message(ctx,f'Looking for saves in the folder {link}')
        ps4_saves = get_valid_saves_out_names_only(raw_files.values())
        
        if not ps4_saves:
            return f'Could not find any saves in the folder {link}, maybe you forgot to upload the whole CUSAXXXXX folder?'
        total_ps4_saves_size = sum(x.bin_file.size + x.white_file.size for x in ps4_saves)

        if len(ps4_saves) > MAX_RESIGNS_PER_ONCE:
            return f'The folder {link} has too many saves {len(ps4_saves)}, the max is {MAX_RESIGNS_PER_ONCE} remove {len(ps4_saves) - MAX_RESIGNS_PER_ONCE} saves and try again'

        if total_ps4_saves_size > FILE_SIZE_TOTAL_LIMIT:
            return f'The total number of saves in {link} is too big, the max size of saves is {FILE_SIZE_TOTAL_LIMIT/1_048_576}mb, {total_ps4_saves_size} bytes is too big'

        for bin_file,white_file in ps4_saves:
            if bin_file.size != 96:
                return f'Invalid bin file {bin_file.file_name_as_path} found in {link}'
            
            new_white_path = Path(output_folder, make_folder_name_safe(white_file.file_name_as_path.parent), make_ps4_path(account_id,white_file.file_name_as_path.parent.name),white_file.file_name_as_path.name)
            new_bin_path = Path(output_folder, make_folder_name_safe(bin_file.file_name_as_path.parent), make_ps4_path(account_id,bin_file.file_name_as_path.parent.name),bin_file.file_name_as_path.name)

            await log_message(ctx,f'Downloading {white_file.file_name_as_path} from {link}')
            try:
                await download_file(white_file.file_id,new_white_path)
                await download_file(bin_file.file_id,new_bin_path)
            except Exception:
                return 'blud thinks hes funny'
        return ''


    async with TemporaryDirectory() as tp:
        direct_zip = await download_direct_link(ctx,link,tp,filename_valid_extension)
        if isinstance(direct_zip,str):
            return direct_zip
        return await extract_ps4_encrypted_saves_archive(ctx,link,output_folder,account_id,direct_zip)


async def upload_encrypted_to_ps4(ctx: interactions.SlashContext, bin_file: Path, white_file: Path,parent_dir: Path, save_dir_ftp: str):
    ftp_bin = f'{save_dir_ftp}.bin'
    ftp_white = f'sdimg_{save_dir_ftp}'
    pretty_save_dir = white_file.relative_to(parent_dir)
    # await log_message(ctx,'Ensuring base save exists on ps4 before uploading')
    # async with MountSave(ps4,mem,int(CONFIG['user_id'],16),'YAHY40786',save_dir_ftp) as mp:
        # pass
    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,'Connecting to PS4 ftp to upload encrpyted save (this may take a while if mutiple slots are in use)'))
    async with mounted_saves_at_once:
        tick_tock_task.cancel()
        async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
            await log_message(ctx,f'Pwd to {SAVE_FOLDER_ENCRYPTED}')
            await ftp.change_directory(SAVE_FOLDER_ENCRYPTED)
            await log_message(ctx,f'Uploading {pretty_save_dir} to ps4')
            await ftp.upload(bin_file,ftp_bin,write_into=True)
            await ftp.upload(white_file,ftp_white,write_into=True)

async def download_encrypted_from_ps4(ctx: interactions.SlashContext, bin_file_out: Path, white_file_out: Path,parent_dir: Path, save_dir_ftp: str):
    ftp_bin = f'{save_dir_ftp}.bin'
    ftp_white = f'sdimg_{save_dir_ftp}'
    pretty_save_dir = white_file_out.relative_to(parent_dir)
    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,'Connecting to PS4 ftp to download encrpyted save (this may take a while if mutiple slots are in use)'))
    async with mounted_saves_at_once:
        tick_tock_task.cancel()
        async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
            await log_message(ctx,f'Pwd to {SAVE_FOLDER_ENCRYPTED}')
            await ftp.change_directory(SAVE_FOLDER_ENCRYPTED)
            await log_message(ctx,f'Downloading {pretty_save_dir} from ps4')
            await ftp.download(ftp_bin,bin_file_out,write_into=True)
            await ftp.download(ftp_white,white_file_out,write_into=True)


async def resign_mounted_save(ctx: interactions.SlashContext, ftp: aioftp.Client,new_mount_dir:str, account_id: PS4AccountID) -> PS4AccountID:
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
        await log_message(ctx,f'Something went wrong when resinging the save, {type(e).__name__}: {e}, ignoring!')
    finally:
        return old_account_id

async def apply_cheats_on_ps4(ctx: interactions.SlashContext,account_id: PS4AccountID, bin_file: Path, white_file: Path, parent_dir: Path, cheats: Sequence[CheatFunc], save_dir_ftp: str | tuple[str,str]) -> str | tuple[list | PS4AccountID]:
    pretty_save_dir = white_file.relative_to(parent_dir)
    await log_message(ctx,f'Attempting to mount {pretty_save_dir}')
    mount_save_title_id = 'YAHY40786' if isinstance(save_dir_ftp,str) else save_dir_ftp[1]
    try:
        async with MountSave(ps4,mem,int(CONFIG['user_id'],16),mount_save_title_id,save_dir_ftp) as mp:
            savedatax = mp.savedatax
            new_mount_dir = (MOUNTED_POINT / savedatax).as_posix()
            if not mp:
                return f'Could not mount {pretty_save_dir}, reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")})'
            # input(f'{mp}\n {new_mount_dir}')
            for index, chet in enumerate(cheats):
                results = []
                try:
                    await log_message(ctx,'Connecting to PS4 ftp to do some cheats')
                    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                        await ftp.change_directory(new_mount_dir) 
                        await log_message(ctx,f'Applying cheat {chet.pretty()} {index + 1}/{len(cheats)} for {pretty_save_dir}')
                        result = await chet.func(ftp,new_mount_dir,white_file.name,**chet.kwargs)
                    results.append(result) if result else None
                except Exception:
                    return f'Could not apply cheat {chet.pretty()}to {pretty_save_dir}. reason: ```{format_exc()}```'
            await log_message(ctx,'Connecting to PS4 ftp to do resign')
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                await ftp.change_directory(new_mount_dir) 
                await log_message(ctx,f'Resinging {pretty_save_dir} to {account_id.account_id}')
                account_id_old = await resign_mounted_save(ctx,ftp,new_mount_dir,account_id)
            return results,account_id_old
    finally:
        if savedatax:
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                try:
                    await ftp.change_directory(new_mount_dir) # check if we are still mounted
                except Exception:
                    pass#print(f'{type(e).__name__}: {e}')
                else:
                    await ftp.upload(Path(__file__).parent / 'savemount_py/backup_dec_save/sce_sys')
                    umount_p = await unmount_save(ps4,mem,mp)
                    if umount_p:
                        try:
                            await ftp.change_directory(new_mount_dir)
                        except Exception: pass
                        else:
                            await log_user_error(ctx,'WARNING WARNING SAVE DIDNT UNMOUNT, MANUAL ASSITENCE IS NEEDED!!!!!!!!')
                            breakpoint()
                    return f'Could not unmount {pretty_save_dir} likley corrupted param.sfo or something went wrong with the bot, best to report it with the save you provided'


async def decrypt_saves_on_ps4(ctx: interactions.SlashContext, bin_file: Path, white_file: Path, parent_dir: Path,decrypted_save_ouput: Path, save_dir_ftp: str,decrypt_fun: DecFunc | None = None) -> str:
    pretty_save_dir = white_file.relative_to(parent_dir)
    await log_message(ctx,'Connecting to PS4 ftp to do some decrypts')

    await log_message(ctx,f'Attempting to mount {pretty_save_dir}')
    try:
        async with MountSave(ps4,mem,int(CONFIG['user_id'],16),'YAHY40786',save_dir_ftp) as mp:
            savedatax = mp.savedatax
            new_mount_dir = (MOUNTED_POINT / savedatax).as_posix()
            if not mp:
                return f'Could not mount {pretty_save_dir}, reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")})'
            if decrypt_fun:
                await log_message(ctx,f'Doing custom decryption {decrypt_fun.pretty()} for {pretty_save_dir}')
                async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                    await ftp.change_directory(new_mount_dir)
                    try:
                        await decrypt_fun.func(ftp,new_mount_dir,white_file.name,decrypted_save_ouput,**decrypt_fun.kwargs)
                    except Exception:
                        return f'Could not custom decrypt your save {pretty_save_dir}, reason ```{format_exc()}```'
            else:
                await log_message(ctx,f'Downloading savedata0 folder from decrypted {pretty_save_dir}')
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
                    await ftp.upload(Path(__file__).parent / 'savemount_py/backup_dec_save/sce_sys')
                    umount_p = await unmount_save(ps4,mem,mp)
                    if umount_p:
                        try:
                            await ftp.change_directory(new_mount_dir) # check if we are still mounted
                        except Exception: pass
                        else:
                            await log_user_error(ctx,'WARNING WARNING SAVE DIDNT UNMOUNT, MANUAL ASSITENCE IS NEEDED!!!!!!!!')
                            breakpoint()
                    return f'Could not unmount {pretty_save_dir} likley corrupted param.sfo or something went wrong with the bot, best to report it the save you provided'


def _zipping_time(ctx: interactions.SlashContext,link_for_pretty: str,results: Path, parent_dir: Path, new_zip_name: Path, custom_msg):
    with zipfile.ZipFile(new_zip_name,'w') as zp:
        for file in results.rglob('*'):
            zp.write(file,file.relative_to(parent_dir))


async def send_result_as_zip(ctx: interactions.SlashContext,link_for_pretty: str,results: Path, parent_dir: Path, new_zip_name: Path, custom_msg: str = 'paypal me some money eboot.bin@protonmail.com and i might fix this message'):
    global amnt_used_this_session
    await log_message(ctx,f'Zipping up modified {link_for_pretty} saves')
    await asyncio.to_thread(_zipping_time,ctx,link_for_pretty,results,parent_dir,new_zip_name,custom_msg)

    if new_zip_name.stat().st_size > ATTACHMENT_MAX_FILE_SIZE:
        await log_message(ctx,f'Uploading modified {link_for_pretty} saves to google drive')
        try:
            how_do_i_name_variables = await google_drive_upload_file(new_zip_name,UPLOAD_SAVES_FOLDER_ID)
        except Exception as e:
            if 'storageQuotaExceeded' in str(e):
                pingers = ' '.join(f'<@{id}>' for id in CONFIG['bot_admins'])
                await log_message(ctx,f'oh no the bots owner gdrive is full, im giving you 2 minutes to ask {pingers} to clear some space')
                await asyncio.sleep(2*60)
                try:
                    how_do_i_name_variables = await google_drive_upload_file(new_zip_name,UPLOAD_SAVES_FOLDER_ID)
                except Exception as e2:
                    if 'storageQuotaExceeded' in str(e2):
                        await log_user_error(ctx,f'You were too late, owners gdrive is full! ask {pingers} to clear some space')
                        return
                    else:
                        raise
            else:
                raise
        await log_user_success(ctx,f'Here is a google drive link to your {custom_msg.strip()}\n{how_do_i_name_variables}\nPlease download this asap as it can be deleted at any time')
    else:
        # shutil.move(new_zip_name,new_zip_name.name)
        await log_message(ctx,f'Uploading modified {link_for_pretty} saves as a discord zip attachment')
        await log_user_success(ctx,f'Here is a discord zip attachment to your {custom_msg.strip()}\nPlease download this asap as it can be deleted at any time',file=str(new_zip_name))
        # os.remove(new_zip_name.name)
    amnt_used_this_session += 1
    add_1_total_amnt_used()

############################00 Real commands stuff
def dec_enc_save_files(func):
    return interactions.slash_option(
    name="save_files",
    description="a google drive folder link containing your encrypted saves to be decrpyted",
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
    return interactions.slash_option(name='filename_p',description='If mutiple files are found, it will look for a file with this name, put path if in folder',opt_type=interactions.OptionType.STRING,required=False)(func)# (like man4/mysave.sav)')

async def pre_process_cheat_args(ctx: interactions.SlashContext,cheat_chain: Sequence[CheatFunc | DecFunc],chet_files_custom: Path, savedata0_folder:Path) -> bool:
    await log_message(ctx,f'Looking for any `dl_link`s or `savedata0`s to download')
    for cheat in cheat_chain:
        for arg_name,link in cheat.kwargs.items():
            if arg_name.startswith('dl_link'):
                if link.isdigit() and int(link) > 1:
                    try:
                        link = get_saved_url(ctx.author_id,int(link))
                    except KeyError:
                        await log_user_error(ctx,f'You dont have any url saved for {link}, try running the file2url command again!')
                        return False
                await log_message(ctx,f'Downloading {link} {arg_name}')
                result = await download_direct_link(ctx,link,chet_files_custom,max_size=DL_FILE_TOTAL_LIMIT)
                if isinstance(result,str):
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = result
            if isinstance(link,interactions.Attachment):
                await log_message(ctx,f'Downloading attachment {arg_name}')
                result = await download_direct_link(ctx,link.url,chet_files_custom,max_size=DL_FILE_TOTAL_LIMIT)
                if isinstance(result,str):
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = result
            if arg_name == 'decrypted_save_file':
                await log_message(ctx,f'Downloading {link} savedata0 folder or zip')
                result = await download_decrypted_savedata0_folder(ctx,link,savedata0_folder)
                if result:
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = savedata0_folder
            if arg_name == 'gameid' and (not is_ps4_title_id(link)):
                await log_user_error(ctx,f'Invalid gameid {link}')
                return False
            if arg_name.startswith('psstring'):
                link = link.encode('utf-8')
                for specparemcodelol in PARAM_SFO_SPECIAL_STRINGS:
                    link = link.replace(specparemcodelol.encode('ascii'),bytes.fromhex(specparemcodelol))
                    cheat.kwargs[arg_name] = link
            if arg_name.endswith('_p'):
                cheat.kwargs[arg_name] = link.replace('\\','/')
    return True

async def base_do_dec(ctx: interactions.SlashContext,save_files: str, decrypt_fun: DecFunc | None = None):
    ctx = await set_up_ctx(ctx)
    await ps4_life_check(ctx)

    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return
    
    if save_files.isdigit() and int(save_files) > 1:
        try:
            save_files = get_saved_url(ctx.author_id,int(save_files))
        except KeyError:
            await log_user_error(ctx,f'You dont have any url saved for {save_files}, try running the file2url command again!')
            return
    
    try:
        save_dir_ftp = await get_save_str()
    except SaveMountPointResourceError:
        await log_user_error(ctx,'Theres too many people using the bot at the moment, please wait for a spot to free up')
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
                tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'Getting ready to mount {pretty_folder_thing} (this may take a while if mutiple slots are in use)'))
                async with mounted_saves_at_once:
                    tick_tock_task.cancel()
                    a = await decrypt_saves_on_ps4(ctx,bin_file,white_file,enc_tp,new_dec,save_dir_ftp,decrypt_fun)
                if a:
                    await log_user_error(ctx,a)
                    return
            your_saves_msg = 'savedata0 decrypted save'
            if decrypt_fun:
               your_saves_msg = (decrypt_fun.__doc__ or 'paypal me some money eboot.bin@protonmail.com and i might fix this message').strip()
            await send_result_as_zip(ctx,save_files,dec_tp,dec_tp,Path(tp,my_token + '.zip'),your_saves_msg)
            return
    finally:
        await free_save_str(save_dir_ftp)


async def base_do_cheats(ctx: interactions.SlashContext, save_files: str,account_id: str, cheat: CheatFunc):
    ctx = await set_up_ctx(ctx)
    await ps4_life_check(ctx)

    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return

    if save_files.isdigit() and int(save_files) > 1:
        try:
            save_files = get_saved_url(ctx.author_id,int(save_files))
        except KeyError:
            await log_user_error(ctx,f'You dont have any url saved for {save_files}, try running the file2url command again!')
            return

    account_id = account_id_from_str(account_id,ctx.author_id,ctx)
    if isinstance(account_id,str):
        await log_user_error(ctx,account_id)
        return

    if save_files == '0':
        add_cheat_chain(ctx.author_id,cheat)
        await log_user_success(ctx,f'Added the cheat {cheat.pretty()} to your chain!')
        return
        
    try:
        save_dir_ftp = await get_save_str()
    except SaveMountPointResourceError:
        await log_user_error(ctx,'Theres too many people using the bot at the moment, please wait for a spot to free up')
        return
    try:
        my_token = await get_time_as_string_token()
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
            
            if save_files.isdigit():
                await log_message(ctx,'doing special built in save thing')
                await log_user_error(ctx,'unimplemented')
                return
            else:
                download_ps4_saves_result = await download_ps4_saves(ctx,save_files,enc_tp,account_id)
                if download_ps4_saves_result:
                    await log_user_error(ctx,download_ps4_saves_result)
                    return
                for bin_file, white_file in (done_ps4_saves := list(list_ps4_saves(enc_tp))):
                    await upload_encrypted_to_ps4(ctx,bin_file,white_file,enc_tp,save_dir_ftp)
                    pretty_folder_thing = white_file.relative_to(enc_tp).parts[0] + white_file.name
                    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'Getting ready to mount {pretty_folder_thing} (this may take a while if mutiple slots are in use)'))
                    async with mounted_saves_at_once:
                        tick_tock_task.cancel()
                        a: tuple[list[CheatFuncResult],PS4AccountID] = await apply_cheats_on_ps4(ctx,account_id,bin_file,white_file,enc_tp,my_cheats_chain,save_dir_ftp)
                    if isinstance(a,str):
                        await log_user_error(ctx,a)
                        return
                    results,old_account_id = a
                    await download_encrypted_from_ps4(ctx,bin_file,white_file,enc_tp,save_dir_ftp)
            
            await log_message(ctx,f'looking through results to do some renaming for {save_files}')
            for bin_file, white_file in done_ps4_saves:
                for savename, gameid in results:
                    if savename:
                        try:
                            white_file.rename(white_file.parent / savename)
                        except (FileNotFoundError, FileExistsError):
                            pass
                        
                        try:
                            bin_file.rename(bin_file.parent / (savename + '.bin'))
                        except (FileNotFoundError, FileExistsError):
                            pass

                    if gameid:
                        try:
                            white_file.parent.rename(white_file.parent.parent / gameid)
                        except FileNotFoundError:
                            pass
                if not account_id:
                    try:
                        white_file.parent.parent.rename(white_file.parent.parent.parent / old_account_id.account_id)
                    except (FileNotFoundError, FileExistsError):
                        pass
            if save_files.isdigit():
                await log_message(ctx,'cleaning up the things you did')
                await log_user_error(ctx,'unimplemented')
                return
                
            await send_result_as_zip(ctx,save_files,enc_tp,enc_tp,Path(tp,my_token + '.zip'),(cheat.func.__doc__ or 'paypal me some money eboot.bin@protonmail.com and i might fix this message').strip())
            return
    finally:
        await free_save_str(save_dir_ftp)
        delete_chain(ctx.author_id)


############################01 Custom decryptions
advanced_mode_export = interactions.SlashCommand(name="advanced_mode_export", description="Commands to do any extra decryptions or file management for certain saves")

@interactions.slash_command(name="decrypt",description=f"Decrypt your save files! (max {MAX_RESIGNS_PER_ONCE} save per command)")
@dec_enc_save_files
async def do_dec(ctx: interactions.SlashContext,save_files: str):
    await base_do_dec(ctx,save_files)

async def export_single_file_any_game(ftp: aioftp.Client, mount_dir: str, savename: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None):
    """
    Exported file
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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
any_game_export = advanced_mode_export.group(name="any_game", description="Export a decrypted save from any game, if it doesnt work, please ask to add your game")
@any_game_export.subcommand(sub_cmd_name="export", sub_cmd_description="Export a decrypted save from any game, if it doesnt work, please ask to add your game")
@dec_enc_save_files
@filename_p_opt
async def do_export_single_file_any_game(ctx: interactions.SlashContext,save_files: str,**kwargs):
    await base_do_dec(ctx,save_files,DecFunc(export_single_file_any_game,kwargs))


async def export_dl2_save(ftp: aioftp.Client, mount_dir: str, savename: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None):
    """
    Exported dl2 file
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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
            shutil.copyfileobj(f_in, f_out)
    os.replace(downloaded_ftp_save.with_suffix('.gz'),downloaded_ftp_save)
dying_light_2_export = advanced_mode_export.group(name='dying_light_2_export',description='Export .sav files')
@dying_light_2_export.subcommand(sub_cmd_name='dying_light_2_export_sav',sub_cmd_description="Export a .sav file (eg save_main_0.sav) from your save")
@dec_enc_save_files
@filename_p_opt
async def do_export_dl2_save(ctx: interactions.SlashContext,save_files: str,**kwargs):
    await base_do_dec(ctx,save_files,DecFunc(export_dl2_save,kwargs))

async def export_xenoverse_2_sdata000_dat_file(ftp: aioftp.Client, mount_dir: str, savename: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None,verify_checksum: bool = True):
    """
    Exported xenoverse 2 SDATAXXX.DAT file
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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
xenoverse_2_export = advanced_mode_export.group(name='xenoverse_2',description='Export Xenoverse 2 saves')
@xenoverse_2_export.subcommand(sub_cmd_name='xenoverse_2_export_sdata000_dat',sub_cmd_description='Export SDATAXXX.DAT files (eg SDATA000.DAT)')
@dec_enc_save_files
@filename_p_opt
@interactions.slash_option(name='verify_checksum',description='If set to true, then the command will fail if save has bad checksum (corrupted), default is True',required=False,opt_type=interactions.OptionType.BOOLEAN)
async def do_export_xenoverse_2_sdata000_dat_file(ctx: interactions.SlashContext,save_files: str,**kwargs):
    await base_do_dec(ctx,save_files,DecFunc(export_xenoverse_2_sdata000_dat_file,kwargs))


async def export_red_dead_redemption_2_or_gta_v_file(ftp: aioftp.Client, mount_dir: str, savename: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None):
    """
    Exported Red Dead Redemption 2 or Grand Theft Auto V savedata
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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
rdr_2_or_gta_v_export = advanced_mode_export.group(name='rdr_2_or_gta_v_export',description='Export Red Dead Redemption 2 or GTA V saves')
@rdr_2_or_gta_v_export.subcommand(sub_cmd_name='rdr_2_or_gta_v_export_savedata',sub_cmd_description='Export Red Dead Redemption 2 or GTA V saves')
@dec_enc_save_files
@filename_p_opt
#@interactions.slash_option(name='verify_checksum',description='If set to true, then the command will fail if save has bad checksum (corrupted), default is True',required=False,opt_type=interactions.OptionType.BOOLEAN)
async def do_export_red_dead_redemption_2_or_gta_v_file(ctx: interactions.SlashContext,save_files: str,**kwargs):
    await base_do_dec(ctx,save_files,DecFunc(export_red_dead_redemption_2_or_gta_v_file,kwargs))
# async def export_dl2_save(ftp: aioftp.Client, mount_dir: str, savename: str, decrypted_save_ouput: Path,/):
#     await ftp.change_directory(mount_dir)
#     files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path) and path.name != 'SETTINGS.dat']
#     print(f'{files = }')
#     try:
#         ftp_save, = files
#     except ValueError:
#         raise ValueError('Mutiple files found in save excluding SETTINGS.dat file, maybe a different save type?') from None
    
#     await ftp.download(ftp_save[0],decrypted_save_ouput)
# dying_light_2_export = advanced_mode_export.group(name='dying_light_2_export',description='Export .sav files')
# @dying_light_2_export.subcommand(sub_cmd_name='dying_light_2_export_sav',sub_cmd_description="Export a .sav file (eg save_main_0.sav) to your save")
# @dec_enc_save_files
# async def do_export_dl2_save(ctx: interactions.SlashContext,save_files: str):
#     await base_do_dec(ctx,save_files,DecFunc(export_dl2_save,{}))
############################02 Custom cheats
cheats_base_command = interactions.SlashCommand(name="cheats", description="Commands for custom cheats for some games")

async def _(ftp: aioftp.Client, mount_dir: str, save_name: str): """Resigned Saves"""
DUMMY_CHEAT_FUNC = CheatFunc(_,{})
@interactions.slash_command(name="resign", description=f"Resign save files to an account id (max {MAX_RESIGNS_PER_ONCE} saves per command)")
@interactions.slash_option('save_files','The save files to resign too',interactions.OptionType.STRING,True)
@account_id_opt
async def do_resign(ctx: interactions.SlashContext,save_files: str,account_id: str):
    await base_do_cheats(ctx,save_files,account_id,DUMMY_CHEAT_FUNC)


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
async def upload_savedata0_folder(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,decrypted_save_file: Path, clean_encrypted_file: bool = False):
    """
    Encrypted save
    """
    parent_mount, mount_last_name = Path(mount_dir).parent.as_posix(), Path(mount_dir).name
    await ftp.change_directory(parent_mount)

    if clean_encrypted_file:
        try:
            await ftp.remove(mount_last_name)
        except Exception:
            pass
        else:
            print('Yeah we should have gotten an error here')
            breakpoint()
            raise AssertionError('Yeah we should have gotten an error here')
    await ftp.change_directory(parent_mount)
    await ftp.upload(decrypted_save_file / 'savedata0',mount_last_name,write_into=True)
@interactions.slash_command(name="encrypt", description=f"Encrypt a save (max 1 save per command) only jb ps4 decrypted save")
@interactions.slash_option('save_files','The save file orginally decrypted',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('decrypted_save_file','A link to a folder or zip of your decrypted savedata0 folder',interactions.OptionType.STRING,True)
@interactions.slash_option('clean_encrypted_file','If True, deletes all in encrypted file; only use when decrypted folder has all files. Default: False',interactions.OptionType.BOOLEAN,False)
async def do_encrypt(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_savedata0_folder,kwargs))


async def re_region(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,gameid: str) -> CheatFuncResult:
    """
    re regioned save
    """
    is_xenoverse = gameid in XENOVERSE_TITLE_IDS
   
    if is_xenoverse:
        seeks = (0x61C,0xA9C,0x9F8)
    else:
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
    if is_xenoverse:
        savename = gameid + save_name[9:]
    else:
        savename = None
        for x in found_titleids:
            x -= 0x9F8
            savename = save_name.replace(save_name[x:x+9],gameid)
            save_name = savename
    return CheatFuncResult(savename,gameid)
@interactions.slash_command(name="re_region", description=f"Re region your save files! (max {MAX_RESIGNS_PER_ONCE} saves per command)")
@interactions.slash_option('save_files','The save files to be re regioned',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('gameid','The gameid of the region you want, in format CUSAXXXXX',interactions.OptionType.STRING,True,max_length=9,min_length=9)
async def do_re_region(ctx: interactions.SlashContext,save_files: str,account_id: str, gameid: str):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(re_region,{'gameid':gameid.upper()}))

async def change_save_icon(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_image_overlay: Path, option: ChangeSaveIconOption):
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
            
            with Image.open(og_icon0_path) as im:
                im.paste(icon_overlay,(0,0),icon_overlay)
                im.save(og_icon0_path)
        await ftp.upload(og_icon0_path,'icon0.png',write_into=True)
@interactions.slash_command(name="change_icon",description=f"Add an icon overlay to your saves!")
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

async def change_save_name(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,psstring_new_name: bytes) -> CheatFuncResult:
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


@interactions.slash_command(name="change_save_name", description=f"Change the name of the save displayed on PS4 menu")
@interactions.slash_option('save_files','The save files to change the name of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('psstring_new_name','the name you want, put hex code for symbols (eg this is a checkmark -> EFA1BE)',interactions.OptionType.STRING,True,min_length=1,max_length=0x80*3)
async def do_change_save_name(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(change_save_name,kwargs))


async def change_save_desc(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,psstring_new_desc: bytes) -> CheatFuncResult:
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


@interactions.slash_command(name="change_save_desc", description=f"Change the description of the save displayed on PS4 menu")
@interactions.slash_option('save_files','The save files to change the description of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('psstring_new_desc','the description you want, put hex code for symbols (eg this is a TV -> EFA1B1)',interactions.OptionType.STRING,True,min_length=1,max_length=0x79*6)
async def do_change_save_desc(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(change_save_desc,kwargs))
############################03 Custom imports
advanced_mode_import = interactions.SlashCommand(name="advanced_mode_import", description="Commands to import singular files, usually from savewizard")

async def upload_single_file_any_game(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_single: Path, filename_p: str | None = None):
    """
    Encrypted save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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
any_game_import = advanced_mode_import.group(name="any_game", description="Import a decrypted save from any game, if it doesnt work, please ask to add your game")
@any_game_import.subcommand(sub_cmd_name="import", sub_cmd_description="Import a decrypted save from any game, if it doesnt work, please ask to add your game")
@interactions.slash_option('save_files','The save file to import the decrypted save to',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_single','The file link you wanna import YOU SHOULD GET THIS FROM SAVEWIZARD OR advanced_mode_export',interactions.OptionType.STRING,True)
@filename_p_opt
async def do_upload_single_file_any_game(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_single_file_any_game,kwargs))


async def upload_dl2_sav_gz_decompressed(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_sav_decompressed: Path, filename_p: str | None = None):
    """
    Encrypted save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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
    
    with open(dl_link_sav_decompressed, 'rb') as f_in:
        with gzip.open(dl_link_sav_decompressed.with_suffix('.gz'), 'wb') as f_out: # its not a gz file but i dont care i just want it to work
            shutil.copyfileobj(f_in, f_out)
    os.replace(dl_link_sav_decompressed.with_suffix('.gz'),dl_link_sav_decompressed)
    
    await ftp.upload(dl_link_sav_decompressed,ftp_save[0],write_into=True)
dying_light_2_import = advanced_mode_import.group(name="dying_light_2_import", description="Import .sav files")
@dying_light_2_import.subcommand(sub_cmd_name="dying_light_2_import_sav", sub_cmd_description="Import a .sav file (eg save_main_0.sav) to your save")
@interactions.slash_option('save_files','The save file to import the .sav file to',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_sav_decompressed','the .sav file you want, eg a save_main_0.sav file',interactions.OptionType.STRING,True)
@filename_p_opt
async def do_upload_dl2_save(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_dl2_sav_gz_decompressed,kwargs))

async def upload_xenoverse_2_save(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_sdata000_dat_dec: Path, filename_p: str | None = None):
    """
    Xenoverse 2 encrypted save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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

    with open(dl_link_sdata000_dat_dec,'rb') as f, open(dl_link_sdata000_dat_dec.with_suffix('.enc'),'wb') as f_out:
        encrypt_xenoverse2_ps4(f,f_out)
    await ftp.upload(dl_link_sdata000_dat_dec.with_suffix('.enc'),ftp_save[0],write_into=True)
xenoverse_2_import = advanced_mode_import.group(name="xenoverse_2_import", description="Import decrypted xeno files")
@xenoverse_2_import.subcommand(sub_cmd_name="xenoverse_2_import_sdata000_dat", sub_cmd_description="Import a SDATAXXX.DAT decrypted file (eg SDATA000.DAT.dec) to your save")
@interactions.slash_option('save_files','The save file to import the SDATAXXX.DAT file to',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_sdata000_dat_dec','the SDATAXXX.DAT file you want, eg a SDATA000.DAT.dec file, should be extra decrypted',interactions.OptionType.STRING,True)
@filename_p_opt
async def do_upload_xenoverse_2_save(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_xenoverse_2_save,kwargs))

async def upload_red_dead_redemption_2_or_gta_v_save(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_savedata: Path, filename_p: str | None = None):
    """
    Red Dead Redemption 2 or Grand Theft Auto V encrypted save
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
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

    with open(dl_link_savedata,'rb+') as f:
        encrypted_rdr2_data = auto_encrypt_decrypt(f)
    
    with open(dl_link_savedata,'wb') as f:
        f.write(encrypted_rdr2_data)
    
    await ftp.upload(dl_link_savedata,ftp_save[0],write_into=True)
rdr_2_or_gta_v_import = advanced_mode_import.group(name="rdr_2_or_gta_v_import", description="Import decrypted Red Dead Redemption 2 or GTA V saves")
@rdr_2_or_gta_v_import.subcommand(sub_cmd_name="rdr_2_or_gta_v_import_savedata", sub_cmd_description="Import a exported save file from Red Dead Redemption 2 or GTA V")
@interactions.slash_option('save_files','The save file to import the savedata file to',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_savedata','the savedata you want, eg a memory.dat file, should be extra decrypted',interactions.OptionType.STRING,True)
@filename_p_opt
async def do_upload_red_dead_redemption_2_or_gta_v_save(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_red_dead_redemption_2_or_gta_v_save,kwargs))
# async def upload_dl2_save(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_dot_sav_file: Path):
#     """
#     Encrypted Dying Light 2 save
#     """
#     await ftp.change_directory(mount_dir)
#     files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path) and path.name != 'SETTINGS.dat']
#     try:
#         ftp_save, = files
#     except ValueError:
#         raise ValueError('Mutiple files found in save excluding SETTINGS.dat file, maybe a different save type?') from None
    
#     await ftp.upload(dl_link_dot_sav_file,ftp_save[0],write_into=True)
# dying_light_2_import = advanced_mode_import.group(name="dying_light_2_import", description="Import .sav files")
# @dying_light_2_import.subcommand(sub_cmd_name="dying_light_2_import_sav", sub_cmd_description="Import a .sav file (eg save_main_0.sav) to your save")
# @interactions.slash_option('save_files','The save file to import the .sav file to',interactions.OptionType.STRING,True)
# @account_id_opt
# @interactions.slash_option('dl_link_dot_sav_file','the .sav file you want, eg a save_main_0.sav file',interactions.OptionType.STRING,True)
# async def do_upload_dl2_save(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
#     await base_do_cheats(ctx,save_files,account_id,CheatFunc(upload_dl2_save,kwargs))

async def import_bigfart(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,dl_link_bigfart: Path):
    """
    Encrypted bigfart
    """
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and 'sce_sys' not in str(path)]
    try:
        ftp_save, = files
    except ValueError:
        raise ValueError('Too many files in the save, likley not a lbp3 big save, did you upload the 500mb+ one?') from None

    if not ftp_save[0].name.startswith('bigfart'):
        raise ValueError(f'Invalid bigfart {ftp_save[0].name}, not a lbp3 big save, did you upload the 500mb+ one?')

    with open(dl_link_bigfart,'rb+') as f:
        savkey = f4.SaveKey(f)
        savkey.is_ps4_endian = True
        savkey.write_to_far4(f)
    
    await ftp.upload(dl_link_bigfart,ftp_save[0],write_into=True)
littlebigplanet3_import = advanced_mode_import.group(name="littlebigplanet3", description="decrypted save files for lbp3")
@littlebigplanet3_import.subcommand(sub_cmd_name="bigfart_import", sub_cmd_description="Import a bigfart to your lbp3 big save, can be a bigfart from any game besides vita!")
@interactions.slash_option('save_files','The save file to import the bigfart to',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('dl_link_bigfart','The bigfart you want',interactions.OptionType.STRING,True)
async def do_import_bigfart(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(import_bigfart,kwargs))
############################04 Cool bot features
@interactions.listen()
async def ready():
    await update_status()
    _update_status.start()
    await ps4.notify('eZwizard3-bot connected!')
    print('eZwizard3-bot connected!')

update_status_start = time.perf_counter()
amnt_used_this_session = 0
old_amnt_of_free = 0
@interactions.Task.create(interactions.IntervalTrigger(seconds=30))
async def _update_status():
    await update_status()
async def update_status():
    global old_amnt_of_free
    global update_status_start
    amnt_of_free = await get_amnt_free_save_strs()

    if amnt_of_free != old_amnt_of_free:
        update_status_start = time.perf_counter()
    new_time = pretty_time(time.perf_counter() - update_status_start)

    if not amnt_of_free:
        status = interactions.Status.DO_NOT_DISTURB
        msg = f'NO slots free {amnt_of_free}/{len(SAVE_DIRS)} for {new_time}, used {amnt_used_this_session} times this session, {get_total_amnt_used()} total'
    elif amnt_of_free == len(SAVE_DIRS):
        status = interactions.Status.IDLE
        msg = f'All slots free {amnt_of_free}/{len(SAVE_DIRS)} for {new_time} used {amnt_used_this_session} times this session, {get_total_amnt_used()} total'
    else:
        status = interactions.Status.ONLINE
        msg = f'Some slots free {amnt_of_free}/{len(SAVE_DIRS)} for {new_time} used {amnt_used_this_session} times this session, {get_total_amnt_used()} total'
    await bot.change_presence(activity=interactions.Activity.create(
                                name=msg),
                                status=status)

    old_amnt_of_free = amnt_of_free

psnawp = PSNAWP(CONFIG["ssocookie"])
@interactions.slash_command(name="my_account_id",description="Get your Account ID from your psn name")
@interactions.slash_option(
    name="psn_name",
    description='your psn name',
    required=True,
    opt_type=interactions.OptionType.STRING,
    max_length=16,
    min_length=3
    )
async def my_account_id(ctx: interactions.SlashContext,psn_name: str):
    ctx = await set_up_ctx(ctx)
    
    await log_message(ctx,f'Looking for psn name {psn_name}')
    try:
        user = psnawp.user(online_id=psn_name)
    except PSNAWPNotFound as e:
        await log_user_error(ctx,f'Invalid psn name {psn_name}')
        return
    account_id_hex = f'{int(user.account_id):016x}'
    
    start_msg = 'your account id for {0} is {1}, saved to database, put 0 in the account_id option to use this account id!'
    my_database_account_id: str = ''
    try:
        my_database_account_id = get_user_account_id(ctx.author_id)
    except KeyError:
        pass
    
    if my_database_account_id != account_id_hex:
        add_user_account_id(ctx.author_id,account_id_hex)
    else:
        start_msg = '**We\'ve already saved your account id for {0}**, it\'s {1}, put 0 in the account_id option to use this account id!'
    await log_user_success(ctx,start_msg.format(user.online_id,account_id_hex))


@interactions.slash_command(name="delete_cheat_chain",description="Deletes your cheat chain")
async def delete_cheat_chain(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    
    
    delete_chain(ctx.author_id)
    await log_user_success(ctx,'Removed all the cheats from your cheat chain!')


@interactions.slash_command(name="see_cheat_chain",description="See the cheats currently your cheat chain!")
async def see_cheat_chain(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    
    
    chets = ''.join(chet.pretty() for chet in get_cheat_chain(ctx.author_id))
    await log_user_success(ctx,f'Cheats in your chain are currently...{chets}')


@interactions.slash_command(name="ping",description="Test if the bot is responding")
async def ping_test(ctx: interactions.SlashContext):
    global bot
    await ps4_life_check(ctx)
    cool_ping_msg = f'<@{ctx.author_id}> Pong! bot latency is {ctx.bot.latency * 1000:.2f}ms'
    
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_DMS}'
    
    await ctx.send(cool_ping_msg,ephemeral=False)


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
    required=True,
    opt_type=interactions.OptionType.INTEGER,
    min_value=2
    )
async def file2url(ctx: interactions.SlashContext, my_file: interactions.Attachment, my_file_id: int):
    ctx = await set_up_ctx(ctx)
    await log_message(ctx,'Getting url')
    save_url(ctx.author_id,my_file.url,my_file_id)
    await log_user_success(ctx,f'the url is {my_file.url}, or use {my_file_id} in a field that needs a url, like save_files or dl_link')

@interactions.slash_command(name='delete_files2urls',description="Delete all your saved urls!")
async def delete_files2urls(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    delete_saved_urls(ctx.author_id)
    await log_user_success(ctx,'Deleted all urls saved succesfully!')

@interactions.slash_command(name='see_saved_files2urls',description="See all your saved urls with the file2url command")
async def see_saved_files2urls(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    a = get_all_saved_urls(ctx.author_id)
    pretty = ''
    for key,value in a.items():
        pretty += f'{key} -> {value}\n'
    await log_user_success(ctx,f'Your saved urls are... \n{pretty.strip()}')

async def main() -> int:
    global ps4
    global UPLOAD_SAVES_FOLDER_ID
    await send_ps4debug(CONFIG['ps4_ip'],port=9090)
    ps4 = PS4Debug(CONFIG['ps4_ip'])


    UPLOAD_SAVES_FOLDER_ID = await make_gdrive_folder('ezwizardtwo_saves')

    initialise_database()
    
    global mem
    global bot
    async with PatchMemoryPS4900(ps4) as mem:
        print('Memory patched, ensuring all base saves exist!')
        for eeeee in SAVE_DIRS:
            async with MountSave(ps4,mem,int(CONFIG['user_id'],16),'YAHY40786',eeeee) as mp:
                pass
        print('done checking!')
        bot = interactions.Client(token=CONFIG['discord_token'])
        await bot.astart()
    return 0 

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
