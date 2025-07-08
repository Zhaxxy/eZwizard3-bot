import dataclasses
import asyncio
from contextlib import nullcontext
import sys
import re
from typing import NamedTuple, Callable, Generator, Any, Sequence, Coroutine, NoReturn, assert_never, BinaryIO
from enum import Enum
from pathlib import Path
from traceback import format_exc
from io import BytesIO
import time
import zipfile
import os
import math
from stat import S_IWRITE
import datetime
from zlib import crc32 # put modules you need at the bottom of list for custom cheats, in correct block
import struct
import gzip
from sqlite3 import connect as sqlite3_connect
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
from lbptoolspy.binary_files import LBP3_PS4_L0_FILE_TEMPLATE

from string_helpers import INT64_MAX_MIN_VALUES, UINT64_MAX_MIN_VALUES, INT32_MAX_MIN_VALUES, UINT32_MAX_MIN_VALUES, INT16_MAX_MIN_VALUES, UINT16_MAX_MIN_VALUES, INT8_MAX_MIN_VALUES, UINT8_MAX_MIN_VALUES, extract_drive_folder_id, extract_drive_file_id, is_ps4_title_id, make_folder_name_safe, reset_make_folder_name_counter, pretty_time, load_config, CUSA_TITLE_ID, chunker, is_str_int, get_a_stupid_silly_random_string_not_unique, is_psn_name, PARENT_TEMP_DIR, pretty_bytes, pretty_seconds_words, non_format_susceptible_byte_repr, hex_dump
from archive_helpers import get_archive_info, extract_single_file, filename_valid_extension,SevenZipFile,SevenZipInfo, extract_full_archive, filename_is_not_an_archive
from gdrive_helpers import get_gdrive_folder_size, list_files_in_gdrive_folder, gdrive_folder_link_to_name, get_valid_saves_out_names_only, download_file, get_file_info_from_id, GDriveFile, download_folder, google_drive_upload_file, make_gdrive_folder, get_folder_info_from_id, delete_google_drive_file_or_file_permentaly
from savemount_py import PatchMemoryPS4900,MountSave,ERROR_CODE_LONG_NAMES,unmount_save,send_ps4debug,SUPPORTED_MEM_PATCH_FW_VERSIONS
from savemount_py.firmware_getter_from_libc_ps4 import get_fw_version
from git_helpers import check_if_git_exists,run_git_command,get_git_url,is_modfied,is_updated,get_remote_count,get_commit_count
from custom_crc import custom_crc
from dry_db_stuff import ps3_level_backup_to_l0_ps4
from bot_admin_helpers import is_in_test_mode, is_in_fast_boot_mode, toggle_test_mode_bool
from title_id_lookup_commands import dm_all_at_once
try:
    from custom_cheats.xenoverse2_ps4_decrypt.xenoverse2_ps4_decrypt import decrypt_xenoverse2_ps4, encrypt_xenoverse2_ps4
    from custom_cheats.rdr2_enc_dec.rdr2_enc_dec import auto_encrypt_decrypt
except ModuleNotFoundError as e:
    msg = f'{e}, maybe you need to add the --recurse-submodules to the git clone command `git clone https://github.com/Zhaxxy/eZwizard3-bot.git --recurse-submodules` (or you can do `git submodule update --init --recursive` if you dont want to clone again)'
    raise ModuleNotFoundError(msg) from e

try:
    __file__ = sys._MEIPASS
except Exception:
    pass
else:
    __file__ = str(Path(__file__) / 'huh.huh')

CANT_USE_BOT_IN_DMS = 'Sorry, but the owner of this instance has disabled commands in dms'
CANT_USE_BOT_IN_TEST_MODE = 'Sorry, but the bot is currently in test mode, only bot admins can use the bot atm'
WARNING_COULD_NOT_UNMOUNT_MSG = 'WARNING WARNING SAVE DIDNT UNMOUNT, MANUAL ASSITENCE IS NEEDED!!!!!!!!'

LBP3_EU_BIGFART = 'https://drive.google.com/drive/folders/1fmUMCZlvj5011njMi6Xl-uP8WvIfRyuN?usp=sharing'
LBP3_EU_LEVEL_BACKUP = 'https://drive.google.com/drive/folders/1wCBA0sZumgBRr3cDJm5BADRA9mfq4NpR?usp=sharing'

FILE_SIZE_TOTAL_LIMIT = 1_473_741_920
DL_FILE_TOTAL_LIMIT = 50_000_000 # 50mb
DISCORD_CHOICE_LIMIT = 25
ATTACHMENT_MAX_FILE_SIZE = 10_000_000-1 # 10mb, the actual limit is 10mib but this includes metadata which is hard to calculate, so im hoping this will give it enough slack for metadata
DISCORD_BOT_STATUS_MAX_LENGTH = 128 - len('...')
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
    'CUSA05350': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb5\xaa\xa6\xdd\x19*\xfd\xdd\x8dy\x93\x8eJ\xce\x13\x7f\xd4H\x1d\xf1\x11\xbd\x18\x8a\xf3\x02\xc5l6j\x91\x12K\xcbZe\x06tj\x9d\x08\xd53;\xc1\x9cD\x96h\xff\xef\xe2\x18$W\x96\x8fQ\xa1\xc8<\x0b\x18\x96',
    'CUSA05088': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00&\xedp\x94\xb2\x94\xa3\x9bc\xbd\x94\x11;\x06l\x93x\x9d\xc2K\xe2\xed\xfc\xd78\xff\xdd\x8dU\x86\xab\xd8N\x1dx8q\xcf\xd3\x0b\xfc\x8cr<il\xbbd\xbd\x17\xbe(?\x85Xn\xa5\xf4T\xe8s\xdcu\xaa',
    'CUSA08767': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0fmj\x91\x05\x0e\xa7"\x9e3I\x94\x12].2\xe1\xbd\xff\x86\xac9\x0b{\xf0\x13\\\xa8\x83\x04o\xf0\x9c\xda\x9e64\x07H\x90o\xeb\xed\x86\xdc\x9aA$x\xe3\xbfZe\xb0\x9d\t\x92\xfa\xa4\xe8x\xb6\x1d\x8a',
    'CUSA12555': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\xc3\xc4\xea\x6a\x09\x09\x5f\x03\x6c\x2b\xcc\x61\x3b\x3f\x99\x6a\x35\xff\xbd\xb8\xf3\x59\x35\xbf\x86\x27\x92\x18\x53\x9b\xbe\x73\x52\xda\x5f\x95\x13\x53\x73\x16\xf2\x2c\x9b\xe5\xeb\x02\x58\x75\x4e\x5e\x02\x30\x9c\x38\xad\x58\x57\xc1\x25\xc9\xf9\xa1\x49',
    'CUSA00419': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc06\x2c\x14\x08\x7b\xb0Zv\x8a\x5e\x9e\xcf\x89\xd3\xdf\x94\xcb\x23u\xe1\xd0\xae\xab\x105i\x229\x93\x97\x1d\x84\x8b\xd3\xb8\x20\x8bg\xa0\xc3\xcb\xfd\xa7S\xdf7\xa22\x7d\x17F\x3b\xe7\xb4\xc9\x88\x8a\x06Z\x11\xa52K',
    'CUSA00411': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x22\x81\xd0\xe5WwZ\xe2u\xbcn\x2a\xd6\x14\xc8\x8b\xf2\xd6\xc9\xf0\xcd\xbe\x11\x20c\xc9\x88Bh\x02\xa9\xc8y\x3f\x94r\xc9\x29\xdeA\xe4m\xd0\x5c\x07\x1d\x0a\x97\xd7\x9f\xc7\xc2\x95L\xb6\x5e\xaf\xa1N\xaf\x10Q\x97B',
    'CUSA08966': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd9aT\x7b\x1fq\x80\x7b\xdah\xa5Q\xf4\x29\x2e\xd6\xc7\x8ar\xcf\xfd\xa7\xaaB\x8e\xc0cI\xc1\x94\xbcO\x85\xa6\xf4\x1f\x040\x2c\xaf\x02\xc2\xa3\x0b\x1by\x27\xf8\x86V\x0c\xdb\x2c\x3d\xfa\xdb\x1f\x01\xe4W\x9f\x01\x2e\xbe',
    'CUSA09175': b'keystone\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd9aT\x7b\x1fq\x80\x7b\xdah\xa5Q\xf4\x29\x2e\xd6\xc7\x8ar\xcf\xfd\xa7\xaaB\x8e\xc0cI\xc1\x94\xbcO\x85\xa6\xf4\x1f\x040\x2c\xaf\x02\xc2\xa3\x0b\x1by\x27\xf8\x86V\x0c\xdb\x2c\x3d\xfa\xdb\x1f\x01\xe4W\x9f\x01\x2e\xbe',
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

PARAM_SFO_SPECIAL_STRINGS_AS_BYTES = frozenset(bytes.fromhex(x) for x in PARAM_SFO_SPECIAL_STRINGS)

HUH = "Connection terminated. I'm sorry to interrupt you Elizabeth, if you still even remember that name. But I'm afraid you've been misinformed. You are not here to receive a gift, nor have you been called here by the individual you assume. Although you have indeed been called. You have all been called here. Into a labyrinth of sounds and smells, misdirection and misfortune. A labyrinth with no exit, a maze with no prize. You don't even realize that you are trapped. Your lust for blood has driven you in endless circles, chasing the cries of children in some unseen chamber, always seeming so near, yet somehow out of reach. But you will never find them, none of you will. This is where your story ends. And to you, my brave volunter, who somehow found this job listing not intended for you. Although there was a way out planned for you, I have a feeling that's not what you want. I have a feeling that you are right where you want to be. I am remaining as well, I am nearby. This place will not be remembered, and the memory of everything that started this can finally begin to fade away. As the agony of every tragedy should. And to you monsters trapped in the corridors: Be still and give up your spirits, they don't belong to you. For most of you, I believe there is peace and perhaps more waiting for you after the smoke clears. Although, for one of you, the darkest pit of Hell has opened to swallow you whole, so don't keep the devil waiting, old friend. My daughter, if you can hear me, I knew you would return as well. It's in your nature to protect the innocent. I'm sorry that on that day, the day you were shut out and left to die, no one was there to lift you up into their arms the way you lifted others into yours. And then, what became of you. I should have known you wouldn't be content to disappear, not my daughter. I couldn't save you then, so let me save you now. It's time to rest. For you, and for those you have carried in your arms. This ends for all of us. End communication."


class ExpectedError(Exception):
    """
    Raise this error if you just wanna print some information about a save as a cheat
    """

class HasExpectedError(NamedTuple):
    error_text: str
    pretty_dir: Path

class InvalidBinFile(Exception):
    pass

# class TemporaryDirectory():
#     def __enter__(self):
#         self.new_path = Path(str(time.perf_counter()).replace('.','_'))
#         self.new_path.mkdir()
#         self.new_path = self.new_path.resolve()
#         return self.new_path

#     def __exit__(self, exc_type=None, exc_value=None, traceback=None):
#         await shutil.rmtree(self.new_path)


class PS4AccountID:
    __slots__ = ('_account_id',)
    def __init__(self, account_id: str):
        account_id = account_id.split(' ')[0]
        if len(account_id) != 16:
            raise ValueError('Invalid account id, length is not 16')
        int(account_id,16)
        account_id = account_id.casefold()
        
        # TODO make this be a bool option in the init function, make it default always check this but have it False in places where it needs to be (eg when mounting the save first time to check param.sfo)
        # if account_id[0] in 'abcdef':
            # raise ValueError('Invalid account id, does not start with a number')
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
    def from_bytes(cls,account_id_bytes: bytes) -> 'PS4AccountID':
        return cls(account_id_bytes[::-1].hex())

    @classmethod
    def from_account_id_number(cls, account_id_int: str | int) -> 'PS4AccountID':
        return cls(f'{int(account_id_int):016x}')


PARAM_SFO_REGION_SEEKS = (0xA9C,0x61C,0x62C)

@dataclasses.dataclass(slots = True)
class PS4SaveParamSfo:
    dir_name: str
    title_id: str
    menu_name: bytes
    menu_description: bytes
    account_id: PS4AccountID
    blocks_count: int
    
    _param_sfo_data: bytes
    miss_matching_title_ids: Sequence[tuple[str,int]] | None
    
    def check_if_account_id_is_banned(self) -> None | str:
        if user := is_account_id_in_ban_list(self.account_id):
            return f'Hey!, this account id {self.account_id.account_id} is banned, what are you trying to do <@{user}>??'
    
    def __bytes__(self) -> bytes:
        return self._param_sfo_data
    
    def __str__(self) -> str:
        info_message = f'Save file name: {self.dir_name}'
        shrug_emoji = '🤷'.encode('utf-8') # TODO make custom emojis for each save special character
        if self.miss_matching_title_ids:
            info_message += '\nMissmatching title ids in save, is a bad save'
            for title_id,seek in self.miss_matching_title_ids:
                info_message += f'\nTitle id at 0x{seek:X}: {title_id}'
        else:
            info_message += f'\nTitle id: {self.title_id}'
        
        save_description = self.menu_name
        for x in PARAM_SFO_SPECIAL_STRINGS_AS_BYTES:
            save_description = save_description.replace(x,shrug_emoji)
        info_message += f'\nName: {save_description.decode("utf-8")}'
        
        if self.menu_description:
            save_description = self.menu_description
            for x in PARAM_SFO_SPECIAL_STRINGS_AS_BYTES:
                save_description = save_description.replace(x,shrug_emoji)
            info_message += f'\nDescription: {save_description.decode("utf-8")}'
        
        info_message += f'\nOld Account ID: {self.account_id.account_id}'
        
        info_message += f'\nMax Decrypted Save Size: {pretty_bytes(self.blocks_count_in_bytes)} ({self.blocks_count} Blocks) (The real limit will always be smaller then this, dont get close to it!)'
        
        return info_message
    
    def __repr__(self) -> str:
        return str(self)
    
    @classmethod
    def from_buffer(cls,f: BinaryIO,/) -> 'PS4SaveParamSfo':
        f.seek(0,2)
        if f.tell() > 5_000_000:
            raise ValueError('param.sfo is too big')
        f.seek(0)
        data = f.read() # for indexing
        
        found_game_ids = []
        for seek in PARAM_SFO_REGION_SEEKS:
            f.seek(seek)
            found_game_ids.append((f.read(9).decode('ascii'),seek))
        title_id = found_game_ids[0][0]
        miss_matching_title_ids: Sequence[tuple[str,int]] | None = None
        if not all(x[0] == found_game_ids[0][0] for x in found_game_ids):
            miss_matching_title_ids = tuple(found_game_ids)
        
        obs_index = data.index(b'obs\x00')
        f.seek(obs_index + len(b'obs\x00'))
        if f.read(1) == b'\x00':
            raise ValueError('found a null byte, no existing save name?')
        f.seek(-1, 1)
        
        menu_name = f.read(0x80).rstrip(b'\x00')
        
        menu_name_checker = menu_name
        menu_name_checker.decode('utf-8') # using as an error check
        
        
        f.seek(0x9F8)
        dir_name = b''.join(iter(lambda: f.read(1),b'\x00')).decode('ascii')
        
        if len(dir_name) >= 0x20:
            raise ValueError(f'{dir_name = } is too big, so invalid param.sfo')
        
        f.seek(0x9F8 + 0x24)
        save_description = f.read(0x80).rstrip(b'\x00')
        if save_description:
            save_description_checker = save_description
            save_description_checker.decode("utf-8") # using as an error check
        f.seek(0x15c)
        account_id = PS4AccountID.from_bytes(f.read(8))
        f.seek(0x9F8 - 8)
        blocks_count, = struct.unpack('<q',f.read(8))
        
        return cls(dir_name,title_id,menu_name,save_description,account_id,blocks_count,data,miss_matching_title_ids)
    
    @staticmethod
    def _is_valid_ps_title_id(title_id: str) -> bool:
        """
        Checks if the title_id is capable of being mounted
        """
        return len(title_id) == 9 and all(x in '0123456789' for x in title_id[-5:])
    
    @staticmethod
    def blocks_count_to_bytes(blocks_count: int) -> int:
        return blocks_count*32768
    
    @staticmethod
    def bytes_to_blocks_count(bytes_count: int) -> int:
        return math.ceil(bytes_count/32768)
        
    @property
    def blocks_count_in_bytes(self) -> int:
        return self.blocks_count*32768
    
    def with_new_account_id(self, new_account_id: PS4AccountID) -> None:
        data = BytesIO(self._param_sfo_data)
        
        data.seek(0x15c)
        if new_account_id: # you're welcome @b.a.t.a.n.g (569531198490279957)
            data.write(bytes(new_account_id))
        self._param_sfo_data = data.getvalue()
        
    def with_new_region(self, title_id: str, seeks: Sequence[int] = PARAM_SFO_REGION_SEEKS) -> None:
        if not self._is_valid_ps_title_id(title_id):
            raise ValueError(f'Invalid title id {title_id}')
        data = BytesIO(self._param_sfo_data)
        
        for seek in seeks:
            data.seek(seek)
            data.write(title_id.encode('ascii'))
        self._param_sfo_data = data.getvalue()
    
    def _with_new_special_ps_string(self, new_string: bytes,offset: int, max_length: int = 0x80) -> None:
        f = BytesIO(self._param_sfo_data)
        
        if new_string: # TODO check if you can change description even if none exist
            new_string.decode("utf-8") # using as an error check
            if len(new_string) >= max_length:
                new_string = new_string[:max_length-1]
            
                while True:
                    try:
                        new_string.decode("utf-8")
                    except Exception:
                        new_string = new_string[:-1]
                        continue
                    break

        f.seek(offset)
        f.write(new_string.ljust(max_length,b'\x00'))
        self._param_sfo_data = f.getvalue()
        
    def with_new_description(self, menu_description: bytes) -> None:
        self._with_new_special_ps_string(menu_description,0x9F8 + 0x24)

    def with_new_name(self, menu_name: bytes) -> None:
        new_offset = self._param_sfo_data.index(b'obs\x00') + len(b'obs\x00')
        if not menu_name:
            raise ValueError('You need to provided a save ps4 menu name')
        self._with_new_special_ps_string(menu_name,new_offset)

    def with_new_dir_name(self, dir_name: str) -> None:
        if len(dir_name) >= 0x20:
            raise ValueError(f'Save dir name {dir_name} is too big, max is 0x1F characters')
        data = BytesIO(self._param_sfo_data)
        
        data.seek(0x9F8)
        data.write(dir_name.encode('ascii').ljust(0x20,b'\x00'))
        self._param_sfo_data = data.getvalue()

    def with_new_blocks_count(self, blocks_count: int) -> None:
        if blocks_count > 32768:
            raise ValueError(f'Blocks count {blocks_count} is too big, perhaps you passed in a bytes count and did not convert it?')
        if blocks_count < 96:
            raise ValueError(f'Blocks count {blocks_count} is too small, (smallest is 96 blocks or 3mib)')
        data = BytesIO(self._param_sfo_data)
        
        data.seek(0x9F8 - 8)
        data.write(struct.pack('<Q',blocks_count))
        self._param_sfo_data = data.getvalue()


def is_user_bot_admin(ctx_author_id: str,/) -> bool:
    return ctx_author_id in CONFIG['bot_admins']


_token_getter = asyncio.Lock()
async def get_time_as_string_token() -> str:
    async with _token_getter:
        return datetime.datetime.now(datetime.UTC).strftime("%d_%m_%Y__%H_%M_%S")


def delete_empty_folders(root: Path):
    """
    https://stackoverflow.com/questions/47093561/remove-empty-folders-python
    """
    deleted = set()
    
    for current_dir, subdirs, files in os.walk(root, topdown=False):

        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
                break
    
        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)

class SetUpCtxFailedError(Exception):
    """
    Raise this, if `set_up_ctx` failed for some reason
    """

async def set_up_ctx(ctx: interactions.SlashContext,*,mode = 0) -> interactions.SlashContext:
    """
    mode 1 is test mode
    """
    if res := is_user_id_in_ban_list(ctx.author_id):
        new_msg = f'You have been banned from using this bot, reason:\n\n{res}'
        if is_user_bot_admin(ctx.author_id):
            ctx.ezwizard3_special_ctx_attr_noticemsg_banned_but_is_admin = new_msg
        else:
            await ctx.send(new_msg)
            raise SetUpCtxFailedError(new_msg)
            #await asyncio.sleep(10)
            #assert_never(None)
        
    nth_time = 1
    try:
        ctx.ezwizard3_special_ctx_attr_setup_done += 1
        nth_time = ctx.ezwizard3_special_ctx_attr_setup_done
    except AttributeError:
        if mode != 1:
            await ctx.defer()
    # t = await ctx.respond(content=get_a_stupid_silly_random_string_not_unique())
    # await ctx.delete(t)
    try:
        ctx.ezwizard3_special_ctx_attr_mode
    except AttributeError:
        ctx.ezwizard3_special_ctx_attr_mode = mode
    if ctx.ezwizard3_special_ctx_attr_mode == 1:
        ctx.author_id
        ctx.channel = True
        ctx.ezwizard3_special_ctx_attr_testing_log_message
        ctx.ezwizard3_special_ctx_attr_testing_log_message_tick_tock
        ctx.ezwizard3_special_ctx_attr_testing_log_user_error
        ctx.ezwizard3_special_ctx_attr_testing_log_user_success
        
        
        
        
    await log_message(ctx,f'Pleast wait, if over a minute is spent here do the command again! {nth_time}th time here',_do_print = False)
    ctx.ezwizard3_special_ctx_attr_setup_done = 1
    return ctx


async def pretty_pingers_do(ctx: interactions.SlashContext,pingers: None | Sequence[int],do_channel_send: bool,_do_print: bool) -> str:
    if pingers:
        pretty_pingers = ' '.join(f'<@{id}>' for id in pingers)
        if _do_print:
            print(pretty_pingers)
        if do_channel_send:
            channel = ctx.channel or ctx.author
            pignlet = await channel.send(pretty_pingers)
            await asyncio.sleep(1.5)
        return pretty_pingers + '\n'
    return ''
    
async def log_message(ctx: interactions.SlashContext, msg: str,*,pingers: None | Sequence[int] = None,_do_print: bool = True):
    if ctx.ezwizard3_special_ctx_attr_mode == 1:
        ctx.ezwizard3_special_ctx_attr_testing_log_message(msg)
        return
    if _do_print:
        print(msg)

    channel = ctx.channel or ctx.author
    
    msg = await pretty_pingers_do(ctx,pingers,True,_do_print) + msg
        
    noitce_msgs = [attr_name for attr_name in dir(ctx) if attr_name.startswith('ezwizard3_special_ctx_attr_noticemsg_')]
    for attr_name in noitce_msgs:
        new_line_chars = '\n\n' if attr_name == noitce_msgs[-1] else '\n\n\n'
        msg = getattr(ctx,attr_name) + new_line_chars + msg

    
    if len(msg) > 2000-1-3:
        msg = msg[:2000-1-3] + '...'

    if ctx.expired:
        await channel.send(msg)
    else:
        await ctx.edit(content=msg)


LOG_MESSAGE_TICK_TOCK_TOO_LONG = ', over 15 minutes spent here, likely bot is stuck and needs reboot (including the PS4)'
async def log_message_tick_tock(ctx: interactions.SlashContext, msg: str):
    """
    Use this when you know its gonna wait for a while, MAKE SURE YOU USE `asyncio.create_task` and cancel the task as soon as long task is done
    """
    if ctx.ezwizard3_special_ctx_attr_mode == 1:
        ctx.ezwizard3_special_ctx_attr_testing_log_message_tick_tock(msg)
        return
        
    msg = msg[:2000-len(LOG_MESSAGE_TICK_TOCK_TOO_LONG)]
    await log_message(ctx, msg)
    
    tick = 0
    while True:
        if ctx.expired:
            await log_message(ctx,msg + LOG_MESSAGE_TICK_TOCK_TOO_LONG, _do_print=False)
            while True:
                await asyncio.sleep(10)
        await log_message(ctx, f'{msg} {tick} seconds spent here', _do_print=False)
        await asyncio.sleep(10)
        tick += 10
    

LOG_USER_ERROR_PRETTY_FMT_STRING = '<@{}>❌The command finished with error: {} ❌'
async def log_user_error(ctx: interactions.SlashContext, error_msg: str,*,pingers: None | Sequence[int] = None):
    if ctx.ezwizard3_special_ctx_attr_mode == 1:
        pingers = [] or pingers
        ctx.ezwizard3_special_ctx_attr_testing_log_user_error(msg,pingers)
        return
        
    files = []
    # if error_msg == 'Theres too many people using the bot at the moment, please wait for a spot to free up':
        # # await ctx.send(get_a_stupid_silly_random_string_not_unique(),ephemeral=False)
        # return
    print(f'user bad ##################\n{error_msg}')
    channel = ctx.channel or ctx.author

    error_msg = await pretty_pingers_do(ctx,pingers,False,True) + error_msg

    noitce_msgs = [attr_name for attr_name in dir(ctx) if attr_name.startswith('ezwizard3_special_ctx_attr_noticemsg_')]
    for attr_name in noitce_msgs:
        new_line_chars = '\n\n' if attr_name == noitce_msgs[-1] else '\n\n\n'
        error_msg = getattr(ctx,attr_name) + new_line_chars + error_msg
    
    full_msg = LOG_USER_ERROR_PRETTY_FMT_STRING.format(ctx.author_id,error_msg)
    
    is_big_message = len(full_msg) > 2000-1-3
    async with TemporaryDirectory() if is_big_message else nullcontext() as message_tp:
        if is_big_message:
            message_txt_path = Path(message_tp,'message.txt')
            message_txt_path.write_text(error_msg,encoding="utf-8")
            files.append(str(message_txt_path))
            full_msg = LOG_USER_ERROR_PRETTY_FMT_STRING.format(ctx.author_id,'Error in message.txt file')
        

        if ctx.expired:
            await channel.send(full_msg,ephemeral=False,files=files)
        else:
            placeholder_meesage_to_allow_ping_to_actually_ping_the_user = await ctx.send(get_a_stupid_silly_random_string_not_unique(),ephemeral=False)
            await ctx.send(full_msg,ephemeral=False,files=files) 
            await ctx.delete(placeholder_meesage_to_allow_ping_to_actually_ping_the_user)

    await update_status()


LOG_USER_SUCCESS_PRETTY_FMT_STRING = '<@{}>✅The command finished sucesfully: {} ✅'
async def log_user_success(ctx: interactions.SlashContext, success_msg: str, file: str | None = None,*,pingers: None | Sequence[int] = None):
    files = [file] if file else []
    if ctx.ezwizard3_special_ctx_attr_mode == 1:
        pingers = [] or pingers
        ctx.ezwizard3_special_ctx_attr_testing_log_user_success(msg,pingers)
        return
    
    print(f'{ctx.user} id: {ctx.author_id} sucesfully did a command with msg: {success_msg}')
    channel = ctx.channel or ctx.author
    
    success_msg = await pretty_pingers_do(ctx,pingers,False,True) + success_msg
    
    noitce_msgs = [attr_name for attr_name in dir(ctx) if attr_name.startswith('ezwizard3_special_ctx_attr_noticemsg_')]
    for attr_name in noitce_msgs:
        new_line_chars = '\n\n' if attr_name == noitce_msgs[-1] else '\n\n\n'
        success_msg = getattr(ctx,attr_name) + new_line_chars + success_msg

    full_msg = LOG_USER_SUCCESS_PRETTY_FMT_STRING.format(ctx.author_id,success_msg)
    
    is_big_message = len(full_msg) > 2000-1-3
    async with TemporaryDirectory() if is_big_message else nullcontext() as message_tp:
        if is_big_message:
            message_txt_path = Path(message_tp,'message.txt')
            message_txt_path.write_text(success_msg,encoding="utf-8")
            files.append(str(message_txt_path))
            full_msg = LOG_USER_SUCCESS_PRETTY_FMT_STRING.format(ctx.author_id,'Success message in message.txt file')
        
        
        if ctx.expired:
            await channel.send(full_msg,ephemeral=False, files=files)
        else:
            placeholder_meesage_to_allow_ping_to_actually_ping_the_user = await ctx.send(get_a_stupid_silly_random_string_not_unique(),ephemeral=False)
            await ctx.send(full_msg,ephemeral=False, files=files) 
            await ctx.delete(placeholder_meesage_to_allow_ping_to_actually_ping_the_user)
    
    try:
        ctx.ezwizard3_special_ctx_attr_helped_people_by_allowing_non_cusa_google_drive_folders
    except AttributeError:
        pass
    else:
        add_new_helped_people_by_allowing_non_cusa_google_drive_folders(ctx.ezwizard3_special_ctx_attr_helped_people_by_allowing_non_cusa_google_drive_folders)
    
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

class Lbp3BackupThingTypes(Enum):
    DRY_DB_ARCHIVE_BACKUP = 0
    MOD_INSTALLER = 1

class Lbp3BackupThing(NamedTuple):
    title_id: str
    start_of_file_name: str
    level_name: str
    level_desc: str
    is_adventure: bool
    new_blocks_size: int
    backup_type: Lbp3BackupThingTypes = Lbp3BackupThingTypes.DRY_DB_ARCHIVE_BACKUP
    
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
    
    async def is_all_resources_free(self) -> bool:
        async with self.lock:
            return bool(self.used_resources)
    
SAVE_DIRS = ('save0', 'save1', 'save2', 'save3', 'save4', 'save5', 'save6', 'save7', 'save8', 'save9', 'save10', 'save11')

_save_mount_points = _ResourceManager(SAVE_DIRS)

async def get_save_str() -> str:
    return await _save_mount_points.acquire_resource()

async def is_bot_completely_free() -> bool:
    return await _save_mount_points.is_all_resources_free()

async def free_save_str(save_str: str,/) -> None:
    return await _save_mount_points.release_resource(save_str)

async def get_amnt_free_save_strs() -> int:
    return await _save_mount_points.get_free_resources_count()


mounted_saves_at_once = asyncio.Semaphore(12) # 3 i sadly got an unmount error, and with 2 too


def remove_pc_user_from_path(the_path: object,/) -> object:
    if not isinstance(the_path,(Path,AsyncPath)):
        return the_path
    
    parent_ezwizard_dir = Path(__file__).parent.parent
    
    if the_path.is_relative_to(PARENT_TEMP_DIR): 
        return the_path.relative_to(PARENT_TEMP_DIR)
    elif the_path.is_relative_to(parent_ezwizard_dir):
        return the_path.relative_to(parent_ezwizard_dir)
    else:
        return the_path
   
class CheatFunc(NamedTuple):
    func: Coroutine[None, None, str | None]
    kwargs: dict[str,Any]

    def pretty(self) -> str:
        return f"```py\nawait {self.func.__name__}({', '.join(f'{a}={remove_pc_user_from_path(b)!r}' for a,b in self.kwargs.items())})\n```\n"

class CheatFuncResult(NamedTuple):
    savename: str | None
    gameid: str | None


class DecFunc(NamedTuple):
    func: Coroutine
    kwargs: dict[str,Any]

    def pretty(self) -> str:
        return f"```py\nawait {self.func.__name__}({', '.join(f'{a}={remove_pc_user_from_path(b)!r}' for a,b in self.kwargs.items())})\n```\n"

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

def add_user_id_to_ban_list(ctx_author_id: str | int, reason: str):
    assert reason
    ctx_author_id = str(ctx_author_id)
    with SqliteDict("user_stuff.sqlite", tablename="banned_discord_user_ids") as db:
        db[ctx_author_id] = reason
        db.commit()
        
def remove_user_id_to_ban_list(ctx_author_id: str | int):
    ctx_author_id = str(ctx_author_id)
    with SqliteDict("user_stuff.sqlite", tablename="banned_discord_user_ids") as db:
        try:
            del db[ctx_author_id]
        except KeyError:
            pass
        else:
            db.commit()
        
def is_user_id_in_ban_list(ctx_author_id: str | int) -> list | None:
    ctx_author_id = str(ctx_author_id)
    with SqliteDict("user_stuff.sqlite", tablename="banned_discord_user_ids") as db:
        try:
            return db[ctx_author_id]
        except KeyError:
            return None

def add_account_id_to_ban_list(account_id: PS4AccountID, ctx_author_id: str | int):
    ctx_author_id = str(ctx_author_id)
    with SqliteDict("user_stuff.sqlite", tablename="banned_account_ids") as db:
        db[account_id.account_id] = ctx_author_id
        db.commit()

def is_account_id_in_ban_list(account_id: PS4AccountID) -> str | None:
    with SqliteDict("user_stuff.sqlite", tablename="banned_account_ids") as db:
        try:
            return db[account_id.account_id]
        except KeyError:
            return None

def remove_account_id_from_ban_list(account_id: PS4AccountID):
    with SqliteDict("user_stuff.sqlite", tablename="banned_account_ids") as db:
        try:
            del db[account_id.account_id]
        except KeyError:
            pass
        else:
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
        error_msg = f'```\n{format_exc().replace("Traceback (most recent call last):",get_a_stupid_silly_random_string_not_unique()+" (most recent call last):")}\n```\n'
    else:
        leader = '**Want more verbose or detailed error messages? use the /set_verbose_mode command**\n'
        error_msg = f'```\n{sys.exc_info()[1]}\n```\n'
    
    if error_msg == '```\n' + '\n```\n':
        error_msg = f'```\n{sys.exc_info()[0].__name__}\n```\n'
    
    if 'got 451' in str(sys.exc_info()[1]):
        leader += '**This error usually means, the decrypted save is too large to upload to the encrypted save**\n'
    
    return f'{leader}{message_1} reason:\n{error_msg}\n {message_2}'

def add_new_helped_people_by_allowing_non_cusa_google_drive_folders(unq_id: str,/):
    with SqliteDict("user_stuff.sqlite", tablename="helped_people_by_allowing_non_cusa_google_drive_folders_ids") as db:
        db[unq_id] = unq_id
        db.commit()

def get_amnt_of_helped_people_by_allowing_non_cusa_google_drive_folders() -> int:
    with SqliteDict("user_stuff.sqlite", tablename="helped_people_by_allowing_non_cusa_google_drive_folders_ids") as db:
        return len(db)

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
            return 'You dont have any account id saved to the database!, try running the `/my_account_id` again'
    elif account_id == '1':
        return PS4AccountID('0000000000000000')
    
    if account_id[0] not in '0123456789':
        if not is_psn_name(account_id):
            return f'Not a valid psn name {account_id}, check it again!'
 
        try:
            user = psnawp.user(online_id=account_id)
        except PSNAWPNotFound:
            return f'Could not find psn name {account_id}, perhaps you mispelled it?'

        account_id = PS4AccountID.from_account_id_number(user.account_id).account_id

    
    try:
        my_account_id = PS4AccountID(account_id)
        try:
            my_account_id_for_my_acc = PS4AccountID(get_user_account_id(author_id))
        except KeyError: pass
        else:
            if my_account_id_for_my_acc == my_account_id:
                ctx.ezwizard3_special_ctx_attr_noticemsg_omljustusethe0optionsaccountid = '**Remember, you dont have to manually type in your account id, just put 0 in the field!**'
        return my_account_id
    except ValueError:
        return f'{account_id} is not a valid account id, it should be the one in your SAVEDATA folder! Or get it from the `/my_account_id` command'


def list_ps4_saves(folder_containing_saves: Path,/) -> Generator[tuple[Path,Path],None,None]:
    for filename in folder_containing_saves.rglob('*'):
        if is_ps4_title_id(filename.parent.name) and filename.suffix == '.bin' and filename.is_file() and Path(filename.with_suffix('')).is_file():
            yield filename,Path(filename.with_suffix(''))


async def ps4_life_check(ctx: interactions.SlashContext | None = None):
    channel = ctx.channel or ctx.author
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    try:
        await ps4.notify('life check!')
    except Exception:
        try:
            await channel.send(HUH) if ctx else None
        except Exception:
            pass
        raise KeyboardInterrupt


def get_only_ps4_saves_from_zip(ps4_saves_thing: SevenZipInfo,/,archive_name: str | Path) -> tuple[list[tuple[Path,Path]], list[SevenZipFile]]:
    ps4_saves: list[tuple[Path,Path]] = []
    found_zips: list[SevenZipFile] = [] # we are only doing one level of recusion, this is because its common practise to put single CUSAxxxxx zips inside of one large zip
    
    archive_name_is_title_id = is_ps4_title_id(archive_name.stem.split(' ')[0].upper())
    
    for zip_file in ps4_saves_thing.files.values():
        if '__MACOSX' in zip_file.path.parts[:-1]: continue # if you do happen to have saves in this folder, then tough luck
        if zip_file.path.name.startswith('._'): continue
        
        if not filename_valid_extension(zip_file.path): # returns error string if not valid archive
            found_zips.append(zip_file)
            continue
            
        if zip_file.path.suffix != '.bin': continue
        if not zip_file.is_file: continue
        if not is_ps4_title_id(zip_file.path.parent.name): 
            if not (len(zip_file.path.parts) == 1 and archive_name_is_title_id):
                continue
        
        white_file = zip_file.path.with_suffix('')
        if not ps4_saves_thing.files.get(white_file): continue
        if zip_file.size != 96:
            raise InvalidBinFile(f'Invalid bin file {zip_file.path} found in ')

        ps4_saves.append((zip_file.path,white_file))
    return ps4_saves,found_zips


class ArchiveAndTempFolder(NamedTuple):
    archive_path: Path
    temp_folder: Path


async def get_sce_sys_folders_determining_decrypted_savedata_folders(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID, archive_or_folder: Path | ArchiveAndTempFolder, max_size=FILE_SIZE_TOTAL_LIMIT) -> str:
    raise NotImplementedError('not finshed, theres dead code here, and i need to find out how to extract nested archives, as well as finding sce_sys folders, as well as loose sce_sys, and only doing one if its loose')
    temp_folder = archive_or_folder
    if isinstance(archive_or_folder,ArchiveAndTempFolder):
        temp_folder = archive_or_folder.temp_folder
        await log_message(ctx,f'Checking {link} if valid archive')
        try:
            zip_info = await get_archive_info(archive_or_folder.archive_path)
        except Exception as e:
            return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
        
        current_total_size = zip_info.total_uncompressed_size
        
        if current_total_size > max_size:
            return f'The decompressed {link} is too big ({pretty_bytes(current_total_size)}), the max is {pretty_bytes(max_size)}' # if its a folder, im assuming the size was already checked
        
        await log_message(ctx,f'Extracting {link}')
        await extract_full_archive(archive_or_folder.archive_path,temp_folder,'x')
    
    
    found_an_archive = False
    found_a_savedata0_folder = False
    
    found_things = 0
    consider_using_option = 'raw_encrypt_folder_type_2'
    
    await log_message(ctx,f'Looking for `sce_sys` folders in {link}')
    
#    for x in temp_fold.iterdir():
#        if 
    
    for x in temp_folder.rglob('*'):
        if '__MACOSX' in x.parts[:-1]: continue # if you do happen to have saves in this folder, then tough luck
        if x.name.startswith('._'): continue
        if not x.is_dir():
            if not filename_valid_extension(x.name):
                ctx.ezwizard3_special_ctx_attr_noticemsg_ = '**We found some archives in the decrpyted saves, we do not support unpacking archives within archives for this command, if the archives are part of the decrypted save, please ignore this message**'
                found_an_archive = True
            continue
        if x.name == 'savedata0' and (x.parts.count('savedata0') == 1):
            consider_using_option = 'raw_encrypt_folder'
        
        if x.name == 'sce_sys' and (x.parts.count('sce_sys') == 1):
            pretty_dir = x.relative_to(temp_folder)
            pretty_dir = str(pretty_dir.parent if pretty_dir.parent.parts else 'LOOSE')
            
            await log_message(ctx,f'Checking if param.sfo in {pretty_dir} is valid')
            param_sfo = x / 'param.sfo'
            if not param_sfo.is_file():
                return f'No param.sfo found in {pretty_dir} + {link}'
            try:
                with open(param_sfo,'rb') as f:
                    my_param = PS4SaveParamSfo.from_buffer(f)
            except Exception:
                return make_error_message_if_verbose_or_not(ctx.author_id,f'bad param.sfo in {pretty_dir} + {link}','')
            my_param.with_new_account_id(account_id)
            
            account_id_banned_res = my_param.check_if_account_id_is_banned()
            if account_id_banned_res:
                return account_id_banned_res


            param_sfo.write_bytes(bytes(my_param))
            await log_message(ctx,f'Doing some cleanup for {pretty_dir} + {link}')
            make_folder_name_safe(pretty_dir)
            await shutil.move(x.parent,output_folder)
            found_things += 1
            if found_things > MAX_RESIGNS_PER_ONCE:
                return f'Too many decrypted saves in {link}, max is {MAX_RESIGNS_PER_ONCE}'
    if not found_things:
        return f'Did not find any sce_sys folders in there, consider using /{consider_using_option} instead'
    return ''
    
    
async def extract_ps4_encrypted_saves_archive(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID, archive_name: Path) -> str:
    await log_message(ctx,f'Checking {link} if valid archive')
    try:
        zip_info = await get_archive_info(archive_name)
    except Exception as e:
        return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
    
    current_total_size = zip_info.total_uncompressed_size
    
    if current_total_size > FILE_SIZE_TOTAL_LIMIT:
        return f'The decompressed {link} is too big ({pretty_bytes(current_total_size)}), the max is {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}'
    
    await log_message(ctx,f'Looking for saves in {link}')
    
    try:
        ps4_saves,found_zips = get_only_ps4_saves_from_zip(zip_info,archive_name)
    except InvalidBinFile as e:
        return str(e) + link
    
    
    
    found_zips_2 = [] # Just to not raise NameError later on
    
    async with TemporaryDirectory() if found_zips else nullcontext() as temp_store_zips:
        for i,zip_file in enumerate(found_zips):
            await log_message(ctx,f'Extracting subzip {zip_file.path} from {link}')
            
            here_the_zip = Path(temp_store_zips,f'z{i}')
            real_zip_path = here_the_zip / zip_file.path.name
            
            try:
                await extract_single_file(archive_name,zip_file.path,here_the_zip)
            except Exception as e:
                return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
            
            current_total_size -= zip_file.size
            
            await log_message(ctx,f'Checking if subzip {zip_file.path} from {link} is valid')
            try:
                zip_info = await get_archive_info(here_the_zip)
            except Exception as e:
                return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
            
            current_total_size += zip_info.total_uncompressed_size
            if current_total_size > FILE_SIZE_TOTAL_LIMIT:
                return f'The decompressed {link} is too big ({pretty_bytes(current_total_size)}), the max is {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}'

            try:
                ps4_saves_2,found_zips_2 = get_only_ps4_saves_from_zip(zip_info,archive_name)
            except InvalidBinFile as e:
                return str(e) + f'{link} + {zip_file.path}'
            
            ps4_saves += [(bin_file,(white_file,real_zip_path,zip_file.path)) for bin_file,white_file in ps4_saves_2]
            
        
        if not ps4_saves:
            nested_archives_middle_text = ' we also only support one level of nested archives.' if found_zips_2 else ''
            return f'Could not find any saves in {link}, maybe you forgot to pack the whole CUSAxxxxx folder?{nested_archives_middle_text} your save has 2 files, a file and another file with same name but with `.bin` extension, also it needs to be in a folder with its name being a title id, eg CUSA12345. Otherwise I won\'t be able to find it!'
        
        try:
            ctx.ezwizard3_special_ctx_attr_special_save_files_thing
        except AttributeError:
            pass
        else:
            if ctx.ezwizard3_special_ctx_attr_special_save_files_thing == SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT:#
                if len(ps4_saves) != 1:
                    return f'The archive {link} has more then one save, we can only do 1 save at once for encrypt and import commands, please delete the other saves in this. If you want to upload the same decrypted save to mutiple encrypted saves (which you probably dont) set allow_mulit_enc to Yes'
        
        if len(ps4_saves) > MAX_RESIGNS_PER_ONCE:
            return f'The archive {link} has too many saves {len(ps4_saves)}, the max is {MAX_RESIGNS_PER_ONCE} remove {len(ps4_saves) - MAX_RESIGNS_PER_ONCE} saves and try again'
        
        for bin_file,white_file in ps4_saves:
            if isinstance(white_file,tuple):
                white_file,current_white_file_archive_path,pretty_zip_file_path = white_file
            else:
                pretty_zip_file_path = Path('')
                current_white_file_archive_path = archive_name

            if len(bin_file.parts) == 1:
                bin_parent_pretty = Path('LOOSE',current_white_file_archive_path.stem.split(' ')[0].upper())
            else:
                bin_parent_pretty = bin_file.parent

            pretty_dir_name = make_folder_name_safe(pretty_zip_file_path / bin_parent_pretty)
            new_path = Path(output_folder,pretty_dir_name,make_ps4_path(account_id,bin_parent_pretty.name))
            new_path.mkdir(exist_ok=True,parents=True)
            await log_message(ctx,f'Extracting {white_file} from {link}{" + "+str(pretty_zip_file_path) if pretty_zip_file_path.parts else ""}')
            try:
                await extract_single_file(current_white_file_archive_path,white_file,new_path)
                await extract_single_file(current_white_file_archive_path,bin_file,new_path)
            except Exception as e:
                return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
        return ''

def is_a_savedata0_folder(savedata0_path: Path, is_file: bool) -> bool:
    if is_file:
        return False
    
    if '__MACOSX' in savedata0_path.parts or savedata0_path.name.startswith('._'):
        return False
    
    folder_parts = savedata0_path.parts
    
    if folder_parts.count('savedata0') != 1:
        return False
    
    # yes i know i can make the below `return folder_parts[-1] == 'savedata0'` but this will be cleaner to add more conditions if i want to later
    if folder_parts[-1] == 'savedata0':
        return True
    
    return False


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
        await log_message(ctx,f'Getting file metadata from {link}')
        try:
            zip_file = await get_file_info_from_id(new_link)
        except Exception as e:
            return f'Could not get file metadata from {link}, got error {type(e).__name__}: {e}, maybe its not public?'
        if validation_result := validation(zip_file.file_name_as_path):
            return f'{link} failed validation reason: {validation_result}'
        
        if zip_file.size > max_size:
            return f'The file {link} is too big ({pretty_bytes(zip_file.size)}), we only accept {pretty_bytes(max_size)}, if you think this is wrong please report it'
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
    
    if link.startswith('https://filetransfer.io/data-package'):
        link = link.removesuffix('/') # yes i can combine the 2 links but it looks "cleaner" this way (as if this codebase is clean)
        link = link.removesuffix('/download') + '/download' # TODO theres an extremely low chance that a url can be https://filetransfer.io/data-package/download where `download` is an id, therefore it wont fix that url, but user can manually fix the url himself and i dont wanna write more code then this
        

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
                            return f'{link} failed validation reason: {validation_result}'
                        file_size: int | None | str = response.headers.get('Content-Length')
                        if file_size is None:
                            file_size = '? Bytes'
                        else:
                            try:
                                file_size = int(file_size)
                            except ValueError:
                                return f'Content-Length {file_size!r} was not a valid number'
                            if file_size > max_size:
                                return f'The file {link} is too big ({pretty_bytes(file_size)}), we only accept {pretty_bytes(max_size)}, if you think this is wrong please report it'
                            if file_size < 2:
                                return f'The file {link} is too small lmao'
                            file_size = pretty_bytes(file_size)
                        downloaded_size = 0
                        chunks_done = 0
                        direct_zip = Path(donwload_location,filename)
                        with open(direct_zip, 'wb') as f:
                            while True:
                                if not(chunks_done % AMNT_OF_CHUNKS_TILL_DOWNLOAD_BAR_UPDATE):
                                    await log_message(ctx,f'Downloading {link} {pretty_bytes(downloaded_size)}/{file_size}')
                                chunk = await response.content.read(DOWNLOAD_CHUNK_SIZE)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                chunks_done += 1
                                if downloaded_size > max_size:
                                    return f'YOU LIED! {link} is too big ({pretty_bytes(downloaded_size)}), we only accept {pretty_bytes(max_size)}, if you think this is wrong please report it'
                        await log_message(ctx,f'Downloaded {link} {pretty_bytes(downloaded_size)}')
                        break
                    elif (response.status == 524) and link.startswith('https://zaprit.fish/dl_archive/'):
                        await log_message(ctx,f'Slot id {link} has never been downloaded before, so waiting 2 minutes to try downloading it again')
                        await asyncio.sleep(2*60)
                        continue
                    else:
                        if link.startswith('https://zaprit.fish/dl_archive/') and (b"Level not found" in (await response.content.read(10_000_000))):
                            return ZapritFishKnownLinkError(f'The slot id {link} doesn\'t exist')
                        return f'Failed to download {link}. Status code: {response.status}'
            else: # no break, or return in this case
                return ZapritFishKnownLinkError(f'Took too many tries to download {link}, perhaps try command again')
        except Exception as e:
            return make_error_message_if_verbose_or_not(ctx.author_id,f'Invalid url {link}','maybe you copied the wrong link?')
    return direct_zip



async def download_decrypted_savedata0_folder(ctx: interactions.SlashContext,link: str, output_folder: Path, allow_any_folder: bool, unpack_first_root_folder: bool) -> str:
    """
    For now at least, we are only gonna allow one encryption at a time
    """
    new_link = extract_drive_folder_id(link)
    if new_link:
        ctx.ezwizard3_special_ctx_attr_noticemsg_google_drive_folders_not_needed_anymore_savedata0 = '**Since eZwizard3, you no longer have to upload decrypted saves as google drive folders, we support archives (zips, rars etc) contaning the savedata0 folder from any download link, (like discord file links) or use /file2url command**'
        await log_message(ctx,f'Getting files metadata from folder {link}')
        try:
            raw_files = await list_files_in_gdrive_folder(new_link,await gdrive_folder_link_to_name(new_link),False)
        except Exception as e:
            return f'Could not get files metadata from folder {link}, got error {type(e).__name__}: {e}, maybe its not public?'
        if not allow_any_folder:
            await log_message(ctx,f'Looking for a savedata0 folder in {link}')
            seen_savedata0_folders: set[GDriveFile] = {
                p
                for p in raw_files.values()
                if is_a_savedata0_folder(p.file_name_as_path,p.is_file)
            }

            if not seen_savedata0_folders:
                return f'Could not find any decrypted saves in {link}, make sure to put the decrypted save contents in a savedata0 folder and upload that, or use the /raw_encrypt_folder_type_2 command'

            if len(seen_savedata0_folders) > 1:
                return f'Too many decrypted saves in {link}, we only support encrypting one save per command'
            for savedata0_folder in seen_savedata0_folders:
                pass
        else:
            savedata0_folder = await get_folder_info_from_id(new_link)
        await log_message(ctx,f'Checking if {link} savedata0 folder is too big or not')
        try:
            test = await get_gdrive_folder_size(savedata0_folder.file_id)
        except Exception:
            return 'blud thinks hes funny'
        if test[0] > FILE_SIZE_TOTAL_LIMIT:
            return f'The decrypted save {link} is too big ({pretty_bytes(test[0])}), maybe you uploaded a wrong file to it? max is {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}'
        if test[1] > ZIP_LOOSE_FILES_MAX_AMT:
            return f'The decrypted save {link} has too many loose files ({test[1]}), max is {ZIP_LOOSE_FILES_MAX_AMT} loose files (uploading as a zip instead, will not have such limitations)'

        await log_message(ctx,f'Downloading {link} savedata0 folder')
        Path(output_folder,'savedata0').mkdir(parents=True,exist_ok=True)# TODO maybe i dont gotta do this, but i am
        new_savedata0_folder_made = Path(output_folder,'savedata0')
        try:
            await download_folder(savedata0_folder.file_id,new_savedata0_folder_made)
        except Exception:
            return 'blud thinks hes funny'
        if unpack_first_root_folder:
            await log_message(ctx,f'Doing some file management with {link}')
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
    await log_message(ctx,f'Checking {link} if valid archive')
    try:
        a = await get_archive_info(archive_name)
    except Exception as e:
        return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'

    if a.total_uncompressed_size > FILE_SIZE_TOTAL_LIMIT:
        return f'The decompressed {link} is too big ({pretty_bytes(a.total_uncompressed_size)}), the max is {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}'

    if not allow_any_folder:
        await log_message(ctx,f'Looking for decrypted saves in {link}')
        seen_savedata0_folders: set[SevenZipFile] = {
            p
            for p in a.files.values()
            if is_a_savedata0_folder(p.path, p.is_file)
        }
        if not seen_savedata0_folders:
            return f'Could not find any decrypted saves in {link}, make sure to put the decrypted save contents in a savedata0 folder and archive that, or use the /raw_encrypt_folder_type_2 command'
        if len(seen_savedata0_folders) > 1:
            return f'Too many decrypted saves in {link}, we only support encrypting one save per command'

        for savedata0_folder in seen_savedata0_folders:
            pass
        
        await log_message(ctx,f'Extracting savedata0 from {link}')
        try:
            await extract_single_file(archive_name,savedata0_folder.path,output_folder,'x')
        except Exception as e:
            return f'Invalid archive after downloading it {link}, error when unpacking {type(e).__name__}: {e}'
        if not savedata0_folder.path == Path('savedata0'):
            await log_message(ctx,f'Doing some file management with {link}')
            await shutil.move(Path(output_folder, savedata0_folder.path),output_folder)
            if savedata0_folder.path.parts[0] != Path('savedata0'):
                await shutil.rmtree(Path(output_folder,savedata0_folder.path.parts[0]))

        return ''
    else:
        await log_message(ctx,f'Extracting decrypted save from {link}')
        new_savedata0_folder_made = Path(output_folder,'savedata0')
        new_savedata0_folder_made.mkdir(parents=True, exist_ok=True)
        await extract_full_archive(archive_name,new_savedata0_folder_made,'x')
        if unpack_first_root_folder:
            await log_message(ctx,f'Doing some file management with {link}')
            checker = AsyncPath(new_savedata0_folder_made)
            if link == 'https://github.com/shahrilnet/remote_lua_loader/archive/refs/heads/main.zip':
                thing = checker / 'remote_lua_loader-main/savedata'
                if not await thing.is_dir():
                    return f'remote_lua_loader-main/savedata folder doesnt exist in {link}, this is not your fault, please report this'
            else:
                thing_count = 0
                async for thing in checker.iterdir():
                    thing_count += 1
                if thing_count != 1:
                    return ''
                
                if await thing.is_file(): # This is incase a user sends a zip with a single file
                    return ''
                
            async for file_name in thing.iterdir():
                await shutil.move(file_name,new_savedata0_folder_made)
            
            if link == 'https://github.com/shahrilnet/remote_lua_loader/archive/refs/heads/main.zip':
                await shutil.rmtree(thing.parent)
            else:
                await shutil.rmtree(thing)


async def download_ps4_saves(ctx: interactions.SlashContext,link: str, output_folder: Path, account_id: PS4AccountID) -> str:
    """\
    function to download ps4 encrypted saves from a user given link, if anything goes wrong then a string error is returned, otherwise empty string (falsely).
    the output_folder will contain the ps4 encrypted saves, itll be in a nice format that is ready for sending
    """
    new_link = extract_drive_folder_id(link)
    if new_link:
        ctx.ezwizard3_special_ctx_attr_noticemsg_google_drive_folders_not_needed_anymore_encsaves = '**Since eZwizard3, you no longer have to upload saves as google drive folders, we support archives (zips, rars etc) contaning the CUSAxxxxx folder from any download link, (like discord file links) or use /file2url command**'
        
        await log_message(ctx,f'Getting files metadata from folder {link}')
        try:
            raw_files = await list_files_in_gdrive_folder(new_link,await gdrive_folder_link_to_name(new_link),False)
        except Exception as e:
            return f'Could not get files metadata from folder {link}, got error {type(e).__name__}: {e}, maybe its not public?'
        await log_message(ctx,f'Looking for saves in the folder {link}')
        ps4_saves = get_valid_saves_out_names_only(raw_files.values())
        
        if not ps4_saves:
            return f'Could not find any saves in the folder {link}, (if it has archives, give the archive link instead of folder) maybe you forgot to upload the whole CUSAxxxxx folder? your save has 2 files, a file and another file with same name but with `.bin` extension, also it needs to be in a folder with its name being a title id, eg CUSA12345. Otherwise I won\'t be able to find it!'
        total_ps4_saves_size = sum(x.bin_file.size + x.white_file.size for x in ps4_saves)

        try:
            ctx.ezwizard3_special_ctx_attr_special_save_files_thing
        except AttributeError:
            pass
        else:
            if ctx.ezwizard3_special_ctx_attr_special_save_files_thing == SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT:#
                if len(ps4_saves) != 1:
                    return f'The folder {link} has more then one save, we can only do 1 save at once for encrypt and import commands, if you want to upload the same decrypted save to mutiple encrypted saves set allow_mulit_enc to Yes'

        if len(ps4_saves) > MAX_RESIGNS_PER_ONCE:
            return f'The folder {link} has too many saves {len(ps4_saves)}, the max is {MAX_RESIGNS_PER_ONCE} remove {len(ps4_saves) - MAX_RESIGNS_PER_ONCE} saves and try again'

        if total_ps4_saves_size > FILE_SIZE_TOTAL_LIMIT:
            return f'The total number of saves in {link} is too big, the max size of saves is {pretty_bytes(FILE_SIZE_TOTAL_LIMIT)}, {pretty_bytes(total_ps4_saves_size)} is too big'

        for bin_file,white_file in ps4_saves:
            if bin_file.size != 96:
                return f'Invalid bin file {bin_file.file_name_as_path} found in {link}'
            
            is_google_drive_parent_folder_a_cusa = is_ps4_title_id(white_file.file_name_as_path.parent.name)
            
            title_id = white_file.file_name_as_path.parent.name if is_google_drive_parent_folder_a_cusa else 'CUSA00000'
            
            if not is_google_drive_parent_folder_a_cusa:
                ctx.ezwizard3_special_ctx_attr_helped_people_by_allowing_non_cusa_google_drive_folders = f'{white_file.file_id}/{bin_file.file_id}'
            
            x = make_folder_name_safe(bin_file.file_name_as_path.parent)
            
            new_white_path = Path(output_folder, x, make_ps4_path(account_id,title_id),white_file.file_name_as_path.name)
            new_bin_path = Path(output_folder, x, make_ps4_path(account_id,title_id),bin_file.file_name_as_path.name)
            
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
            if 'failed validation reason:' in direct_zip: # TODO this method means if i change the error msg in download_direct_link and not this, then this if statement never happens
                return f'{direct_zip} **(do not put decrypted saves into the save_files option)**'
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
    pretty_save_dir = Path(*pretty_save_dir.parts[:-5],'...',*pretty_save_dir.parts[-2:])
    
    # await log_message(ctx,'Ensuring base save exists on PS4 before uploading')
    # async with MountSave(ps4,mem,int(CONFIG['user_id'],16),BASE_TITLE_ID,save_dir_ftp) as mp:
        # pass
    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,'Connecting to PS4 ftp to upload encrypted save (this may take a while if mutiple slots are in use)'))
    async with mounted_saves_at_once:
        tick_tock_task.cancel()
        await log_message(ctx,f'Uploading {pretty_save_dir} to PS4')
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
    pretty_save_dir = Path(*pretty_save_dir.parts[:-5],'...',*pretty_save_dir.parts[-2:])
    
    tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,'Connecting to PS4 ftp to download encrypted save (this may take a while if mutiple slots are in use)'))
    async with mounted_saves_at_once:
        tick_tock_task.cancel()
        await log_message(ctx,f'Downloading {pretty_save_dir} from PS4')
        custon_decss = lambda: asyncio.run(_download_encrypted_from_ps4(bin_file_out, white_file_out, ftp_bin, ftp_white))
        await asyncio.get_running_loop().run_in_executor(None,custon_decss)


async def resign_mounted_save(ftp: aioftp.Client,new_mount_dir:str, account_id: PS4AccountID) -> PS4AccountID | str:
    old_account_id = PS4AccountID('0000000000000000')
    await ftp.change_directory(Path(new_mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            my_param = PS4SaveParamSfo.from_buffer(f)
        old_account_id = my_param.account_id
        my_param.with_new_account_id(account_id)
        account_id_banned_res = my_param.check_if_account_id_is_banned()
        if account_id_banned_res:
            return resign_mounted_save
        tp_param_sfo.write_bytes(bytes(my_param))
            
        await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)
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

async def emergency_unmount(savedatax: str, ps4: PS4Debug, mp, pretty_save_dir: Path) -> str | None:
    if savedatax:
        async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
            new_mount_dir = (MOUNTED_POINT / savedatax).as_posix()
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


async def _apply_cheats_on_ps4(account_id: PS4AccountID, bin_file: Path, white_file: Path, parent_dir: Path, cheats: Sequence[CheatFunc], save_dir_ftp: str | tuple[str,str], pretty_save_dir: Path, mount_save_title_id: str, ctx_author_id: str, special_thing: SpecialSaveFiles | None) -> str | tuple[list | PS4AccountID | str] | tuple[ExpectedError,str]:
    ps4 = PS4Debug(CONFIG['ps4_ip'])
    try:
        async with MountSave(ps4,mem,int(CONFIG['user_id'],16),mount_save_title_id,save_dir_ftp) as mp:
            savedatax = mp.savedatax
            new_mount_dir = (MOUNTED_POINT / savedatax).as_posix()
            if not mp:
                return f'Could not mount {pretty_save_dir}, reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")}) (base save {mount_save_title_id}/{save_dir_ftp}), if you get SCE_SAVE_DATA_ERROR_BROKEN please try the command again, this is a known issue to sometimes happen, if happens consistently, then the save may really is broken'
            # input(f'{mp}\n {new_mount_dir}')
            # We need to get real filename as the white_file.name can be differnt (such as a ` (1)` subfixed to it)
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                try:
                    await ftp.change_directory(Path(new_mount_dir,'sce_sys').as_posix())
                    async with TemporaryDirectory() as tp:
                        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
                        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
                        with open(tp_param_sfo,'rb') as f:
                            real_name = PS4SaveParamSfo.from_buffer(f).dir_name
                except Exception as e:
                    return f'Bad save {pretty_save_dir} ({e}) missing param.sfo or broken param.sfo'
            
            results = []
            for index, chet in enumerate(cheats):
                try:
                    # await log_message(ctx,'Connecting to PS4 ftp to do some cheats')
                    async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                        await ftp.change_directory(new_mount_dir)
                        
                        # await log_message(ctx,f'Applying cheat {chet.pretty()} {index + 1}/{len(cheats)} for {pretty_save_dir}')
                        result = await chet.func(ftp,new_mount_dir,real_name,**chet.kwargs)
                    results.append(result) if result else None
                except Exception as e:
                    if isinstance(e,ExpectedError):
                        show_error_type = '' if type(e) == ExpectedError else f'{type(e).__name__}: ' 
                        return HasExpectedError(f'{show_error_type}{e}',pretty_save_dir)
                    return make_error_message_if_verbose_or_not(ctx_author_id,f'Could not apply cheat {chet.pretty()}to {pretty_save_dir}','')
            # await log_message(ctx,'Connecting to PS4 ftp to do resign')
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                await ftp.change_directory(new_mount_dir) 
                # await log_message(ctx,f'Resigning {pretty_save_dir} to {account_id.account_id}')
                try:
                    account_id_old = await resign_mounted_save(ftp,new_mount_dir,account_id)
                except Exception:
                    return make_error_message_if_verbose_or_not(ctx_author_id,f'Bad save {pretty_save_dir}','bad or missing param.sfo')
                if isinstance(account_id_old,str):
                    return account_id_old
            
            
            async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                try:
                    await ftp.change_directory(Path(new_mount_dir,'sce_sys').as_posix())
                    async with TemporaryDirectory() as tp:
                        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
                        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
                        with open(tp_param_sfo,'rb') as f:
                            real_title_id = PS4SaveParamSfo.from_buffer(f).title_id
                        results.insert(0,CheatFuncResult(None,real_title_id))
                except Exception as e:
                    return f'Bad save {pretty_save_dir} ({e}) missing param.sfo or broken param.sfo'
            
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
        if emergency_res_unmount := await emergency_unmount(savedatax,ps4,mp,pretty_save_dir):
            return emergency_res_unmount
        
async def apply_cheats_on_ps4(ctx: interactions.SlashContext,account_id: PS4AccountID, bin_file: Path, white_file: Path, parent_dir: Path, cheats: Sequence[CheatFunc], save_dir_ftp: str | tuple[str,str], special_thing: SpecialSaveFiles | str | None) -> str | tuple[list | PS4AccountID] | ExpectedError:
    if isinstance(special_thing,str):
        special_thing = None
    pretty_save_dir = white_file.relative_to(parent_dir)
    pretty_save_dir = Path(*pretty_save_dir.parts[:-5],'...',*pretty_save_dir.parts[-2:])
    
    mount_save_title_id = BASE_TITLE_ID if isinstance(save_dir_ftp,str) else save_dir_ftp[1]
    
    if special_thing == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
        for chet in cheats:
            if chet.kwargs.get('decrypted_save_folder'):
                await log_message(ctx,f'Doing some file management for your mc world')
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
                    my_param = PS4SaveParamSfo.from_buffer(f)
                my_param.with_new_blocks_count(da_blocks)
                (savedata0hehe / 'sce_sys/param.sfo').write_bytes(bytes(my_param))
                    
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
                        new_name = f.read(0x80-1).encode('utf-8')
                except Exception:
                    pass
                
                if new_name:
                    pretty_save_dir = new_name
                    
                    with open(savedata0hehe / 'sce_sys/param.sfo','rb+') as f:
                        my_param = PS4SaveParamSfo.from_buffer(f)
                    my_param.with_new_description(new_name)
                    my_param.with_new_dir_name(white_file.name)
                    (savedata0hehe / 'sce_sys/param.sfo').write_bytes(bytes(my_param))
                
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

    await log_message(ctx,f'Attempting to apply cheats {"".join(chet.pretty() for chet in cheats)}to {pretty_save_dir}')
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
                    except Exception as e:
                        if isinstance(e,ExpectedError):
                            show_error_type = '' if type(e) == ExpectedError else f'{type(e).__name__}: ' 
                            return HasExpectedError(f'{show_error_type}{e}',pretty_save_dir)
                        return make_error_message_if_verbose_or_not(ctx_author_id,f'Could not custom decrypt your save {pretty_save_dir}.','')
            else:
                # await log_message(ctx,f'Downloading savedata0 folder from decrypted {pretty_save_dir}')
                async with aioftp.Client.context(CONFIG['ps4_ip'],2121) as ftp:
                    await ftp.change_directory(MOUNTED_POINT.as_posix())
                    await ftp.download(savedatax,decrypted_save_ouput / 'savedata0',write_into=True)
    finally:
        if emergency_res_unmount := await emergency_unmount(savedatax,ps4,mp,pretty_save_dir):
            return emergency_res_unmount
async def decrypt_saves_on_ps4(ctx: interactions.SlashContext, bin_file: Path, white_file: Path, parent_dir: Path,decrypted_save_ouput: Path, save_dir_ftp: str,decrypt_fun: DecFunc | None = None) -> str | None:
    pretty_save_dir = white_file.relative_to(parent_dir)
    pretty_save_dir = Path(*pretty_save_dir.parts[:-5],'...',*pretty_save_dir.parts[-2:])
    
    # await log_message(ctx,f'Attempting to mount {pretty_save_dir}')
    if decrypt_fun:
        await log_message(ctx,f'Attemping custom decryption {decrypt_fun.pretty()}for {pretty_save_dir}')
    else:
        await log_message(ctx,f'Attemping to download savedata0 folder from decrypted {pretty_save_dir}')
    custon_decss = lambda: asyncio.run(_decrypt_saves_on_ps4(bin_file, white_file, parent_dir, decrypted_save_ouput, save_dir_ftp, decrypt_fun, pretty_save_dir,ctx.author_id))
    res = await asyncio.get_running_loop().run_in_executor(None,custon_decss)
    return res

def _zipping_time(results: Path, parent_dir: Path, new_zip_name: Path):
    with zipfile.ZipFile(new_zip_name,'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zp:
        for file in results.rglob('*'):
            zp.write(file,file.relative_to(parent_dir))


async def send_result_as_zip(ctx: interactions.SlashContext,link_for_pretty: str,results: Path, parent_dir: Path, new_zip_name: Path, custom_msg: str,*,unzip_if_only_one_file: int = 0):
    global amnt_used_this_session
    global UPLOAD_SAVES_FOLDER_ID
    await log_message(ctx,f'Zipping up modified {link_for_pretty} saves (2 more steps left)')

    found_1_file = False
    if unzip_if_only_one_file:
        for x in results.rglob('*'):
            if x.is_file():
                if found_1_file:
                    found_1_file = False
                    break
                found_1_file = x
            
    if found_1_file:
        new_zip_name = found_1_file
    else:
        await asyncio.to_thread(_zipping_time,results,parent_dir,new_zip_name)
    
    real_file_size = new_zip_name.stat().st_size
    if real_file_size > ATTACHMENT_MAX_FILE_SIZE:
        await log_message(ctx,f'Uploading modified {link_for_pretty} saves to google drive (last step!) ({pretty_bytes(real_file_size)} file)')
        try:
            google_drive_uploaded_user_zip_download_link = await google_drive_upload_file(new_zip_name,UPLOAD_SAVES_FOLDER_ID)
        except Exception as e:
            if 'storageQuotaExceeded' in str(e):
                if CONFIG['automatically_delete_gdrive_saves']:
                    await delete_google_drive_file_or_file_permentaly(UPLOAD_SAVES_FOLDER_ID)
                    UPLOAD_SAVES_FOLDER_ID = await make_gdrive_folder('ezwizardtwo_saves')
                else:
                    await log_message(ctx,f'oh no the bots owner gdrive is full, im giving you 2 minutes to ask ^^^ to clear some space',pingers=CONFIG['bot_admins'])
                    await asyncio.sleep(2*60)
                    await log_message(ctx,f'Uploading modified {link_for_pretty} saves to google drive (last step!) ({pretty_bytes(real_file_size)} file)')
                try:
                    google_drive_uploaded_user_zip_download_link = await google_drive_upload_file(new_zip_name,UPLOAD_SAVES_FOLDER_ID)
                except Exception as e2:
                    if 'storageQuotaExceeded' in str(e2):
                        await log_user_error(ctx,f'You were too late, owners gdrive is full! ask ^^^ to clear some space',pingers=CONFIG['bot_admins'])
                        return
                    else:
                        raise
            else:
                raise
        await log_user_success(ctx,f'Here is a google drive link to your {custom_msg.strip()}\n{google_drive_uploaded_user_zip_download_link}\nPlease download this asap as it can be deleted at any time ({pretty_bytes(real_file_size)} file)')
    else:
        # await shutil.move(new_zip_name,new_zip_name.name)
        await log_message(ctx,f'Uploading modified {link_for_pretty} saves as a discord {"file" if found_1_file else "zip"} attachment (last step!) ({pretty_bytes(real_file_size)} file)')
        await log_user_success(ctx,f'Here is a discord {"file" if found_1_file else "zip"} attachment to your {custom_msg.strip()}\nPlease download this asap as it can be deleted at any time',file=str(new_zip_name))
        # os.remove(new_zip_name.name)
    amnt_used_this_session += 1
    if not is_in_test_mode():
        add_1_total_amnt_used()

############################00 Real commands stuff
def lbp3_reregion_opt(func):
    return interactions.slash_option(
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
    )(func)
def unzip_if_only_one_file_opt(func):
    return interactions.slash_option(
    name="unzip_if_only_one_file",
    description="Do you want the bot to give unzipped decrpyted save?",
    required=True,
    opt_type=interactions.OptionType.INTEGER,
    choices=[ 
        interactions.SlashCommandChoice(name="Yes, unzip if its possible", value=1),
        interactions.SlashCommandChoice(name="No, always keep it zipped", value=0),
    ]
    )(func)
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
    description="Enter account ID (or username) to resign saves. Use 0 for database account ID or 1 for no resign",
    required=True,
    max_length=16,
    min_length=1,
    opt_type=interactions.OptionType.STRING
    )(func)
def account_id_to_ban_opt(func):
    return interactions.slash_option(
    name="account_id",
    description="The account id to ban, unban or check. Can ethier be a username or an account id",
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


def get_enc_save_if_desc(save_files: str,/) -> str:
    for url,desc in CONFIG['built_in_save_links']:
        if save_files == desc:
            return url
    return save_files

def get_dl_link_if_desc(dl_link_thing: str,/) -> str:
    for url,desc in CONFIG['built_in_dl_links']:
        if dl_link_thing == desc:
            return url
    return dl_link_thing

async def pre_process_cheat_args(ctx: interactions.SlashContext,cheat_chain: Sequence[CheatFunc | DecFunc],chet_files_custom: Path, savedata0_folder:Path) -> bool:
    await log_message(ctx,f'Looking for any `dl_link`s or `savedata0`s to download')
    for cheat in cheat_chain:
        for arg_name,link in cheat.kwargs.items():
            if isinstance(link,interactions.Attachment):
                await log_message(ctx,f'Downloading attachment {arg_name}')
                result = await download_direct_link(ctx,link.url,chet_files_custom,max_size=DL_FILE_TOTAL_LIMIT)
                if isinstance(result,str):
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = result
                link = result
            if arg_name.startswith('dl_link'):
                if isinstance(link,Path):
                    continue
                if is_str_int(link) and int(link) > 1:
                    try:
                        link = get_saved_url(ctx.author_id,int(link))
                    except KeyError:
                        await log_user_error(ctx,f'You dont have any url saved for {link}, try running the file2url command again!')
                        return False
                link = get_dl_link_if_desc(link)
                await log_message(ctx,f'Downloading {link} {arg_name}')
                result = await download_direct_link(ctx,link,chet_files_custom,max_size=DL_FILE_TOTAL_LIMIT,validation=filename_is_not_an_archive)
                if isinstance(result,str):
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = result
                link = result
            if arg_name in ('decrypted_save_file','decrypted_save_folder'):
                if isinstance(link,Path):
                    continue
                if is_str_int(link) and int(link) > 1:
                    try:
                        link = get_saved_url(ctx.author_id,int(link))
                    except KeyError:
                        await log_user_error(ctx,f'You dont have any url saved for {link}, try running the file2url command again!')
                        return False
                link = get_dl_link_if_desc(link)
                await log_message(ctx,f'Downloading {link} savedata0 folder or zip')
                result = await download_decrypted_savedata0_folder(ctx,link,savedata0_folder,arg_name=='decrypted_save_folder',cheat.kwargs['unpack_first_root_folder'])
                if result:
                    await log_user_error(ctx,result)
                    return False
                cheat.kwargs[arg_name] = savedata0_folder
                link = savedata0_folder
            if arg_name == 'gameid' and (not is_ps4_title_id(link)):
                await log_user_error(ctx,f'Invalid gameid {link}')
                return False
            if arg_name.startswith('psstring'):
                if not isinstance(link,str):
                    continue
                link = link.encode('utf-8')
                for specparemcodelol in PARAM_SFO_SPECIAL_STRINGS:
                    link = link.replace(specparemcodelol.encode('ascii'),bytes.fromhex(specparemcodelol))
                    link = link.replace(specparemcodelol.encode('ascii').lower(),bytes.fromhex(specparemcodelol))
                if arg_name in ('psstring_new_name','psstring_new_desc') and len(link) >= 0x80:
                    await log_user_error(ctx,f'your string {link} is too long, max is 127 characters')
                    return False
                    
                cheat.kwargs[arg_name] = link
            if arg_name.endswith('_p'):
                link = link.replace('\\','/')
                cheat.kwargs[arg_name] = link
    return True

async def base_do_dec(ctx: interactions.SlashContext,save_files: str, decrypt_fun: DecFunc | None = None,*,unzip_if_only_one_file: int = 0):
    ctx = await set_up_ctx(ctx)
    await ps4_life_check(ctx)
    
    save_files = get_enc_save_if_desc(save_files)
        
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
            has_expcted_errs = []
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
                    if isinstance(a,HasExpectedError):
                        has_expcted_errs.append(a)
                        continue
                    
                    await log_user_error(ctx,a)
                    if a == WARNING_COULD_NOT_UNMOUNT_MSG:
                        breakpoint()
                    return
            
            if has_expcted_errs:
                save_msgs = ''.join(f'{x[1]}:\n```\n{x[0]}\n```\n' for x in has_expcted_errs)
                await log_user_success(ctx,f'Got your messages\n\n{save_msgs}')
                return
            
            your_saves_msg = 'savedata0 decrypted save (Please use /advanced_mode_export command instead if you only want one file)'
            if decrypt_fun:
               your_saves_msg = (decrypt_fun.func.__doc__ or f'paypal me some money eboot.bin@protonmail.com and i might fix this message ({decrypt_fun.func.__name__})').strip()
            await send_result_as_zip(ctx,save_files,dec_tp,dec_tp,Path(tp,my_token + '.zip'),your_saves_msg,unzip_if_only_one_file=unzip_if_only_one_file)
            return
    finally:
        await free_save_str(save_dir_ftp)


async def base_do_cheats(ctx: interactions.SlashContext, save_files: str,account_id: str, cheat: CheatFunc | list[CheatFunc]):
    ctx = await set_up_ctx(ctx)
    await ps4_life_check(ctx)
    
    save_files = get_enc_save_if_desc(save_files)

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
            await log_user_error(ctx,f'You dont have any url saved for {save_files}, try running the file2url command again!')
            return
    
    
    await log_message(ctx,'Checking account_id')
    account_id: str | PS4AccountID = account_id_from_str(account_id,ctx.author_id,ctx)
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
        if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
            mc_filename = f'BedrockWorld{my_token.replace("_","")}@P547'
            mc_base_title_id = 'CUSA00265'
            real_save_dir_ftp = mc_filename
            tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'Getting ready to make base mc world {real_save_dir_ftp} (this may take a while if mutiple slots are in use)'))
            async with mounted_saves_at_once:
                tick_tock_task.cancel()
                await log_message(ctx,f'Making base mc world {real_save_dir_ftp}')
                owner_of_blocks_blocks = cheat.kwargs.get('mc_encrypted_save_size',None)
                assert isinstance(owner_of_blocks_blocks,int)
                custon_decss1 = lambda: asyncio.run(clean_base_mc_save(BASE_TITLE_ID,real_save_dir_ftp,blocks=owner_of_blocks_blocks))
                await asyncio.get_running_loop().run_in_executor(None,custon_decss1)
        elif isinstance(save_files,Lbp3BackupThing):
            mc_filename = save_files.start_of_file_name + my_token.replace("_","")
            mc_base_title_id = save_files.title_id
            real_save_dir_ftp = mc_filename
            tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'Getting ready to make base lbp3 level backup {real_save_dir_ftp} (this may take a while if mutiple slots are in use)'))
            async with mounted_saves_at_once:
                tick_tock_task.cancel()
                await log_message(ctx,f'Making base lbp3 level backup {real_save_dir_ftp}')
                custon_decss1 = lambda: asyncio.run(clean_base_mc_save(BASE_TITLE_ID,real_save_dir_ftp,blocks=save_files.new_blocks_size))
                await asyncio.get_running_loop().run_in_executor(None,custon_decss1)
            await log_message(ctx,f'Setting level filename to {mc_filename}')
            temp_savedata0 = cheat.kwargs['decrypted_save_file']
            with open(temp_savedata0 / 'savedata0/sce_sys/param.sfo','rb+') as f:
                my_param = PS4SaveParamSfo.from_buffer(f)
            my_param.with_new_dir_name(mc_filename)
            (temp_savedata0 / 'savedata0/sce_sys/param.sfo').write_bytes(bytes(my_param))
                
        else:
            real_save_dir_ftp = save_dir_ftp
        async with TemporaryDirectory() as tp:
            chet_files_custom = Path(tp, 'chet_files_custom')
            chet_files_custom.mkdir()
            enc_tp = Path(tp, 'enc_tp')
            enc_tp.mkdir()
            savedata0_folder = Path(tp,'savedata0_folder')
            savedata0_folder.mkdir()
            if isinstance(cheat,list):
                my_cheats_chain = get_cheat_chain(ctx.author_id) + cheat
                cheat = cheat[1] # this acts as a protection, you should not be giving single length lists
            else:
                my_cheats_chain = get_cheat_chain(ctx.author_id) + [cheat]
                
            
            
            if not await pre_process_cheat_args(ctx,my_cheats_chain,chet_files_custom,savedata0_folder):
                return
            

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
            got_expected_errors = False
            for bin_file, white_file in (done_ps4_saves := list(list_ps4_saves(enc_tp))):
                if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
                    pass
                elif isinstance(save_files,Lbp3BackupThing):
                    pass
                else:
                    await upload_encrypted_to_ps4(ctx,bin_file,white_file,enc_tp,real_save_dir_ftp)
                pretty_folder_thing = white_file.relative_to(enc_tp).parts[0] + white_file.name
                tick_tock_task = asyncio.create_task(log_message_tick_tock(ctx,f'Getting ready to mount {pretty_folder_thing} (this may take a while if mutiple slots are in use)'))
                async with mounted_saves_at_once:
                    tick_tock_task.cancel()
                    a: tuple[list[CheatFuncResult],PS4AccountID] = await apply_cheats_on_ps4(ctx,account_id,bin_file,white_file,enc_tp,my_cheats_chain,real_save_dir_ftp,save_files)
                if a == WARNING_COULD_NOT_UNMOUNT_MSG:
                    breakpoint()
                
                if isinstance(a,HasExpectedError):
                    got_expected_errors = True
                    results_big.append(a)
                    continue
                    
                if isinstance(a,str):
                    await log_user_error(ctx,a)
                    return
                results_small,old_account_id,real_name = a
                await download_encrypted_from_ps4(ctx,bin_file,white_file,enc_tp,real_save_dir_ftp)
                real_names.append(real_name)
                results_big.append(results_small)
            
            if got_expected_errors:
                save_msgs = ''.join(f'{x[1]}:\n```\n{x[0]}\n```\n' for x in results_big)
                await log_user_success(ctx,f'Got your messages\n\n{save_msgs}')
                return
                
            await log_message(ctx,f'Making sure file names in {save_files} are all correct')
            found_fakes = False
            for real_name, (bin_file, white_file) in zip(real_names, done_ps4_saves, strict=True):
                if white_file.name != real_name:
                    await log_message(ctx,f'Renaming {white_file.name} to {real_name}')
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
                
            await log_message(ctx,f'looking through results to do some renaming for {save_files}')
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
                    if gameid:
                        new_gameid_folder = white_file.parent.parent / gameid
                        new_gameid_folder.mkdir(exist_ok=True)
                        
                        white_file = white_file.rename(new_gameid_folder / white_file.name)
                        bin_file = bin_file.rename(new_gameid_folder / bin_file.name)
            
            if not account_id:
                account_id = old_account_id
                have_not_done_at_least_1_account_id_change = False
                await log_message(ctx,f'Refreshing {save_files} internal list 2/2')
                done_ps4_saves = list(list_ps4_saves(enc_tp))
                for bin_file, white_file in done_ps4_saves:
                    try:
                        white_file.parent.parent.rename(white_file.parent.parent.parent / account_id.account_id)
                    except FileNotFoundError:
                        if not have_not_done_at_least_1_account_id_change:
                            raise
                    have_not_done_at_least_1_account_id_change = True
            
            await log_message(ctx,f'Putting all saves in one PS4 folder in {save_files}')
            def long_lambda():
                found_files = [x.parts[-2:] for x in enc_tp.rglob('*') if x.is_file()]
                
                if len(found_files) > len(set(found_files)):
                    return
                
                enc_tp_other_saves = (enc_tp / 'other_saves')
                enc_tp_other_saves.mkdir()
                for x in enc_tp.iterdir():
                    if x.name == 'other_saves':
                        continue
                    x.rename(Path(x.parent,'other_saves',x.name))
                
                new_ps4_path = Path(enc_tp,'PS4/SAVEDATA',account_id.account_id)
                new_ps4_path.mkdir(exist_ok=True,parents=True)
                
                for x in enc_tp_other_saves.rglob('*'):
                    if not x.is_file():
                        continue
                    assert is_ps4_title_id(x.parent.name)
                    
                    (new_ps4_path / x.parent.name).mkdir(exist_ok=True)
                    new_save_file_path = new_ps4_path / x.parent.name / x.name
                    if new_save_file_path.is_file():
                        continue
                    x.rename(new_save_file_path)
            
            await asyncio.get_running_loop().run_in_executor(None,long_lambda)
                
            await log_message(ctx,f'Deleting empty folders in {save_files}')
            await asyncio.get_running_loop().run_in_executor(None,lambda: delete_empty_folders(enc_tp))
            
            custom_msg = (cheat.func.__doc__ or f'paypal me some money eboot.bin@protonmail.com and i might fix this message ({cheat.func.__name__})').strip()
            
            if isinstance(save_files,Lbp3BackupThing):
                if save_files.backup_type == Lbp3BackupThingTypes.DRY_DB_ARCHIVE_BACKUP:
                    custom_msg = 'Level backup from the level archive'
                elif save_files.backup_type == Lbp3BackupThingTypes.MOD_INSTALLER:
                    custom_msg = 'LittleBigPlanet .mod files encrypted'
            elif save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD:
                custom_msg = 'Encrypted minecraft .mcworld file'
            
            await send_result_as_zip(ctx,save_files,enc_tp,enc_tp,Path(tp,my_token + '.zip'),custom_msg)
            return
    finally:
        await free_save_str(save_dir_ftp)
        delete_chain(ctx.author_id)
        if save_files == SpecialSaveFiles.MINECRAFT_CUSTOM_SIZE_MCWORLD or isinstance(save_files,Lbp3BackupThing):
            custon_decss1 = lambda: asyncio.run(delete_base_save_just_ftp(BASE_TITLE_ID,real_save_dir_ftp))
            await asyncio.get_running_loop().run_in_executor(None,custon_decss1)  # TODO could be dangerous we are not using the mounted_saves_at_once sempahore

############################01 Custom decryptions
@interactions.slash_command(name="raw_decrypt_folder",description=f"use /advanced_mode_export instead if you want one file (max {MAX_RESIGNS_PER_ONCE} save per command)")
@dec_enc_save_files
async def do_raw_decrypt_folder(ctx: interactions.SlashContext,save_files: str):
    await base_do_dec(ctx,save_files)

# @interactions.slash_command(name="ps4saves_to_mcworlds",description=f"use /advanced_mode_export instead (max {MAX_RESIGNS_PER_ONCE} save per command)")
# @dec_enc_save_files
# async def do_raw_decrypt_folder(ctx: interactions.SlashContext,save_files: str):
    # await base_do_dec(ctx,save_files)
# ctx.ezwizard3_special_ctx_attr_special_save_files_thing

async def export_dl2_save(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None, just_show_hex_dump: bool = False, hex_dump_size: int = 512, hex_dump_seek: int = 0):
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
    do_hex_dump_thingy(decrypted_save_ouput / ftp_save[0],just_show_hex_dump,hex_dump_size,hex_dump_seek)


async def export_xenoverse_2_sdata000_dat_file(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None, just_show_hex_dump: bool = False, hex_dump_size: int = 512, hex_dump_seek: int = 0,verify_checksum: bool = True):
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
    do_hex_dump_thingy(decrypted_save_ouput / ftp_save[0],just_show_hex_dump,hex_dump_size,hex_dump_seek)

# @interactions.slash_option(name='verify_checksum',description='If set to true, then the command will fail if save has bad checksum (corrupted), default is True',required=False,opt_type=interactions.OptionType.BOOLEAN)


async def export_red_dead_redemption_2_or_gta_v_file(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None, just_show_hex_dump: bool = False, hex_dump_size: int = 512, hex_dump_seek: int = 0):
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
    do_hex_dump_thingy(decrypted_save_ouput / ftp_save[0],just_show_hex_dump,hex_dump_size,hex_dump_seek)

async def export_single_file_any_game(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/,*,filename_p: str | None = None, just_show_hex_dump: bool = False, hex_dump_size: int = 512, hex_dump_seek: int = 0):
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
    do_hex_dump_thingy(decrypted_save_ouput / ftp_save[0],just_show_hex_dump,hex_dump_size,hex_dump_seek)

game_dec_functions = { # Relying on the dict ordering here, "Game not here (might not work)" should be at bottom
    'Dying Light 2 Stay Human': export_dl2_save,
    'Grand Theft Auto V': export_red_dead_redemption_2_or_gta_v_file,
    'Red Dead Redemption 2': export_red_dead_redemption_2_or_gta_v_file,
    'DRAGON BALL XENOVERSE 2': export_xenoverse_2_sdata000_dat_file,
    'Game not here (might not work)': export_single_file_any_game,
}

def do_hex_dump_thingy(my_save: Path,just_show_hex_dump: bool, hex_dump_size: int, hex_dump_seek: int):
    assert hex_dump_size <= 512
    if not just_show_hex_dump:
        return
    with open(my_save,'rb+') as f:
        if hex_dump_seek < 0:
            whence = 2
        else:
            whence = 0 
        f.seek(hex_dump_seek,whence)
        start_offset = f.tell()
        raise ExpectedError(hex_dump(f.read(hex_dump_size),start_offset=start_offset))

@interactions.slash_command(name='advanced_mode_export',description="Export/decrypt your saves!")
@dec_enc_save_files
@unzip_if_only_one_file_opt
@interactions.slash_option(name='game',
    description='The game you want to export/decrypt saves of',
    opt_type=interactions.OptionType.STRING,
    required=True,
    choices=[
        interactions.SlashCommandChoice(name=gamenamey, value=gamenamey) for gamenamey in game_dec_functions.keys()
    ])
@filename_p_opt
@interactions.slash_option('just_show_hex_dump','Dont give file, just show a hex dump',interactions.OptionType.BOOLEAN,False)
@interactions.slash_option('hex_dump_size','The size of the hex dump, if just_show_hex_dump is True',interactions.OptionType.INTEGER,False,max_value=512,min_value=0)
@interactions.slash_option('hex_dump_seek','Where to seek in file',interactions.OptionType.INTEGER,False)
async def do_multi_export(ctx: interactions.SlashContext,save_files: str,unzip_if_only_one_file: int,**kwargs): # TODO allow custom args for differnt dec functions, like verify_checksum
    export_func = game_dec_functions[kwargs.pop('game')]
    await base_do_dec(ctx,save_files,DecFunc(export_func,kwargs),unzip_if_only_one_file=unzip_if_only_one_file)
###########################0 Custom cheats
cheats_base_command = interactions.SlashCommand(name="cheats", description="Commands for custom cheats for some games")

async def do_resign_dummy_cheat(ftp: aioftp.Client, mount_dir: str, save_name: str): """Resigned Saves"""
DUMMY_CHEAT_FUNC = CheatFunc(do_resign_dummy_cheat,{})
@interactions.slash_command(name="resign", description=f"Resign save files to an account id (max {MAX_RESIGNS_PER_ONCE} saves per command)")
@interactions.slash_option('save_files','The save files to resign too',interactions.OptionType.STRING,True)
@account_id_opt
async def do_resign(ctx: interactions.SlashContext,save_files: str,account_id: str):
    await base_do_cheats(ctx,save_files,account_id,DUMMY_CHEAT_FUNC)

def ignore_plans_opt(func):
    return interactions.slash_option(
    name = 'ignore_plans',
    description='Do you want to ignore .plan files in the mods? default is No',
    required=False,
    choices=[
        interactions.SlashCommandChoice(name='Yes (only levels (.bins) will get installed)', value=1),
        interactions.SlashCommandChoice(name='No (Everything gets installed (like costumes, objects etc))', value=0)
    ],
    opt_type=interactions.OptionType.INTEGER
    )(func)

def _dl_link_mod_file_options(func, count: int):
    for i in range(1,count+1):
        func = interactions.slash_option(
            name = f'dl_link_mod_file{i}',
            description='A mod file to install to a level backup or LBPxSAVE (bigfart), from toolkit/workbench',
            required=False,
            opt_type=interactions.OptionType.STRING
        )(func)
    return func

def dl_link_mod_file_11_options(func):
    return _dl_link_mod_file_options(func,11)

async def install_mods_for_lbp3_ps4(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,ignore_plans = False, **mod_files: Path):
    """
    LittleBigPlanet .mod files encrypted
    """
    l0_file = mod_files.pop('l0_file',None)
    await ftp.change_directory(mount_dir)
    files = [(path,info) for path, info in (await ftp.list(recursive=True)) if info['type'] == 'file' and path.parts[0] != 'sce_sys']
    try:
        ftp_save, = files
    except ValueError:
        raise ValueError('Too many files in the save, likley not a lbp3 big save or level backup') from None
    
    if ftp_save[0].name.startswith('bigfart') and (not l0_file):
        is_l0 = False
    elif ftp_save[0].name == ('L0'):
        is_l0 = True
    else:
        if l0_file:
            raise ValueError(f'Invalid level backup file {ftp_save[0].name}')
        else:
            raise ValueError(f'Invalid bigfart or level backup file {ftp_save[0].name}')

    async with TemporaryDirectory() if (not l0_file) else nullcontext() as tp:
        if not l0_file:
            sa = Path(tp,'bigfart_or_l0_level_backup')
            await ftp.download(ftp_save[0],sa,write_into=True)
            def _do_the_install_lbp3_ps4_mods_lcoal(): install_mods_to_bigfart(sa,tuple(mod_files.values()),install_plans = not ignore_plans, is_ps4_level_backup = is_l0)
            await asyncio.get_running_loop().run_in_executor(None, _do_the_install_lbp3_ps4_mods_lcoal)
        else:
            sa = l0_file

        await ftp.upload(sa,ftp_save[0],write_into=True)


littlebigplanet_3 = cheats_base_command.group(name="littlebigplanet_3", description="Cheats for LittleBigPlanet 3")
@littlebigplanet_3.subcommand(sub_cmd_name="install_mods", sub_cmd_description="Install .mod files to a level backup or LBPxSAVE (bigfart)")
@interactions.slash_option('save_files','The level backup or profile backup to install the mods too',interactions.OptionType.STRING,True)
@account_id_opt
@ignore_plans_opt
@dl_link_mod_file_11_options
async def do_lbp3_install_mods(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    if not any(key.startswith('dl_link_mod_file') for key in kwargs.keys()):
        ctx = await set_up_ctx(ctx)
        return await log_user_error(ctx,'Please give at least 1 dl_link_mod_file')
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(install_mods_for_lbp3_ps4,kwargs))

@littlebigplanet_3.subcommand(sub_cmd_name="mods2levelbackup", sub_cmd_description="Convert .mod files into a level backup with them in prize bubbles")
@account_id_opt
@lbp3_reregion_opt
@ignore_plans_opt
@dl_link_mod_file_11_options
async def do_mods2levelbackup(ctx: interactions.SlashContext,account_id: str,gameid: str,ignore_plans: int = 0,**mod_files):
    ignore_plans = bool(ignore_plans)
    if not mod_files:
        ctx = await set_up_ctx(ctx)
        return await log_user_error(ctx,'Please give at least 1 dl_link_mod_file')
    await base_do_cheats(ctx,LBP3_EU_LEVEL_BACKUP,account_id,[CheatFunc(install_mods_for_lbp3_ps4,{**mod_files,'ignore_plans':ignore_plans}),CheatFunc(re_region,{'gameid':gameid})])
    return # TODO finish off the below implmentation, need to have it set up a savedata0 with icon and param.sfo, similar to lbp_level_archive2ps4
    ctx = await set_up_ctx(ctx)
    if not mod_files:
        return await log_user_error(ctx,'Please give at least 1 dl_link_mod_file')
    
    async with TemporaryDirectory() as tp:
        chet_files_custom = Path(tp,'chet_files_custom')
        chet_files_custom.mkdir()
        
        sa = Path(tp,'l0')
        sa.write_bytes(LBP3_PS4_L0_FILE_TEMPLATE)
        for key,value in mod_files.items():
            await log_message(ctx,f'Checking {value}')
            if is_str_int(value) and int(value) > 1:
                try:
                    value = get_saved_url(ctx.author_id,int(value))
                except KeyError:
                    await log_user_error(ctx,f'You dont have any url saved for {value}, try running the file2url command again!')
                    return 
            value = get_dl_link_if_desc(value)
            await log_message(ctx,f'Downloading {value}')
            result = await download_direct_link(ctx,value,chet_files_custom,max_size=LBP3_PS4_L0_FILE_MAX_SIZE,validation=filename_is_not_an_archive)
            if isinstance(result,str):
                await log_user_error(ctx,result)
                return 
            mod_files[key] = result
        
        def _do_the_install_lbp3_ps4_mods_lcoal(): install_mods_to_bigfart(sa,tuple(mod_files.values()),install_plans = not ignore_plans, is_ps4_level_backup = True)
        try:
            await asyncio.get_running_loop().run_in_executor(None,_do_the_install_lbp3_ps4_mods_lcoal)
        except Exception:
            msg = make_error_message_if_verbose_or_not(ctx.author_id,f'Could not install modfiles','')
            await log_user_error(ctx,msg)
            return 
        
        if sa.stat().st_size > LBP3_PS4_L0_FILE_MAX_SIZE:
            await log_user_error(ctx,f'All the mods combined is too big ({pretty_bytes(l0_size)}), the max lbp3 ps4 level backup can only be {pretty_bytes(LBP3_PS4_L0_FILE_MAX_SIZE)} (try removing some mods)')
            return
        
        Lbp3BackupThing(gameid,f'{gameid}x00LEVEL',level_name,level_desc,is_adventure,new_blocks_size)


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
        ctx.ezwizard3_special_ctx_attr_special_save_files_thing = SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT

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
        ctx.ezwizard3_special_ctx_attr_special_save_files_thing = SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT

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

@interactions.slash_command(name="lbp_ps3_level_backup_zip_to_ps4", description=f"Convert a single ps3 lbp level backup to a ps4 level backup (lbp1, lbp2 and lbp3!)")
@account_id_opt
@interactions.slash_option('dl_link_level_backup','zip file containing a single ps3 level backup',interactions.OptionType.STRING,True)
@lbp3_reregion_opt
async def lbp_ps3_level_backup_zip_to_ps4(ctx: interactions.SlashContext, account_id: str, dl_link_level_backup: str, gameid: str):
    if is_str_int(dl_link_level_backup) and int(dl_link_level_backup) > 1:
        try:
            dl_link_level_backup = get_saved_url(ctx.author_id,int(dl_link_level_backup))
        except KeyError:
            await log_user_error(ctx,f'You dont have any url saved for {dl_link_level_backup}, try running the file2url command again!')
            return
    await lbp_ps3_level_backup2ps4('level backup',ctx, account_id, pretty_url=dl_link_level_backup, real_url=dl_link_level_backup, gameid=gameid)


@interactions.slash_command(name="lbp_level_archive2ps4", description=f"Gets the level from the lbp archive backup (dry.db) and turns it into a ps4 levelbackup")
@account_id_opt
@interactions.slash_option('slotid_from_drydb','The slot id from dry.db of the level you want, you can search for it on https://maticzpl.xyz/lbpfind',interactions.OptionType.INTEGER,True,min_value=56,max_value=100515565)
@lbp3_reregion_opt
async def do_lbp_level_archive2ps4(ctx: interactions.SlashContext, account_id: str, slotid_from_drydb: int, gameid: str):
    await lbp_ps3_level_backup2ps4('slot',ctx, account_id, pretty_url=f'`{slotid_from_drydb}`', real_url=f'https://zaprit.fish/dl_archive/{slotid_from_drydb}', gameid=gameid)


async def lbp_ps3_level_backup2ps4(pretty_entry_type_str: str, ctx: interactions.SlashContext, account_id: str, pretty_url: str, real_url: str, gameid: str):
    ctx = await set_up_ctx(ctx)
    if account_id == '1':
        return await log_user_error(ctx,'Cannot get original account id of save, perhaps you didnt mean to put 1 in account_id')
    async with TemporaryDirectory() as tp:
        tp = Path(tp)
        await log_message(ctx,f'Downloading {pretty_entry_type_str} {pretty_url}')
        result = await download_direct_link(ctx,real_url,tp)
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
        
        await log_message(ctx,f'Converting {pretty_entry_type_str} {pretty_url} to L0 file')
        with open(savedata0_folder / 'L0','wb') as f:
            level_name, level_desc,is_adventure,icon0_path = await asyncio.get_event_loop().run_in_executor(None, ps3_level_backup_to_l0_ps4,level_backup_folder,f)
            l0_size = f.tell()
        
        if l0_size > LBP3_PS4_L0_FILE_MAX_SIZE:
            await log_user_error(ctx,f'The {pretty_entry_type_str} {pretty_url} is too big ({pretty_bytes(l0_size)}), the max lbp3 ps4 level backup can only be {pretty_bytes(LBP3_PS4_L0_FILE_MAX_SIZE)}')
            return 
        
        await log_message(ctx,f'Doing some file management for {pretty_entry_type_str} {pretty_url}')
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
        
        tp_param_sfo = savedata0_folder / 'sce_sys/param.sfo'
        with open(tp_param_sfo,'rb') as f:
            my_param = PS4SaveParamSfo.from_buffer(f)
        
        my_param.with_new_region(gameid)
        my_param.with_new_name(f'lbp3PS4: {level_name}'.encode('utf-8'))
        my_param.with_new_description(level_desc.encode('utf-8'))


        await log_message(ctx,f'Getting decrypted save size for {pretty_entry_type_str} {pretty_url}')
        
        # new_blocks_size = sum((x.stat()).st_size for x in savedata0_folder.rglob('*'))
        async_savedata0_folder = AsyncPath(savedata0_folder)
        new_blocks_size = 0
        async for x in async_savedata0_folder.rglob('*'):
            new_blocks_size += (await x.stat()).st_size

        new_blocks_size = my_param.bytes_to_blocks_count(new_blocks_size + 3_145_728) # min save is 3mib, but adding the 3mib for room of sce_sys folder contents
        my_param.with_new_blocks_count(new_blocks_size)
        
        tp_param_sfo.write_bytes(bytes(my_param))
        
        await base_do_cheats(ctx,Lbp3BackupThing(gameid,base_name,level_name,level_desc,is_adventure,new_blocks_size),account_id,CheatFunc(upload_savedata0_folder,{'decrypted_save_file':savedata0_folder.parent,'clean_encrypted_file':CleanEncryptedSaveOption.DELETE_ALL_INCLUDING_SCE_SYS}))


############################02 saves info
async def get_keystone_key_from_save(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,ignore_errors_in_saves: bool) -> NoReturn:
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        tp_keystone = Path(tp,'a')

        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        
        with open(tp_param_sfo,'rb') as f:
            my_param = PS4SaveParamSfo.from_buffer(f)
            
        if my_param.miss_matching_title_ids:
            if not ignore_errors_in_saves:
                raise ValueError('Missmatching title ids in save')

        
        await ftp.download('keystone',tp_keystone,write_into=True)
        if tp_keystone.stat().st_size != 96:
            raise ValueError('Invalid keystone found in save')


        raise ExpectedError(f'{my_param.title_id!r}: {non_format_susceptible_byte_repr(tp_keystone.read_bytes())},')
@interactions.slash_command(
    name="saves_info",
    description="Get some common infos about saves",
    # group_name="group",
    # group_description="My command group",
    sub_cmd_name="keystone",
    sub_cmd_description=f"Print the keystones of your saves! (max {MAX_RESIGNS_PER_ONCE} saves per command)",
)
@interactions.slash_option('save_files','The save files you want the keystones of',interactions.OptionType.STRING,True)
@interactions.slash_option('ignore_errors_in_saves','Do you want to ignore any errors of the saves?',interactions.OptionType.INTEGER,True,
choices=[
    interactions.SlashCommandChoice(name="No, fail if theres any errors", value=0),
    interactions.SlashCommandChoice(name="Yes, ignore all errors of the saves", value=1),
]
)
async def do_get_keystone_key_from_save(ctx: interactions.SlashContext,save_files: str,ignore_errors_in_saves: int):
    await base_do_cheats(ctx,save_files,'1',CheatFunc(get_keystone_key_from_save,{'ignore_errors_in_saves':bool(ignore_errors_in_saves)}))


async def download_icon0_pngs(ftp: aioftp.Client, mount_dir: str, save_name_for_dec_func: str, decrypted_save_ouput: Path,/):
    """
    Save Icon
    """
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    icon0_path: str | None = None
    for path, info in (await ftp.list()): # TODO see if i can just check if a file exists
        if info["type"] != "file":
            continue
        if path.name.casefold() == 'icon0.png':
            icon0_path = path.as_posix()
    
    if not icon0_path:
        (decrypted_save_ouput / 'no_image_found.txt').write_text('No image found for this save')
        return
    
    await ftp.download(icon0_path,decrypted_save_ouput)
@interactions.slash_command(
    name="saves_info",
    description="Get some common infos about saves",
    # group_name="group",
    # group_description="My command group",
    sub_cmd_name="icon_image",
    sub_cmd_description=f"Get the icon0.png image from your saves! (max {MAX_RESIGNS_PER_ONCE} saves per command)",
)
@interactions.slash_option('save_files','The save files you want the icon0.png images of',interactions.OptionType.STRING,True)
@unzip_if_only_one_file_opt
async def do_get_saves_icon_image(ctx: interactions.SlashContext,save_files: str,unzip_if_only_one_file: int):
    await base_do_dec(ctx,save_files,DecFunc(download_icon0_pngs,{}),unzip_if_only_one_file=unzip_if_only_one_file)

@interactions.slash_command(name="my_command", description="My first command :)")
async def my_command_function(ctx: interactions.SlashContext):
    await ctx.defer()
    res = get_amnt_of_helped_people_by_allowing_non_cusa_google_drive_folders()
    new = f' {res}' if res else ''
    await ctx.send("Hello World" + new)


async def param_sfo_info(ftp: aioftp.Client, mount_dir: str, save_name: str,/,show_save_tree: bool) -> NoReturn:
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            info_message = str(PS4SaveParamSfo.from_buffer(f))

    if show_save_tree:
        await ftp.change_directory(mount_dir)
        files = [(path,info) for path, info in (await ftp.list(recursive=True))]
        info_message += '\n\nDirectory Tree\n'
        info_message += '\n'.join(f'{"/" if e[1]["type"] != "file" else ""}' + str(e[0]) + f'{"" if e[1]["type"] != "file" else " // " + pretty_bytes(int(e[1]["size"]))}' for e in files)
    
    raise ExpectedError(info_message.replace('```',r'\x60\x60\x60')) # to prevent discord fucking up formatting

@interactions.slash_command(
    name="saves_info",
    description="Get some common infos about saves",
    # group_name="group",
    # group_description="My command group",
    sub_cmd_name="from_param_sfo",
    sub_cmd_description=f"Print some info of your saves! (max {MAX_RESIGNS_PER_ONCE} saves per command)",
)
@interactions.slash_option('save_files','The save files you want info of',interactions.OptionType.STRING,True)
@interactions.slash_option('show_save_tree','Do you want to see each decrypted file in the save?',interactions.OptionType.BOOLEAN,True)
async def do_param_sfo_info(ctx: interactions.SlashContext,save_files: str,show_save_tree: bool):
    await base_do_cheats(ctx,save_files,'1',CheatFunc(param_sfo_info,{'show_save_tree':show_save_tree}))
############################02


async def re_region(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,gameid: str) -> CheatFuncResult:
    """
    re regioned save
    """
    # is_xenoverse = gameid in XENOVERSE_TITLE_IDS
   
    # if is_xenoverse:
        # seeks = (0x61C,0xA9C,0x9F8)
    # else:
    found_titleids = tuple(m.start() + 0x9F8 for m in CUSA_TITLE_ID.finditer(save_name))
    seeks = PARAM_SFO_REGION_SEEKS + found_titleids
    
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            my_param = PS4SaveParamSfo.from_buffer(f)
        my_param.with_new_region(gameid,seeks)
        tp_param_sfo.write_bytes(bytes(my_param))
        
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
@interactions.slash_command(name="re_region", description=f"Re region your save files! (max {MAX_RESIGNS_PER_ONCE} saves per command)")
@interactions.slash_option('save_files','The save files to be re regioned',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('gameid','The gameid of the region you want, in format CUSAxxxxx',interactions.OptionType.STRING,True,max_length=9,min_length=9)
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

async def change_save_name(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,psstring_new_name: bytes) -> None:
    """
    save with new name in menu
    """
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            my_param = PS4SaveParamSfo.from_buffer(f)
        my_param.with_new_name(psstring_new_name)
        tp_param_sfo.write_bytes(bytes(my_param))
            
        await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)


@interactions.slash_command(name="change_save_name", description=f"Change the name of the save displayed on PS4 menu")
@interactions.slash_option('save_files','The save files to change the name of',interactions.OptionType.STRING,True)
@account_id_opt
@interactions.slash_option('psstring_new_name','the name you want, put hex code for symbols (eg this is a checkmark -> EFA1BE)',interactions.OptionType.STRING,True,min_length=1,max_length=0x80*3)
async def do_change_save_name(ctx: interactions.SlashContext,save_files: str,account_id: str, **kwargs):
    await base_do_cheats(ctx,save_files,account_id,CheatFunc(change_save_name,kwargs))


async def change_save_desc(ftp: aioftp.Client, mount_dir: str, save_name: str,/,*,psstring_new_desc: bytes) -> None:
    """
    save with new name in menu
    """
    desc_before_find = save_name.encode('ascii').ljust(0x20, b'\x00')
    await ftp.change_directory(Path(mount_dir,'sce_sys').as_posix())
    async with TemporaryDirectory() as tp:
        tp_param_sfo = Path(tp,'TEMPPPPPPPPPPparam_sfo')
        await ftp.download('param.sfo',tp_param_sfo,write_into=True)
        with open(tp_param_sfo,'rb+') as f:
            my_param = PS4SaveParamSfo.from_buffer(f)
        my_param.with_new_description(psstring_new_desc)
        tp_param_sfo.write_bytes(bytes(my_param))
        await ftp.upload(tp_param_sfo,'param.sfo',write_into=True)


@interactions.slash_command(name="change_save_desc", description=f"Change the description of the save displayed on PS4 menu")
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

@interactions.slash_command(name="import_littlebigplanet_bigfart",description=f"Import any LittleBigPlanet bigfart to PS4 (just not from Vita)")
@account_id_opt
@interactions.slash_option('dl_link_bigfart','A download link to your bigfart',interactions.OptionType.STRING,True)
@lbp3_reregion_opt
async def do_import_littlebigplanet_bigfart(ctx: interactions.SlashContext, account_id: str, dl_link_bigfart: str, gameid: str):
    await base_do_cheats(ctx,LBP3_EU_BIGFART,account_id,[CheatFunc(import_bigfart,{'dl_link_single':dl_link_bigfart}),CheatFunc(re_region,{'gameid':gameid})])
    
game_enc_functions = { # Relying on the dict ordering here, "Game not here (might not work)" should be at bottom
    'Dying Light 2 Stay Human': upload_dl2_sav_gz_decompressed,
    'Grand Theft Auto V': upload_red_dead_redemption_2_or_gta_v_save,
    'Red Dead Redemption 2': upload_red_dead_redemption_2_or_gta_v_save,
    'DRAGON BALL XENOVERSE 2': upload_xenoverse_2_save,
    'Rayman Legends': rayman_legends_upload_fix_checksum,
    'LittleBigPlanet bigfart (just not from Vita)': import_bigfart,
    'Game not here (might not work)': upload_single_file_any_game,
}


@interactions.slash_command(name="advanced_mode_import",description=f"Import/encrypt your exported/decrypted saves!")
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
        ctx.ezwizard3_special_ctx_attr_special_save_files_thing = SpecialSaveFiles.ONLY_ALLOW_ONE_SAVE_FILES_CAUSE_IMPORT

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
    await ps4.notify('eZwizard3-bot connected!')
    print('eZwizard3-bot connected!')
    if _did_first_boot:
        print(f'took {time.perf_counter() - _boot_start:.1f} seconds to boot')
    _did_first_boot = False
    print('Trying to dm the people')
    await dm_all_at_once(bot)
    print('Done trying to dm the people')

update_status_start = time.perf_counter()
amnt_used_this_session = 0
old_amnt_of_free = 0
BOT_STATUS_GETTING = asyncio.Lock()

async def get_bot_status(*,trunacte_status_text: bool = True) -> tuple[str,interactions.Status]:
    global old_amnt_of_free
    global update_status_start
    global total_runtime
    global _did_first_boot
    async with BOT_STATUS_GETTING:
        amnt_of_free = await get_amnt_free_save_strs()
        
        if await is_bot_completely_free():
            reset_make_folder_name_counter()
        
        leader = 'IN TEST MODE, NO ONE CAN USE BOT! ' if is_in_test_mode() else ''
        
           
        if amnt_of_free != old_amnt_of_free:
            update_status_start = time.perf_counter()
        new_time = pretty_time(time.perf_counter() - update_status_start)
        
        cumulative_up_time = pretty_seconds_words(total_runtime,shorter_text=trunacte_status_text)
        
        if not amnt_of_free:
            status = interactions.Status.DO_NOT_DISTURB
            msg = f'NO slots free {amnt_of_free}/{len(SAVE_DIRS)} for {new_time}, used {amnt_used_this_session} times this session, {get_total_amnt_used()} total. Cumulative uptime: {cumulative_up_time}'
        elif amnt_of_free == len(SAVE_DIRS):
            status = interactions.Status.IDLE
            msg = f'All slots free {amnt_of_free}/{len(SAVE_DIRS)} for {new_time} used {amnt_used_this_session} times this session, {get_total_amnt_used()} total. Cumulative uptime: {cumulative_up_time}'
        else:
            status = interactions.Status.ONLINE
            msg = f'Some slots free {amnt_of_free}/{len(SAVE_DIRS)} for {new_time} used {amnt_used_this_session} times this session, {get_total_amnt_used()} total. Cumulative uptime: {cumulative_up_time}'
        
        bot_status_text = leader+msg
        
        if trunacte_status_text and len(bot_status_text) > DISCORD_BOT_STATUS_MAX_LENGTH:
            bot_status_text = bot_status_text[:DISCORD_BOT_STATUS_MAX_LENGTH] + '...'
        
        old_amnt_of_free = amnt_of_free
    
        return bot_status_text,status


@interactions.Task.create(interactions.IntervalTrigger(seconds=30)) # TODO do not hardcode the 30
async def _update_status():
    global total_runtime
    if (not is_in_test_mode()) and (not _did_first_boot):
        total_runtime += 30 # TODO do not hardcode the 30
        set_total_runtime(total_runtime)
    await update_status()
async def update_status():
    bot_status_text,status = await get_bot_status()
    await bot.change_presence(activity=interactions.Activity.create(
                                name=bot_status_text),
                                status=status)

@interactions.slash_command(name="get_bot_status",description="Gets some info about the bot")
async def do_get_bot_status(ctx: interactions.SlashContext):
    await ctx.defer()
    bot_status_text,_ = await get_bot_status(trunacte_status_text=False)
    await ps4_life_check(ctx)
    await ctx.send(f'bot latency is {ctx.bot.latency * 1000:.2f}ms\n' + bot_status_text)
    await ctx.send(await ezwizard3_info())
    
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
        await log_user_error(ctx,f'Not a valid psn name {psn_name}, check it again!')
        return
        
    await log_message(ctx,f'Looking for psn name {psn_name}')
    try:
        user = psnawp.user(online_id=psn_name)
    except PSNAWPNotFound:
        await log_user_error(ctx,f'Could not find psn name {psn_name}, perhaps you mispelled it?')
        return
    account_id_hex = PS4AccountID.from_account_id_number(user.account_id).account_id
    
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


@interactions.slash_command(name="ping",description="Test if the bot is responding")
async def ping_test(ctx: interactions.SlashContext):
    await ctx.defer()
    await ps4_life_check(ctx)
    cool_ping_msg = f'<@{ctx.author_id}> Pong! bot latency is {ctx.bot.latency * 1000:.2f}ms\n**Want to get DMed by the bot when it goes online? If so, run the `/dm_me_when_online` command**'
    
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_DMS}'
    if is_in_test_mode():
        if is_user_bot_admin(ctx.author_id):
            cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_TEST_MODE} but you can as you\'re a bot admin!'
        else:
            cool_ping_msg = f'{cool_ping_msg} but {CANT_USE_BOT_IN_TEST_MODE}'
        
    await ctx.send(cool_ping_msg,ephemeral=False)
    if CONFIG['should_ping_command_show_git_stuff']:
        await ctx.send(await ezwizard3_info())

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


@interactions.slash_command(name='see_built_in_sabes',description="See all of the built in saves/dl_link files of this instance")
@interactions.slash_option(
    name="show",
    description='Do you want to see built in encrypted saves or dl_link',
    required=True,
    opt_type=interactions.OptionType.STRING,
    choices=[
        interactions.SlashCommandChoice(name="Built in encrypted saves", value='built_in_save_links'),
        interactions.SlashCommandChoice(name="Built in dl_links (NOT encrypted saves)", value='built_in_dl_links'),
    ]
    )
async def see_built_in_sabes(ctx: interactions.SlashContext, show: str):
    ctx = await set_up_ctx(ctx)

    if is_in_test_mode() and not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,CANT_USE_BOT_IN_TEST_MODE)
        return
    if (not CONFIG['allow_bot_usage_in_dms']) and (not ctx.channel):
        await log_user_error(ctx,CANT_USE_BOT_IN_DMS)
        return

    await log_user_success(ctx,'\n'.join(f'{i}: {x[1]}' for i,x in enumerate(CONFIG[show])))

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

@interactions.slash_command(name='toggle_test_mode',description="Toggle test mod on and off (only bot admins can use bot)")
async def do_toggle_test_mode(ctx: interactions.SlashContext):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        await log_user_error(ctx,'Only bot instance admins may use this command')
        return


    if toggle_test_mode_bool():
        await log_user_success(ctx,'Test mode turned on, only bot admins can use bot now')
    else:
        await log_user_success(ctx,'Test mode turned off, people can use the bot now')
    
    return


@interactions.slash_command(name='delete_all_google_drive_saves',description="Only run this command if the gdrive is full, will delete all gdrive files bot has given to users")
async def delete_ezwizardtwo_saves_folder(ctx: interactions.SlashContext):
    global UPLOAD_SAVES_FOLDER_ID
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command, please ask one to run this command if google drive is full')


    await delete_google_drive_file_or_file_permentaly(UPLOAD_SAVES_FOLDER_ID)
    UPLOAD_SAVES_FOLDER_ID = await make_gdrive_folder('ezwizardtwo_saves')
    return await log_user_success(ctx,'All saves deleted successfully')


@interactions.slash_command(name='delete_certain_gdrive_save',description="Only run this command if the gdrive is full, will delete a certain google drive file sent by bot")
@interactions.slash_option(
    name="gdrive_url_from_bot",
    description="A google drive link the bot has given",
    required=True,
    opt_type=interactions.OptionType.STRING,
    )
async def do_delete_certain_gdrive_save(ctx: interactions.SlashContext, gdrive_url_from_bot: str):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command, please ask one to run this command if google drive is full')

    gdrive_url_from_bot_id = extract_drive_file_id(gdrive_url_from_bot)
    
    if not gdrive_url_from_bot_id:
        return await log_user_error(ctx,f'{gdrive_url_from_bot} is not a valid google drive link, please copy the exact link the bot sent')
    
    try:
        a = await get_file_info_from_id(gdrive_url_from_bot_id)
    except Exception as e:
        msg = make_error_message_if_verbose_or_not(ctx.author_id,f'Could not get file metadata from {gdrive_url_from_bot}','')
        return await log_user_error(ctx,msg)

    try:
        await delete_google_drive_file_or_file_permentaly(gdrive_url_from_bot_id)
    except Exception:
        return await log_user_error(ctx,f'Could not delete {gdrive_url_from_bot}, are you sure its from the same bot as you running this command?')
    
    await log_user_success(ctx,f'Deleted {gdrive_url_from_bot} successfully')
    
setting_global_image_lock = asyncio.Lock()
@interactions.slash_command(name='set_global_watermark',description="Allows a bot instance admin to set a global watermark to all saves icons")
@interactions.slash_option(
    name="global_image_link",
    description="A direct download to your image, will be saved to current dir",
    required=True,
    opt_type=interactions.OptionType.STRING,
    )
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
async def do_global_image_link(ctx: interactions.SlashContext, global_image_link: str, option: int):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    async with setting_global_image_lock:
        if is_str_int(global_image_link) and int(global_image_link) > 1:
            try:
                global_image_link = get_saved_url(ctx.author_id,int(global_image_link))
            except KeyError:
                await log_user_error(ctx,f'You dont have any url saved for {global_image_link}, try running the file2url command again!')
                return False
        global_image_link = get_dl_link_if_desc(global_image_link)
        await log_message(ctx,f'Downloading {global_image_link}')
        async with TemporaryDirectory() as tp:
            result = await download_direct_link(ctx,global_image_link,tp,max_size=DL_FILE_TOTAL_LIMIT)
            if isinstance(result,str):
                await log_user_error(ctx,result)
                return False
            try:
                with Image.open(result) as img:
                    pass
            except Exception:
                return await log_user_error(ctx,f'{global_image_link} is not a valid image, please give a image link')
            
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


@interactions.slash_command(name='ban_user_from_bot',description="Bans a discord user from using most commands")
@interactions.slash_option(
    name="offending_user",
    description="The discord user to ban from using the bot",
    required=True,
    opt_type=interactions.OptionType.USER,
    )
@interactions.slash_option(
    name="reason",
    description="Why was the discord user banned from using the bot?",
    required=True,
    opt_type=interactions.OptionType.STRING,
    )
async def do_ban_user_from_bot(ctx: interactions.SlashContext, offending_user: interactions.Member | interactions.User, reason: str):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    add_user_id_to_ban_list(offending_user.id,reason)

    await log_message(ctx,'Checking offending_user account id')
    pretty_thing_account_idk = ''
    account_id_for_db: str | PS4AccountID = account_id_from_str('0',offending_user.id,ctx)
    if isinstance(account_id_for_db,PS4AccountID):
        add_account_id_to_ban_list(account_id_for_db, offending_user.id)
        pretty_thing_account_idk = f' and account id {account_id_for_db.account_id}'
        
    await log_user_success(ctx,f'<@{offending_user.id}>{pretty_thing_account_idk} was banned from using the bot, reason:\n\n{reason}')


@interactions.slash_command(name='is_user_banned_from_bot',description="Check if a user is banned from using the bot")
@interactions.slash_option(
    name="user_to_check",
    description="The discord user to check if banned from using the bot",
    required=True,
    opt_type=interactions.OptionType.USER,
    )
async def do_is_user_banned(ctx: interactions.SlashContext, user_to_check: interactions.Member | interactions.User):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    ban_reason = is_user_id_in_ban_list(user_to_check.id)
    if not ban_reason:
        await log_user_error(ctx,f'<@{user_to_check.id}> is not banned')
    else:
        await log_user_success(ctx,f'<@{user_to_check.id}> was banned from using the bot, reason:\n\n{ban_reason}')


@interactions.slash_command(name='unban_user_from_bot',description="Unbans a user")
@interactions.slash_option(
    name="user_to_unban",
    description="The discord user to unban",
    required=True,
    opt_type=interactions.OptionType.USER,
    )
async def do_unban_user_from_bot(ctx: interactions.SlashContext, user_to_unban: interactions.Member | interactions.User):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    ban_reason = is_user_id_in_ban_list(user_to_unban.id)
    if not ban_reason:
        await log_user_error(ctx,f'<@{user_to_unban.id}> is not banned')
        return
    remove_user_id_to_ban_list(user_to_unban.id)
    await log_user_success(ctx,f'<@{user_to_unban.id}> was unbanned from using the bot')


@interactions.slash_command(name='ban_account_id_from_bot',description="Bans a certain psn account id from using the bot")
@interactions.slash_option(
    name="offending_user",
    description="The discord user that owns the account id",
    required=True,
    opt_type=interactions.OptionType.USER,
    )
@account_id_to_ban_opt
async def do_ban_account_id_from_bot(ctx: interactions.SlashContext, offending_user: interactions.Member | interactions.User, account_id: str):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    await log_message(ctx,'Checking if the offending_user is banned')
    ban_reason = is_user_id_in_ban_list(offending_user.id)
    if not ban_reason:
        await log_user_error(ctx,f'<@{offending_user.id}> is not banned, you need to link the account id to a banned discord user!')
        return
    
    await log_message(ctx,'Checking account_id')
    account_id_for_db: str | PS4AccountID = account_id_from_str(account_id,offending_user.id,ctx)
    if isinstance(account_id_for_db,str):
        await log_user_error(ctx,account_id_for_db)
        return
    
    add_account_id_to_ban_list(account_id_for_db, offending_user.id)
    await log_user_success(ctx,f'Account id {account_id_for_db.account_id} ({account_id}), owned by <@{offending_user.id}> was banned from using the bot')
    
    
@interactions.slash_command(name='is_account_id_banned_from_bot',description="Check if a psn account id is banned from using the bot")
@account_id_to_ban_opt
async def do_account_id_banned(ctx: interactions.SlashContext, account_id: str):
    ctx = await set_up_ctx(ctx)

    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')
    
    await log_message(ctx,'Checking account_id')
    account_id_for_db: str | PS4AccountID = account_id_from_str(account_id,ctx.author_id,ctx)
    if isinstance(account_id_for_db,str):
        await log_user_error(ctx,account_id_for_db)
        return
    
    pretty_account_id_show = f'Account id {account_id_for_db.account_id} ({account_id}),'
    
    ban_reason = is_account_id_in_ban_list(account_id_for_db)
    if not ban_reason:
        await log_user_error(ctx,f'{pretty_account_id_show} is not banned')
    else:
        await log_user_success(ctx,f'{pretty_account_id_show} owned by <@{ban_reason}> is banned, use `is_user_banned_from_bot` to see reason')


@interactions.slash_command(name='unban_account_id_from_bot',description="Unbans a psn account id")
@account_id_to_ban_opt
async def do_unban_account_id_from_bot(ctx: interactions.SlashContext, account_id: str):
    ctx = await set_up_ctx(ctx)
    if not is_user_bot_admin(ctx.author_id):
        return await log_user_error(ctx,'Only bot instance admins may use this command')

    await log_message(ctx,'Checking account_id')
    account_id_for_db: str | PS4AccountID = account_id_from_str(account_id,ctx.author_id,ctx)
    if isinstance(account_id_for_db,str):
        await log_user_error(ctx,account_id_for_db)
        return
    
    pretty_account_id_show = f'Account id {account_id_for_db.account_id} ({account_id}),'
    
    ban_reason = is_account_id_in_ban_list(account_id_for_db)
    if not ban_reason:
        await log_user_error(ctx,f'{pretty_account_id_show} is not banned')
        return
    remove_user_id_to_ban_list(account_id_for_db.account_id)
    await log_user_success(ctx,f'{pretty_account_id_show} owned by <@{ban_reason}> was unbanned from using the bot')


async def base_saved_ting_autocomplete(ctx: interactions.AutocompleteContext,thing: tuple[tuple[str,str]],/):
    string_option_input = ctx.input_text
    if not string_option_input:
        return await ctx.send(choices=[{'name':'Please start typing a built in save from /see_built_in_sabes','value':'Please start typing a built in save from /see_built_in_sabes'}])
    string_option_input = string_option_input.casefold()

    return await ctx.send(choices=[dict(name=x[1], value=x[0]) for x in thing if string_option_input in x[1].casefold()][:25])


BASE_ENC_SAVES_AUTO_STR = 'async def replacewithrealfuncname_base_saved_enc_saves_autocomplete(ctx: interactions.AutocompleteContext): return await base_saved_ting_autocomplete(ctx,BUILT_IN_SAVE_LINKS)\n'
BASE_ENC_SAVES_AUTO_STR_NAME = 'replacewithrealfuncname_base_saved_enc_saves_autocomplete'

BASE_DL_LINKS_AUTO_STR = 'async def replacewithrealfuncname_base_saved_dl_tings_autocomplete(ctx: interactions.AutocompleteContext): return await base_saved_ting_autocomplete(ctx,BUILT_IN_DL_LINKS)\n'
BASE_DL_LINKS_AUTO_STR_NAME = 'replacewithrealfuncname_base_saved_dl_tings_autocomplete'


quick_commands_base = interactions.SlashCommand(name="quick", description="Versions of commands with choices for save_files and dl_links chosen by bot owner")
quick_cheats_commands_base = interactions.SlashCommand(name="quick_cheats", description="Versions of commands with choices for save_files and dl_links chosen by bot owner")

BUILT_IN_DL_LINKS = tuple((desc[1],desc[1]) for i,desc in enumerate(CONFIG['built_in_dl_links'])) # TODO, dont rely on this lol
BUILT_IN_SAVE_LINKS = tuple((desc[1],desc[1]) for i,desc in enumerate(CONFIG['built_in_save_links'])) # TODO, dont rely on this lol

if __name__ == '__main__':
    print('making the /quick commands')

def _make_quick_functions():
    from inspect import getsource
    from copy import copy
    from interactions import SlashCommand
    global quick_commands_base
    old_repr = interactions.OptionType.__repr__
    interactions.OptionType.__repr__ = lambda self: f'interactions.OptionType({self.value})' # weve gotta do this as the current repr of enums is not valid python code
    

    globals_thing = copy(globals()).items()
    for global_var_name,global_var_value in globals_thing:
        if not isinstance(global_var_value,interactions.models.internal.application_commands.SlashCommand):
            continue
        # as far as im aware, a command will only have options, as well as the function body, which ill use exec for
        thing_dict = global_var_value.to_dict()
        options = thing_dict.get('options')
        if not options:
            continue

        if 'saves_info' == str(global_var_value.name):
            continue
        
        if str(global_var_value.group_name) == 'littlebigplanet_3' and str(global_var_value.to_dict().get("name")) == 'install_mods':
            continue
        
        decor_options: str | list = []
        auto_complete_things_dl_links: str | list = []
        auto_complete_things_enc_saves: str | list = []

        is_viable = False
        for option in options:
            option.pop('description_localizations') # theese seems to be some internal thing, slash_option doesnt accept them
            option.pop('name_localizations') # ^
            option['opt_type'] = option.pop('type')
                        
            if option['name'].startswith('dl_link') or option['name'] in ('decrypted_save_file','decrypted_save_folder','global_image_link'):
                is_viable = True
                if len(BUILT_IN_DL_LINKS) > 0: # Force always use autocorrect to allow users to copy and paste urls too
                    auto_complete_things_dl_links.append((f'@replacewithrealfuncname.autocomplete({option["name"]!r})\n',option["name"]))
                else:
                    option['choices'] += [dict(name=x[1],value=x[0]) for x in BUILT_IN_DL_LINKS]
            if option['name'] == 'save\x5ffiles':
                is_viable = True
                if len(BUILT_IN_SAVE_LINKS) > 0: # Force always use autocorrect to allow users to copy and paste urls too
                    auto_complete_things_enc_saves.append((f'@replacewithrealfuncname.autocomplete({option["name"]!r})\n',option["name"]))
                else:
                    option['choices'] += [dict(name=x[1],value=x[0]) for x in BUILT_IN_SAVE_LINKS]
            
            
            
            decor_options.append(f'@interactions.slash_option(**{option!r})\n')
        if not is_viable:
            continue
        decor_options = ''.join(decor_options)
        
        new_func_name = f'do_quick_auto_gened_code_{0}'
        for i in range(0,0xFFFFFFFF):
            try:
                globals()[new_func_name]
                new_func_name = f'do_quick_auto_gened_code_{i}'
            except KeyError:
                break
        else: # nobreak
            raise AssertionError('nah wtf')
        base_name = 'quick_cheats_commands_base' if str(global_var_value.name) == 'cheats' else 'quick_commands_base' # TODO, implement checks if another possible base comamnd besides `cheats` exists
        base_two = f'umm = {base_name}.group(name={str(global_var_value.group_name)!r}, description={str(global_var_value.group_description)!r})' if global_var_value.group_name else 'umm = umm'
        
        payload_func = f"""
global {new_func_name}
umm = {base_name}
{base_two}
@umm.subcommand(sub_cmd_name={str(global_var_value.to_dict()["name"])!r}, sub_cmd_description={str(global_var_value.to_dict()["description"])!r})
{decor_options}
async def {getsource(global_var_value.callback).split('async def ')[1]}
""".replace(global_var_name,new_func_name)
        payload_func_2 = ''
        payload_func_3 = ''
        if auto_complete_things_dl_links:
            payload_func_2 = f"""
{''.join('global ' + x[1]+BASE_DL_LINKS_AUTO_STR_NAME+chr(0x0A) for x in auto_complete_things_dl_links)}
{''.join(x[0] + BASE_DL_LINKS_AUTO_STR for x in auto_complete_things_dl_links)}
""".replace('replacewithrealfuncname',new_func_name)
        if auto_complete_things_enc_saves:
            payload_func_3 = f"""
{''.join('global ' + x[1]+BASE_ENC_SAVES_AUTO_STR_NAME+chr(0x0A) for x in auto_complete_things_enc_saves)}
{''.join(x[0] + BASE_ENC_SAVES_AUTO_STR for x in auto_complete_things_enc_saves)}
""".replace('replacewithrealfuncname',new_func_name)
        if 1:#global_var_name == 'do_change_save_icon':
            exec(payload_func)
            # print(payload_func_3) if global_var_name == 'do_raw_decrypt_folder' else None
            exec(payload_func_2)
            exec(payload_func_3)
            if __name__ == '__main__':
                pass
                # print(f'Made quick version of {global_var_value.to_dict()["name"]}')

    interactions.OptionType.__repr__ = old_repr # See, im not that insane
    
    
_make_quick_functions()
del _make_quick_functions # we use a function in order to not polute the globals
 
if __name__ == '__main__':
    print('done making the /quick commands')


async def main(turn_on_bot: bool = True, patched_memory_object = None, print_function = print) -> int:
    print = print_function
    
    check_base_saves = not is_in_fast_boot_mode()
    global GIT_EXISTS
    GIT_EXISTS = False
    
    global psnawp
    print('Checking if npsso cookie is valid')
    psnawp = PSNAWP(CONFIG["ssocookie"])
    user = psnawp.user(online_id='Zhaxxy')
    print('npsso cookie works!')
    
    
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
        print('WARNING!: fast boot (-r flag) is set, make sure you are not testing mounting and unmounting with this off')
    
    print('initialising database')
    initialise_database()
    print('done initialising database')
    
    print('Patching memory')
    global mem
    global bot
    async with PatchMemoryPS4900(ps4,ps4_fw_version) if (patched_memory_object is None) else nullcontext() as mem:
        if patched_memory_object:
            mem = patched_memory_object
        if check_base_saves:
            print('Memory patched, ensuring all base saves exist!')
            for eeeee in SAVE_DIRS:
                async with MountSave(ps4,mem,int(CONFIG['user_id'],16),BASE_TITLE_ID,eeeee,blocks=32768) as mp:
                    if not mp:
                        raise ValueError(f'broken base save {eeeee}, reason: {mp.error_code} ({ERROR_CODE_LONG_NAMES.get(mp.error_code,"Missing Long Name")})')
        print('done checking!')
        if turn_on_bot:
            print('turning on bot...')
            bot = interactions.Client(token=CONFIG['discord_token'])
            bot.load_extension("title_id_lookup_commands")
            await bot.astart()
    return 0 

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
