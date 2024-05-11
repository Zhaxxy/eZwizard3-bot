import asyncio
from pathlib import Path
from io import StringIO
from typing import NamedTuple, Literal
from os import getcwd

class SevenZipFile(NamedTuple):
    path: Path
    size: int
    is_file: bool


class SevenZipInfo(NamedTuple):
    files: dict[Path,SevenZipFile]
    total_uncompressed_size: int

    
SEVEN_ZIP_ARGS = ('7z',)
VALID_7Z_EXTENSIONS = frozenset(('.7z', '.xz', '.bzip2', '.gzip', '.tar', '.zip', '.wim', '.apfs', '.ar', '.arj', '.cab', '.chm', '.cpio', '.cramfs', '.dmg', '.ext', '.fat', '.gpt', '.hfs', '.ihex', '.iso', '.lzh', '.lzma', '.mbr', '.msi', '.nsis', '.ntfs', '.qcow2', '.rar', '.rpm', '.squashfs', '.udf', '.uefi', '.vdi', '.vhd', '.vhdx', '.vmdk', '.xar', '.z'))

def test_7z():
    global SEVEN_ZIP_ARGS
    import subprocess
    try:
        res = subprocess.run(SEVEN_ZIP_ARGS,capture_output=True)
    except FileNotFoundError:
        SEVEN_ZIP_ARGS = ('C:/Program Files/7-Zip/7z.exe',)
        try:
            res = subprocess.run(SEVEN_ZIP_ARGS,capture_output=True)
        except FileNotFoundError:
            raise FileNotFoundError('7z is not on the PATH, ethier edit the SEVEN_ZIP_ARGS constant to the path to 7z.exe or install 7zip propley') from None

    if res.returncode:
        raise Exception(f'something went wrong with 7zip... {res.stderr}')
    res_stdout = res.stdout.decode("utf-8").replace("\r\n","\n")
    try:
        version = res_stdout.split('\n')[1].split(' ')[1]
    except IndexError:
        raise Exception(f'Could not parse output from 7z (7zip) {res_stdout}')
    if version != '23.01':
        raise Exception(f'Too new or old of a 7zip version {version} should be 23.01')
test_7z()

async def get_archive_info(path_to_archive: Path | str) -> SevenZipInfo:
    proc = await asyncio.create_subprocess_exec(
       *SEVEN_ZIP_ARGS,
        'l','-ba','-slt',path_to_archive,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    stdout, stderr = stdout.decode('utf-8').replace('\r\n','\n'), stderr.decode('utf-8').replace('\r\n','\n')
    if stderr or proc.returncode:
        raise Exception(f'bad zip file? error code {proc.returncode} error: {stderr}{stdout}')
    
    files = {}
    total_uncompressed_size = 0
    for entry in stdout.split('\n\n'):
        is_file = None
        if not entry.startswith('Path = '): continue
        for thing in entry.split('\n'):
            if thing.startswith('Path = '):
                path = Path(thing.split('Path = ')[1])
            if thing.startswith('Size = '):
                path_size = int(thing.split('Size = ')[1])
            if thing.startswith('Folder = '):
                is_folder_raw = thing.split('Folder = ')[1]
                assert is_folder_raw in ('-','+')
                is_file = True if is_folder_raw == '-' else False
        if is_file is None: # fall back to size method
            is_file = bool(path_size)
        files[path] = SevenZipFile(path,path_size,is_file)
        total_uncompressed_size += path_size
    
    return SevenZipInfo(files,total_uncompressed_size)


async def extract_single_file(path_to_archive: Path | str, name_of_file: Path | str, output_loc: Path | str = '', command: Literal['e'] | Literal['x'] = 'e'):
    output_loc = output_loc or getcwd()
    proc = await asyncio.create_subprocess_exec(
       *SEVEN_ZIP_ARGS,
        command,path_to_archive,name_of_file,f'-o{output_loc}',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    stdout, stderr = stdout.decode('utf-8').replace('\r\n','\n'), stderr.decode('utf-8').replace('\r\n','\n')
    if stderr or proc.returncode:
        raise Exception(f'bad zip file? error code {proc.returncode} error: {stderr}{stdout}')
    
    if 'No files to process\n' in stdout:
        raise Exception(f'did not find {name_of_file} in the thing')

def filename_valid_extension(filename: Path | str) -> str:
    """
    from https://www.7-zip.org/
    """
    extension = Path(filename).suffix.casefold()
    if extension in VALID_7Z_EXTENSIONS:
        return ''
    else:
        return f'{filename}\'s extension {extension} is not a valid archive'

"""    
async def main():
    await extract_single_file('a.rar',r'PS4\SAVEDATA\4bacdde2acfa85ba\CUSA00473\LBPxSAVE.bin')
    

if __name__ == "__main__":
    asyncio.run(main())
"""
