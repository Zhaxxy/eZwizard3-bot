from threading import Lock
import struct
from dataclasses import dataclass
from typing import NamedTuple, Tuple

from ps4debug import PS4Debug

SUPPORTED_MEM_PATCH_FW_VERSIONS = (
    9,
    # 11 # Unconfirmed 11.00, need to test, it did fail on the one test i didnt, likley a silly mistake
)

class Of_Offsets:
    sceSaveDataInitialize3 = 0x00027FA0
    sceUserServiceGetUserName = 0x000045A0
    sceUserServiceGetLoginUserIdList = 0x00002C00
    sceSaveDataMount = 0x00028130
    sceSaveDataUmount = 0x000288E0
    sceUserServiceGetInitialUser = 0x000033C0

class Fu_Functions:
    GetSaveDirectories = bytes([
        0x55, 0x48, 0x89, 0xE5, 0x48, 0x83, 0xEC, 0x50, 0x48, 0x89, 0x7D, 0xB8, 0x48, 0x89, 0x75, 0xB0, 0x48,
        0xB8, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0x48, 0x89, 0x45, 0xE8, 0x48, 0xB8, 0xBB, 0xBB,
        0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0x48, 0x89, 0x45, 0xE0, 0x48, 0xB8, 0xCC, 0xCC, 0xCC, 0xCC, 0xCC,
        0xCC, 0xCC, 0xCC, 0x48, 0x89, 0x45, 0xD8, 0x48, 0xB8, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD, 0xDD,
        0x48, 0x89, 0x45, 0xD0, 0x48, 0x8B, 0x55, 0xB8, 0x48, 0x8B, 0x45, 0xE8, 0x48, 0x89, 0xD7, 0xFF, 0xD0,
        0x48, 0x89, 0x45, 0xC8, 0x48, 0x83, 0x7D, 0xC8, 0x00, 0x75, 0x0A, 0xB8, 0xFF, 0xFF, 0xFF, 0xFF, 0xE9,
        0x88, 0x00, 0x00, 0x00, 0x48, 0x8B, 0x55, 0xC8, 0x48, 0x8B, 0x45, 0xE0, 0x48, 0x89, 0xD7, 0xFF, 0xD0,
        0x48, 0x89, 0x45, 0xF8, 0xC7, 0x45, 0xF4, 0x00, 0x00, 0x00, 0x00, 0x48, 0x83, 0x7D, 0xF8, 0x00, 0x74,
        0x59, 0x48, 0x8B, 0x45, 0xF8, 0x0F, 0xB6, 0x40, 0x06, 0x3C, 0x04, 0x75, 0x3A, 0x48, 0x8B, 0x45, 0xF8,
        0x0F, 0xB6, 0x40, 0x07, 0x3C, 0x09, 0x75, 0x2E, 0x48, 0x8B, 0x45, 0xF8, 0x48, 0x8D, 0x48, 0x08, 0x8B,
        0x55, 0xF4, 0x89, 0xD0, 0xC1, 0xE0, 0x02, 0x01, 0xD0, 0x01, 0xC0, 0x48, 0x63, 0xD0, 0x48, 0x8B, 0x45,
        0xB0, 0x48, 0x01, 0xC2, 0x48, 0x8B, 0x45, 0xD0, 0x48, 0x89, 0xCE, 0x48, 0x89, 0xD7, 0xFF, 0xD0, 0x83,
        0x45, 0xF4, 0x01, 0x48, 0x8B, 0x55, 0xC8, 0x48, 0x8B, 0x45, 0xE0, 0x48, 0x89, 0xD7, 0xFF, 0xD0, 0x48,
        0x89, 0x45, 0xF8, 0xEB, 0xA0, 0x48, 0x8B, 0x55, 0xC8, 0x48, 0x8B, 0x45, 0xD8, 0x48, 0x89, 0xD7, 0xFF,
        0xD0, 0x8B, 0x45, 0xF4, 0xC9, 0xC3
    ])
    
    GetUsers = bytes([
        0x55, 0x48, 0x89, 0xE5, 0x48, 0x83, 0xEC, 0x70, 0x48, 0x89, 0x7D, 0x98, 0xC7, 0x45, 0xFC, 0x00, 0x00, 0x00,
        0x00, 0x48, 0xB8, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0x48, 0x89, 0x45, 0xF0, 0x48, 0xB8, 0xBB,
        0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0x48, 0x89, 0x45, 0xE8, 0x48, 0xB8, 0xCC, 0xCC, 0xCC, 0xCC, 0xCC,
        0xCC, 0xCC, 0xCC, 0x48, 0x89, 0x45, 0xE0, 0x48, 0x8D, 0x55, 0xC0, 0x48, 0x8B, 0x45, 0xF0, 0x48, 0x89, 0xD7,
        0xFF, 0xD0, 0x89, 0x45, 0xDC, 0x83, 0x7D, 0xDC, 0x00, 0x74, 0x0A, 0xB8, 0xFF, 0xFF, 0xFF, 0xFF, 0xE9, 0xB4,
        0x00, 0x00, 0x00, 0xC7, 0x45, 0xF8, 0x00, 0x00, 0x00, 0x00, 0x83, 0x7D, 0xF8, 0x03, 0x0F, 0x8F, 0xA0, 0x00,
        0x00, 0x00, 0x8B, 0x45, 0xF8, 0x48, 0x98, 0x8B, 0x44, 0x85, 0xC0, 0x85, 0xC0, 0x0F, 0x8E, 0x86, 0x00, 0x00,
        0x00, 0x8B, 0x45, 0xF8, 0x48, 0x98, 0x8B, 0x4C, 0x85, 0xC0, 0x48, 0x8D, 0x75, 0xA0, 0x48, 0x8B, 0x45, 0xE8,
        0xBA, 0x11, 0x00, 0x00, 0x00, 0x89, 0xCF, 0xFF, 0xD0, 0x89, 0x45, 0xDC, 0x83, 0x7D, 0xDC, 0x00, 0x74, 0x07,
        0xB8, 0xFF, 0xFF, 0xFF, 0xFF, 0xEB, 0x68, 0x8B, 0x55, 0xF8, 0x89, 0xD0, 0xC1, 0xE0, 0x02, 0x01, 0xD0, 0xC1,
        0xE0, 0x02, 0x01, 0xD0, 0x48, 0x98, 0x48, 0x8D, 0x14, 0x85, 0x00, 0x00, 0x00, 0x00, 0x48, 0x8B, 0x45, 0x98,
        0x48, 0x01, 0xC2, 0x8B, 0x45, 0xF8, 0x48, 0x98, 0x8B, 0x44, 0x85, 0xC0, 0x89, 0x02, 0x8B, 0x55, 0xF8, 0x89,
        0xD0, 0xC1, 0xE0, 0x02, 0x01, 0xD0, 0xC1, 0xE0, 0x02, 0x01, 0xD0, 0x48, 0x98, 0x48, 0x8D, 0x50, 0x04, 0x48,
        0x8B, 0x45, 0x98, 0x48, 0x8D, 0x0C, 0x02, 0x48, 0x8D, 0x55, 0xA0, 0x48, 0x8B, 0x45, 0xE0, 0x48, 0x89, 0xD6,
        0x48, 0x89, 0xCF, 0xFF, 0xD0, 0x83, 0x45, 0xFC, 0x01, 0x83, 0x45, 0xF8, 0x01, 0xE9, 0x56, 0xFF, 0xFF, 0xFF,
        0x8B, 0x45, 0xFC, 0xC9, 0xC3
    ])

fu = Fu_Functions
of = Of_Offsets

class ToRemovePatches(NamedTuple):
    pid: int
    address: int
    data: bytes


SAVE_MOUNT_LOCk = Lock()


@dataclass(frozen = True, slots = True)
class MemoryIsPatched:
    pid: int
    libSceSaveDataBase: int
    libSceUserServiceBase: int
    libSceLibcInternalBase: int
    stub: int
    GetSaveDirectoriesAddr: int
    GetSaveDirectoriesAddr_length: int

    patches_made: Tuple[ToRemovePatches]
    sceunderscore_patch: ToRemovePatches
    
    async def _remove_patches(self, ps4: PS4Debug):
        """
        Be careful to not call this more then once per instance! if i could delete the instance after calling this i would
        """
        data = await ps4.read_memory(self.sceunderscore_patch.pid,self.sceunderscore_patch.address,length=len(self.sceunderscore_patch.data))
        if data != b'\x00':
            raise PS4MemoryNotPatched('PS4 memory is not patched, unless its partially unpatched, when in doubt, reboot ps4!')
          
        for patch in self.patches_made:
            await ps4.write_memory(patch.pid,patch.address,patch.data)
        await ps4.free_memory(self.pid,self.GetSaveDirectoriesAddr,self.GetSaveDirectoriesAddr_length)
        
        await ps4.write_memory(self.sceunderscore_patch.pid,self.sceunderscore_patch.address,self.sceunderscore_patch.data)
        print('PS4 Save patches removed from memory')
        await ps4.notify('PS4 Save patches removed from memory')


@dataclass(slots = True, frozen = True)
class SceSaveDataMount:
    userId: int
    dirName: int
    blocks: int
    mountMode: int
    titleId: int
    fingerprint: int
    
    def to_bytes(self):
        return (
                struct.pack('<i',self.userId) +
                b'\x00\x00\x00\x00' +
                struct.pack('<Q',self.titleId) +
                struct.pack('<Q',self.dirName) +
                struct.pack('<Q',self.fingerprint) +
                struct.pack('<Q',self.blocks) +
                struct.pack('<I',self.titleId) 
                )


@dataclass(slots = True, frozen = True)
class SceSaveDataMountResult:
    SceSaveDataMountPoint: bytes 
    requiredBlocks: int
    mountStatus: int
    
    error_code: int # should be 0 for no error


    def __post_init__(self):
        if len(self.SceSaveDataMountPoint) != 32:
            raise ValueError(f"{type(self).__name__} should be a bytes object of length 32, not {len(self.SceSaveDataMountPoint)}")

    def to_bytes(self) -> bytes:
        return self.SceSaveDataMountPoint + struct.pack('<Q',self.requiredBlocks) + struct.pack('<I',self.mountStatus) 
    
    def __bool__(self) -> bool:
        return self.error_code == 0

    @property
    def savedatax(self) -> str:
        """
        Will return the savedataX folder in which the save is mounted, eg savedata0 or savedata11
        """
        return self.SceSaveDataMountPoint.strip(b'\x00').decode('ascii').removeprefix('/').removeprefix('\\')


class PS4MemoryPatchingError(Exception):
    """
    Raise if error for errors with patching and unpatching memory 
    """

class ProcessNotFound(PS4MemoryPatchingError):
    """
    Raise if a process is not found
    """

class PS4VersionNotSupported(PS4MemoryPatchingError):
    """
    Raise if firmware version not supported
    """

class PS4MemoryAlreadyPatched(PS4MemoryPatchingError):
    """
    Raise if already patched when trying to patch
    """

class PS4MemoryNotPatched(PS4MemoryPatchingError):
    """
    Raise if not patched, but trying to unpatch
    """

async def patch_memory_for_saves_900(ps4: PS4Debug, fw_version: int) -> MemoryIsPatched:
    if fw_version not in SUPPORTED_MEM_PATCH_FW_VERSIONS:
        raise PS4VersionNotSupported(f'fimrware {fw_version} is not supported, only {SUPPORTED_MEM_PATCH_FW_VERSIONS}')
    processes = await ps4.get_processes()
    
    su = next((p for p in processes if p.name == 'SceShellUI'), None)
    
    if su is None:
        raise ProcessNotFound ("Couldn't find SceShellUI")
    
    pid = su.pid
    
    pm = await ps4.get_process_maps(pid)
    
    tmp = next((p.start for p in pm if p.name == 'libSceSaveData.sprx'), None)
    
    if tmp is None:
        raise ProcessNotFound('savedata lib not found')
    
    libSceSaveDataBase = int(tmp)
    
    tmp = next((p.start for p in pm if p.name == 'libSceUserService.sprx'), None)
    
    if tmp is None:
        raise ProcessNotFound('user service lib not found')
    
    libSceUserServiceBase = int(tmp)
     
    
    if next((p for p in pm if p.name == 'executable'), None) is None:
        raise ProcessNotFound('executable not found')
    
    tmp = next((p.start for p in pm if p.name == 'libSceLibcInternal.sprx'), None)
    
    if tmp is None:
        raise ProcessNotFound('libc not found')
    
    libSceLibcInternalBase = int(tmp)
    
    stub = None
    stub = await ps4.install_rpc(pid) if (next((p for p in pm if p.name == '(NoName)clienthandler'), None)) is None else int(next((p.start for p in pm if p.name == '(NoName)clienthandler'), None))
     
    ret = await ps4.call(pid,libSceSaveDataBase + of.sceSaveDataInitialize3, rpc_stub = stub)
    
    patches_made = []
    
    if fw_version == 9:
        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00035DA8,length=1)
        if data == b'\x00':
            raise PS4MemoryAlreadyPatched('PS4 memory is already patched, or lingering patches exist, please turn off any bots, or unpatch in save mounter, if this issue occurs, restart ps4')
        sceunderscore_patch = ToRemovePatches(pid, libSceSaveDataBase + 0x00035DA8,data)
        await ps4.write_memory(pid,libSceSaveDataBase + 0x00035DA8, b'\x00') # 'sce_' patch

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00034679,length=1)
        patches_made.append(ToRemovePatches(pid,libSceSaveDataBase + 0x00034679,data))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x00034679, b'\x00') # 'sce_sdmemory' patch
        
        # data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00000E81,length=1)
        # patches_made.append(ToRemovePatches(pid,libSceSaveDataBase + 0x00000E81,data))
        # await ps4.write_memory(pid,libSceSaveDataBase + 0x00000E81, b'\x30') # '_' patch
        pass # pass here to make notepad++ close the if statment propley
    elif fw_version == 11:
        # 11.00 WIP patches by LM and SocraticBliss
        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00355E8,length=1)
        if data == b'\x00':
            raise PS4MemoryAlreadyPatched('PS4 memory is already patched, or lingering patches exist, please turn off any bots, or unpatch in save mounter, if this issue occurs, restart ps4')
        sceunderscore_patch = ToRemovePatches(pid, libSceSaveDataBase + 0x00355E8,data)
        await ps4.write_memory(pid,libSceSaveDataBase + 0x00355E8, b'\x00') # 'sce_' patch

        # data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0034679,length=1)
        # patches_made.append(ToRemovePatches(pid, libSceSaveDataBase + 0x0034679,data))
        # await ps4.write_memory(pid,libSceSaveDataBase + 0x0034679, b'\x00') # patch commented out as idk WTF it does
        
        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0033E49,length=1)
        patches_made.append(ToRemovePatches(pid, libSceSaveDataBase + 0x0033E49,data))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x0033E49, b'\x00') 

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0035AA6,length=1)
        patches_made.append(ToRemovePatches(pid, libSceSaveDataBase + 0x0035AA6,data))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x0035AA6, b'\x00') 

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0000FB8,length=1)
        patches_made.append(ToRemovePatches(pid, libSceSaveDataBase + 0x0000FB8,data))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x0000FB8, b'\x1F') # sb

    l = await ps4.get_processes()
    
    s = next((p for p in l if p.name == u'SceShellCore\x00elf'), None)
    assert s is not None
    
    m = await ps4.get_process_maps(s.pid)
    ex = next((p for p in m if p.name == 'executable'), None) # theres mutiple wtf, lets hope this works
        
    # SHELLCORE PATCHES (SceShellCore)
    if fw_version == 9:
        # Patch 1
        data = await ps4.read_memory(s.pid, ex.start + 0x00E351D9, length=1)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x00E351D9, data))
        await ps4.write_memory(s.pid, ex.start + 0x00E351D9, b'\x00')  # 'sce_sdmemory' patch

        # Patch 2
        data = await ps4.read_memory(s.pid, ex.start + 0x00E35218, length=1)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x00E35218, data))
        await ps4.write_memory(s.pid, ex.start + 0x00E35218, b'\x00')  # 'sce_sdmemory1' patch

        # Patch 3
        data = await ps4.read_memory(s.pid, ex.start + 0x00E35226, length=1)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x00E35226, data))
        await ps4.write_memory(s.pid, ex.start + 0x00E35226, b'\x00')  # 'sce_sdmemory2' patch

        # Patch 4
        data = await ps4.read_memory(s.pid, ex.start + 0x00E35234, length=1)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x00E35234, data))
        await ps4.write_memory(s.pid, ex.start + 0x00E35234, b'\x00')  # 'sce_sdmemory3' patch

        # Patch 5
        data = await ps4.read_memory(s.pid, ex.start + 0x008AEAE0, length=4)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x008AEAE0, data))
        await ps4.write_memory(s.pid, ex.start + 0x008AEAE0, b'\x48\x32\xC0\xC3')  # verify keystone patch

        # Patch 6
        data = await ps4.read_memory(s.pid, ex.start + 0x0006C560, length=3)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x0006C560, data))
        await ps4.write_memory(s.pid, ex.start + 0x0006C560, b'\x31\xC0\xC3')  # transfer mount permission patch

        # Patch 7
        data = await ps4.read_memory(s.pid, ex.start + 0x000C9000, length=3)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x000C9000, data))
        await ps4.write_memory(s.pid, ex.start + 0x000C9000, b'\x31\xC0\xC3')  # patch psn check

        # Patch 8
        data = await ps4.read_memory(s.pid, ex.start + 0x0006DC5D, length=2)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x0006DC5D, data))
        await ps4.write_memory(s.pid, ex.start + 0x0006DC5D, b'\x90\x90')  #       ^

        # Patch 9
        data = await ps4.read_memory(s.pid, ex.start + 0x0006C0A8, length=6)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x0006C0A8, data))
        await ps4.write_memory(s.pid, ex.start + 0x0006C0A8, b'\x90\x90\x90\x90\x90\x90')  # something something patches

        # Patch 10
        data = await ps4.read_memory(s.pid, ex.start + 0x0006BA62, length=6)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x0006BA62, data))
        await ps4.write_memory(s.pid, ex.start + 0x0006BA62, b'\x90\x90\x90\x90\x90\x90')  # don't even remember doing this

        # Patch 11
        data = await ps4.read_memory(s.pid, ex.start + 0x0006B2C4, length=2)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x0006B2C4, data))
        await ps4.write_memory(s.pid, ex.start + 0x0006B2C4, b'\x90\x90')  # nevah jump

        # Patch 12
        data = await ps4.read_memory(s.pid, ex.start + 0x0006B51E, length=2)
        patches_made.append(ToRemovePatches(s.pid, ex.start + 0x0006B51E, data))
        await ps4.write_memory(s.pid, ex.start + 0x0006B51E, b'\x90\xE9')  # always jump
    elif fw_version == 11:
        patches_11_00 = (
            (0x0E26439, b"\x00", 1),  # 'sce_sdmemory' patch 1
            (0x0E26478, b"\x00", 1),  # 'sce_sdmemory1' patch
            (0x0E26486, b"\x00", 1),  # 'sce_sdmemory2' patch
            (0x0E26494, b"\x00", 1),  # 'sce_sdmemory3' patch
            (0x08BAF40, b"\x48\x31\xC0\xC3", 4),  # verify keystone patch
            (0x006B630, b"\x31\xC0\xC3", 3),  # transfer mount permission patch
            (0x00C7060, b"\x31\xC0\xC3", 3),  # patch psn check
            (0x006CFA5, b"\x90\x90", 2),  #     ^ (thanks to GRModSave_Username)
            (0x006B177, b"\x90\x90\x90\x90\x90\x90", 6),  # something something patches...
            (0x006AB32, b"\x90\x90\x90\x90\x90\x90", 6),  # don't even remember doing this
            (0x006A394, b"\x90\x90", 2),  # nevah jump
            (0x006A5EE, b"\xE9\xC8\x00", 3),  # always jump
        )


        for patch_address, patch_data, patch_data_length in patches_11_00:
            data = await ps4.read_memory(s.pid, ex.start + patch_address, length=patch_data_length)
            patches_made.append(ToRemovePatches(s.pid, ex.start + patch_address, data))
            await ps4.write_memory(s.pid, ex.start + patch_address, patch_data)
    # WRITE CUSTOM FUNCTIONS (libSceLibcInternal)
    GetSaveDirectoriesAddr = await ps4.allocate_memory(pid, 0x8000)
    await ps4.write_memory(pid, GetSaveDirectoriesAddr, fu.GetSaveDirectories)
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x12, libSceLibcInternalBase + 0x000AF370) # opendir
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x20, libSceLibcInternalBase + 0x000B0100) # readdir
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x2E, libSceLibcInternalBase + 0x000AE100) # closedir
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x3C, libSceLibcInternalBase + 0x000BB930) # strcpy
    
    GetUsersAddr = GetSaveDirectoriesAddr + len(fu.GetSaveDirectories) + 0x20
    await ps4.write_memory(pid, GetUsersAddr, fu.GetUsers)
    await ps4.write_int64(pid, GetUsersAddr + 0x15, libSceUserServiceBase + of.sceUserServiceGetLoginUserIdList)
    await ps4.write_int64(pid, GetUsersAddr + 0x23, libSceUserServiceBase + of.sceUserServiceGetUserName)
    await ps4.write_int64(pid, GetUsersAddr + 0x31, libSceLibcInternalBase + 0x000BB930) # strcpy
    

    async with ps4.memory(pid,length=1) as memory:
        ret = await ps4.call(pid, GetUsersAddr, memory.address, rpc_stub = stub)
    
    print('PS4 Save patches applied to memory') 
    await ps4.notify('PS4 Save patches applied to memory')

    return MemoryIsPatched(pid = pid, 
                            libSceSaveDataBase = libSceSaveDataBase, 
                            libSceUserServiceBase = libSceUserServiceBase, 
                            libSceLibcInternalBase = libSceLibcInternalBase, 
                            stub = stub,
                            GetSaveDirectoriesAddr = GetSaveDirectoriesAddr,
                            GetSaveDirectoriesAddr_length = 0x8000,
                            patches_made = tuple(patches_made),
                            sceunderscore_patch = sceunderscore_patch
                            )

""" # ITS BROKEN!, returns -1 for some reason
async def get_user_id(ps4: PS4Debug ,mem: MemoryIsPatched) -> int:
    
    pm = await ps4.get_process_maps(mem.pid)
    
    async with ps4.memory(mem.pid,length=4) as memory1: # 4 bytes for a int32        
        buffer_addr = memory1.address
        await ps4.call(mem.pid, mem.libSceUserServiceBase + of.sceUserServiceGetInitialUser, buffer_addr, rpc_stub = mem.stub)
        id = await ps4.read_int32(mem.pid, buffer_addr)

        print('user id:',id)
        return id
""" 

async def mount_save(ps4: PS4Debug, mem: MemoryIsPatched, user_id: int,cusa_game_id: str, savedir: str, mountMode: int, blocks: int) -> SceSaveDataMountResult:
    with SAVE_MOUNT_LOCk:
        size_of_SceSaveDataDirName = 32
        size_of_SceSaveDataMount = 80
        size_of_SceSaveDataMountResult = 64
        # await get_user_id(ps4,mem)
        async with ps4.memory(mem.pid,size_of_SceSaveDataDirName + 0x10 + 0x41) as memory1:
            dirNameAddr = memory1.address
            titleIdAddr = dirNameAddr + size_of_SceSaveDataDirName
            fingerprintAddr = titleIdAddr + 0x10
            await ps4.write_memory(mem.pid, titleIdAddr, cusa_game_id.encode('utf-8'))
            await ps4.write_memory(mem.pid, fingerprintAddr, b"0000000000000000000000000000000000000000000000000000000000000000")
            
            await ps4.write_memory(mem.pid, dirNameAddr, savedir.encode('utf-8'))
            
            mount = SceSaveDataMount(userId = user_id, dirName = dirNameAddr, blocks = blocks, mountMode = mountMode, fingerprint = fingerprintAddr, titleId = titleIdAddr)
            
            ########
            async with ps4.memory(mem.pid,size_of_SceSaveDataMount + size_of_SceSaveDataMountResult) as memory2:
                mountAddr = memory2.address
                mountResultAddr = mountAddr + size_of_SceSaveDataMount
                await ps4.write_memory(mem.pid , mountAddr, mount.to_bytes())
                await ps4.write_memory(mem.pid , mountResultAddr, b'\x00' * size_of_SceSaveDataMountResult)
                
                ret = await ps4.call(mem.pid, mem.libSceSaveDataBase + of.sceSaveDataMount, mountAddr, mountResultAddr, rpc_stub = mem.stub)
                result = SceSaveDataMountResult(SceSaveDataMountPoint=b'\x00' * size_of_SceSaveDataDirName, requiredBlocks=0, mountStatus=0, error_code = ret[0])
                
                if ret[0] == 0:
                    mount_bytes = await ps4.read_memory(mem.pid, mountResultAddr, size_of_SceSaveDataMountResult)
                    
                    mount_point = mount_bytes[:0x20]
                    requried_blocks = struct.unpack('<Q',mount_bytes[0x20:0x28])[0]
                    mount_status = struct.unpack('<I',mount_bytes[0x28:0x2C])[0]
                    
                    result = SceSaveDataMountResult(SceSaveDataMountPoint = mount_point, requiredBlocks = requried_blocks, mountStatus = mount_status, error_code = ret[0]) 

        return result


async def unmount_save(ps4: PS4Debug, mem: MemoryIsPatched, mp: SceSaveDataMountResult) -> int:
    with SAVE_MOUNT_LOCk:
        async with ps4.memory(mem.pid, length = len(mp.SceSaveDataMountPoint)) as memory:
            await memory.write(mp.SceSaveDataMountPoint)
            ret = await ps4.call(mem.pid,mem.libSceSaveDataBase + of.sceSaveDataUmount,memory.address,rpc_stub = mem.stub)
            return ret[0]

"""
import asyncio
async def main():
    ps4 = PS4Debug('1.1.1.2')
    mem = await patch_memory_for_saves_900(ps4)
    
    leh_mp = await mount_save(ps4,mem,0x1eb71bbd,'CUSA00473','LBPxSAVE')
    
    if leh_mp:
        await ps4.notify('save Mounted!')
    
    input(f'{leh_mp = }')
    
    unmount_error = await unmount_save(ps4,mem,leh_mp)
    
    if unmount_error == 0:
        await ps4.notify('save Unmounted!')
    
    print(f'{unmount_error = }')
    
    await mem._remove_patches(ps4)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
"""
