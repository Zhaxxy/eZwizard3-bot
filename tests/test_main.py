from pathlib import Path
import asyncio
import zlib
import sys

import pytest

import main

try:
    __file__ = sys._MEIPASS
except:
    pass
else:
    __file__ = str(Path(__file__) / 'huh.huh')

pytest_plugins = ('pytest_asyncio',)


DECOMP_PARAM_SFO = zlib.decompress(b'x\xdac\x08\x08vcdd`\xb8\xc2\xc0\xc0\x10\x03\xa4y\x18@\x80\x85\x81\x03Hr0@\x007\x03\x0b\x0b\x0bX\x14"&\xca\xc0\xc2\xc4\x0c\xe5\x83\xd4\xcb\x01\xf9Z\x10m\x0c\x02@J\x15I^\x00H\xe8\x00\xf9\xc2@v\x03\x10\x8b\x00\xf9f \x19\xa8\x81S\x80\xd8\x16\xc9\xbe)@\xc2\x17\xa8\x9e\x17\xc8V\x00\xe29@~\x02\x92\xfd{\x80\xfc\x12\xa0<#\xd4\xbc\x03@~-\x90\xcf\x05u\x8b\x03\'\x03\x83\xa3\xb3\xb3\x7f\xa8_H\xbc\xa7\x0b\x83cHH\x90\xa7Sh\x88+\x83\xb3c\x88\xab\xbb\x7fP$\x83\x8bk\x88\xa3\xa7\x0f\x83\x9b\x7f\x90\xafc\x08\x83\xaf\xa3\xa7_\x88g\x88\x8f+C\x80c\x90\xa3o0C\xb0c\x98\xab\x8bc\x88c\xbc\x93\x8f\xbf\xb37\x12\xdf\xc53\xc8\xd59\x04d\x02\\\xc8\xc738$\x1e\xac\x8f!8\xd4\tb\x0c\x98\x04Y\xcd\xc0\xa0\xe7\xb4e\xd3\xc7\xa4<7P\xd0\x14\xa700\x04G\xfa9{\x04\xf9\xfb\x05{\xba\x06\x85\xfa\xb9[)\x98\x9b\xabr\x05\x07x\xba\xfaD\xb9z\x86X)\x18\x99X\x19\x99[\x19\x1ar1\x8c\x82Q0\n\x86\x1b\xc8O*fpO-.H\xcdL\xceH-*IUpI,I\xcd\xa3\xbf;:\xefIH\xacl\x8f3\xdej\x7fE`\xae\xb2n\xc2\x87\xb6\x07K\xec\x8b?\x9f\xad\xbe\xcf\xf1I\xeaay\xd4\xc2\xc4\xd9?A\xe5\xabsh\xb0\xa3\x81\x91\xb1\xb9\x19T\x1f:\x7f\x073\xaa\xb9L@,\xefs.\x12\xc4f5\xbb\x199\x1a\xe3\xa3`\x14\x0c.\x90\x00\xa5\x8b\x93S\xe3\x8bSrSs\xf3\x8b*\x07\xab[\x91\xcb\x1b\x00\x88Hh\x90')

@pytest.mark.asyncio
async def test_ftp_mounts():
    possible_save_points = [x for save in main.CONFIG['save_dirs'] for x in (f'{save}.bin', f'sdimg_{save}')]
    async with main.aioftp.Client.context(main.CONFIG['ps4_ip'],2121) as ftp:
        await ftp.change_directory(main.SAVE_FOLDER_ENCRYPTED)
        for path, info in await ftp.list():
            if not path.name in possible_save_points or info['type'] != 'file': continue
            if path.suffix == '.bin':
                assert int(info["size"]) == 96, f'Invalid bin file {path.name}'
            possible_save_points.remove(path.name)
        
    assert not [save[:-4] for save in possible_save_points if save.endswith('.bin')], 'missing ftp save dirs on PS4'


async def ftp_mount_save_ftp_dir(mem,ps4,save_ftp_dir: str):
    async with main.MountSave(ps4,mem,int(main.CONFIG['user_id'],16),main.CONFIG['title_id'],save_ftp_dir) as mp, main.mounted_saves_at_once:
        assert mp
        async with main.aioftp.Client.context(main.CONFIG['ps4_ip'],2121) as ftp:
            await ftp.change_directory((main.MOUNTED_POINT / mp.savedatax / 'sce_sys').as_posix())
            async with main.TemporaryDirectory() as tp:
                param_sfo = Path(tp,'param.sfo')
                await ftp.download('param.sfo',tp)
                assert param_sfo.read_bytes() == DECOMP_PARAM_SFO


@pytest.mark.asyncio
async def test_ftp_mounts_mounting():
    real_bin = Path(__file__).parent / 'helper_test_data_files/CUSA02376/sce_sdmemory.bin'
    real_white = Path(__file__).parent / 'helper_test_data_files/CUSA02376/sce_sdmemory'
    async with main.aioftp.Client.context(main.CONFIG['ps4_ip'],2121) as ftp:
        await ftp.change_directory(main.SAVE_FOLDER_ENCRYPTED)
        for save in main.CONFIG['save_dirs']:
            await ftp.upload(real_bin,f'{save}.bin',write_into=True)
            await ftp.upload(real_white,f'sdimg_{save}',write_into=True)

    await main.send_ps4debug(main.CONFIG['ps4_ip'])
    ps4 = main.PS4Debug(main.CONFIG['ps4_ip'])
    async with main.PatchMemoryPS4900(ps4) as mem:
        for save_ftp_dir in main.CONFIG['save_dirs']:
            await ftp_mount_save_ftp_dir(mem,ps4,save_ftp_dir)
