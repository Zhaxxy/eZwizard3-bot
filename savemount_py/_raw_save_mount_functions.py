from threading import Lock
import struct
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple, Tuple

from ps4debug import PS4Debug

SUPPORTED_MEM_PATCH_FW_VERSIONS = (
    9,
    # 11 is not enabled until it is re-tested on real hardware.
    1050,
    1200,  # FW 12.00 offsets confirmed on real hardware.
)
DEBUG_SAVE_MOUNT = False
MEMORY_PATCH_STATE_FILE = Path(__file__).resolve().parents[1] / "ps4_memory_patch_state.json"
MEMORY_PATCH_STATE_VERSION = 1


def _debug(message: str) -> None:
    if DEBUG_SAVE_MOUNT:
        print(f"DEBUG: {message}")


def _clean_ps4_name(value: object) -> str:
    return str(value).replace("\x00", "")


def _delete_memory_patch_state() -> None:
    try:
        MEMORY_PATCH_STATE_FILE.unlink()
    except FileNotFoundError:
        pass

class Of_Offsets:
    sceSaveDataInitialize3 = 0x00027FA0
    sceUserServiceGetUserName = 0x000045A0
    sceUserServiceGetLoginUserIdList = 0x00002C00
    sceSaveDataMount = 0x00028130
    sceSaveDataUmount = 0x000288E0
    sceUserServiceGetInitialUser = 0x000033C0

class Of_Offsets_1200:
    # FW 12.00 offsets confirmed on real hardware.
    sceSaveDataInitialize3 = 0x00027BC0
    sceUserServiceGetUserName = 0x000044F0
    sceUserServiceGetLoginUserIdList = 0x00002C00
    sceSaveDataMount = 0x00027D50
    sceSaveDataMount2 = 0x00028030
    sceSaveDataUmount = 0x00028540
    sceUserServiceGetInitialUser = 0x00003400

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


class MemoryPatchStateBuilder:
    def __init__(self, fw_version: int) -> None:
        self.state = {
            "version": MEMORY_PATCH_STATE_VERSION,
            "fw_version": fw_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "complete": False,
            "patches": [],
            "allocations": [],
        }

    def _write(self) -> None:
        tmp_path = MEMORY_PATCH_STATE_FILE.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        tmp_path.replace(MEMORY_PATCH_STATE_FILE)

    def record_patch(
        self,
        *,
        process_name: str,
        pid: int,
        map_name: str,
        map_base: int,
        module_offset: int,
        old_data: bytes,
        patched_data: bytes,
    ) -> ToRemovePatches:
        address = int(map_base) + int(module_offset)
        self.state["patches"].append(
            {
                "process_name": _clean_ps4_name(process_name),
                "pid": int(pid),
                "map_name": _clean_ps4_name(map_name),
                "map_base": int(map_base),
                "module_offset": int(module_offset),
                "address": int(address),
                "old_data": old_data.hex(),
                "patched_data": patched_data.hex(),
            }
        )
        self._write()
        return ToRemovePatches(pid, address, old_data)

    def record_allocation(
        self,
        *,
        process_name: str,
        pid: int,
        address: int,
        length: int,
    ) -> None:
        self.state["allocations"].append(
            {
                "process_name": _clean_ps4_name(process_name),
                "pid": int(pid),
                "address": int(address),
                "length": int(length),
            }
        )
        self._write()

    def mark_complete(self) -> None:
        self.state["complete"] = True
        self._write()


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
        _delete_memory_patch_state()
        print('PS4 Save patches removed from memory')
        await ps4.notify('PS4 Save patches removed from memory')


@dataclass(slots=True)
class SceSaveDataMount:
    userId: int
    titleId: int
    dirName: int
    fingerprint: int
    blocks: int
    mount_mode: int

    def to_bytes(self) -> bytes:
        b = bytearray(0x80)

        struct.pack_into("<I", b, 0x00, self.userId)
        struct.pack_into("<Q", b, 0x08, self.titleId)
        struct.pack_into("<Q", b, 0x10, self.dirName)
        struct.pack_into("<Q", b, 0x18, self.fingerprint)
        struct.pack_into("<Q", b, 0x20, self.blocks)
        struct.pack_into("<I", b, 0x28, self.mount_mode)

        return bytes(b)

@dataclass(slots=True)
class SceSaveDataMount2:
    userId: int
    titleId: int
    fingerprint: int
    mount_mode: int


    def to_bytes(self) -> bytes:
        b = bytearray(0x40)

        struct.pack_into("<I", b, 0x00, self.userId)

        # 0x04 -> 4 bytes zero padding.

        struct.pack_into("<Q", b, 0x08, self.titleId)
        struct.pack_into("<Q", b, 0x10, self.fingerprint)
        struct.pack_into("<I", b, 0x18, self.mount_mode)


        return bytes(b)


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

    @property
    def clean_mount_point(self) -> bytes:
        return self.SceSaveDataMountPoint.split(b'\x00', 1)[0]

    def __bool__(self) -> bool:
        return self.error_code == 0 and bool(self.clean_mount_point)

    @property
    def savedatax(self) -> str:
        """
        Will return the savedataX folder in which the save is mounted, eg savedata0 or savedata11
        """
        return self.clean_mount_point.decode('ascii').removeprefix('/').removeprefix('\\')


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


class PS4MemoryPatchStateError(PS4MemoryPatchingError):
    """
    Raise if the saved patch state cannot be safely restored
    """


async def _find_process_by_clean_name(ps4: PS4Debug, process_name: str):
    processes = await ps4.get_processes()
    clean_process_name = _clean_ps4_name(process_name)
    return next(
        (p for p in processes if _clean_ps4_name(getattr(p, "name", "")) == clean_process_name),
        None,
    )


async def _find_map_by_clean_name(ps4: PS4Debug, pid: int, map_name: str):
    maps = await ps4.get_process_maps(pid)
    clean_map_name = _clean_ps4_name(map_name)
    return next(
        (m for m in maps if _clean_ps4_name(getattr(m, "name", "")) == clean_map_name),
        None,
    )


async def restore_memory_patches_from_state(ps4: PS4Debug) -> dict[str, int | str]:
    if not MEMORY_PATCH_STATE_FILE.exists():
        raise PS4MemoryNotPatched(
            f"No memory patch state file found at {MEMORY_PATCH_STATE_FILE}"
        )

    state = json.loads(MEMORY_PATCH_STATE_FILE.read_text(encoding="utf-8"))
    if state.get("version") != MEMORY_PATCH_STATE_VERSION:
        raise PS4MemoryPatchStateError(
            f"Unsupported memory patch state version: {state.get('version')}"
        )

    patch_records = list(reversed(state.get("patches", [])))
    resolved_patches = []
    mismatches = []

    for record in patch_records:
        process = await _find_process_by_clean_name(ps4, record["process_name"])
        if process is None:
            raise PS4MemoryPatchStateError(
                f"Could not find process {record['process_name']!r}; state was left untouched"
            )

        process_map = await _find_map_by_clean_name(ps4, process.pid, record["map_name"])
        if process_map is None:
            raise PS4MemoryPatchStateError(
                f"Could not find map {record['map_name']!r} in {record['process_name']!r}; "
                "state was left untouched"
            )

        old_data = bytes.fromhex(record["old_data"])
        patched_data = bytes.fromhex(record["patched_data"])
        address = int(process_map.start) + int(record["module_offset"])
        current_data = await ps4.read_memory(process.pid, address, length=len(old_data))

        if current_data not in (old_data, patched_data):
            mismatches.append(
                f"{record['process_name']}:{record['map_name']}+0x{record['module_offset']:X} "
                f"current={current_data.hex()} expected={patched_data.hex()} or {old_data.hex()}"
            )
            continue

        resolved_patches.append(
            {
                "pid": process.pid,
                "address": address,
                "old_data": old_data,
                "patched_data": patched_data,
                "current_data": current_data,
            }
        )

    if mismatches:
        raise PS4MemoryPatchStateError(
            "Memory does not match the saved patch state; state was left untouched: "
            + "; ".join(mismatches)
        )

    restored_patches = 0
    already_restored_patches = 0
    active_patches = False

    for patch in resolved_patches:
        if patch["current_data"] == patch["patched_data"]:
            active_patches = True
            await ps4.write_memory(patch["pid"], patch["address"], patch["old_data"])
            restored_patches += 1
        else:
            already_restored_patches += 1

    freed_allocations = 0
    skipped_allocations = 0
    if active_patches:
        for allocation in state.get("allocations", []):
            process = await _find_process_by_clean_name(ps4, allocation["process_name"])
            if process is None or int(process.pid) != int(allocation["pid"]):
                skipped_allocations += 1
                continue

            try:
                await ps4.free_memory(
                    process.pid,
                    int(allocation["address"]),
                    int(allocation["length"]),
                )
            except Exception:
                skipped_allocations += 1
            else:
                freed_allocations += 1
    else:
        skipped_allocations = len(state.get("allocations", []))

    _delete_memory_patch_state()
    return {
        "restored_patches": restored_patches,
        "already_restored_patches": already_restored_patches,
        "freed_allocations": freed_allocations,
        "skipped_allocations": skipped_allocations,
        "state_file": str(MEMORY_PATCH_STATE_FILE),
    }


async def patch_memory_for_saves_900(ps4: PS4Debug, fw_version: int) -> MemoryIsPatched:
    if fw_version not in SUPPORTED_MEM_PATCH_FW_VERSIONS:
        raise PS4VersionNotSupported(f'fimrware {fw_version} is not supported, only {SUPPORTED_MEM_PATCH_FW_VERSIONS}')

    if MEMORY_PATCH_STATE_FILE.exists():
        raise PS4MemoryAlreadyPatched(
            f"A memory patch state file already exists at {MEMORY_PATCH_STATE_FILE}. "
            "Run `python main.py --unpatch-memory` before patching again."
        )

    global of
    if fw_version == 1200:
        of = Of_Offsets_1200
    else:
        of = Of_Offsets

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
    _debug(f"sceSaveDataInitialize3 ret = 0x{ret[0] & 0xffffffff:X}")

    patches_made = []
    patch_state = MemoryPatchStateBuilder(fw_version)

    def record_save_data_patch(module_offset: int, old_data: bytes, patched_data: bytes) -> ToRemovePatches:
        return patch_state.record_patch(
            process_name=su.name,
            pid=pid,
            map_name="libSceSaveData.sprx",
            map_base=libSceSaveDataBase,
            module_offset=module_offset,
            old_data=old_data,
            patched_data=patched_data,
        )

    if fw_version == 9:
        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00035DA8,length=1)
        if data == b'\x00':
            raise PS4MemoryAlreadyPatched('PS4 memory is already patched, or lingering patches exist, please turn off any bots, or unpatch in save mounter, if this issue occurs, restart ps4')
        sceunderscore_patch = record_save_data_patch(0x00035DA8, data, b'\x00')
        await ps4.write_memory(pid,libSceSaveDataBase + 0x00035DA8, b'\x00') # 'sce_' patch

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00034679,length=1)
        patches_made.append(record_save_data_patch(0x00034679, data, b'\x00'))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x00034679, b'\x00') # 'sce_sdmemory' patch

        pass # pass here to make notepad++ close the if statment propley
    elif fw_version in (11,1050):
        # 10.50 uses this older patch family. FW 11.00 stays disabled until
        # it is validated again on real hardware.
        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x00355E8,length=1)
        if data == b'\x00':
            raise PS4MemoryAlreadyPatched('PS4 memory is already patched, or lingering patches exist, please turn off any bots, or unpatch in save mounter, if this issue occurs, restart ps4')
        sceunderscore_patch = record_save_data_patch(0x00355E8, data, b'\x00')
        await ps4.write_memory(pid,libSceSaveDataBase + 0x00355E8, b'\x00') # 'sce_' patch

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0033E49,length=1)
        patches_made.append(record_save_data_patch(0x0033E49, data, b'\x00'))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x0033E49, b'\x00')

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0035AA6,length=1)
        patches_made.append(record_save_data_patch(0x0035AA6, data, b'\x00'))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x0035AA6, b'\x00')

        data = await ps4.read_memory(pid,libSceSaveDataBase + 0x0000FB8,length=1)
        patches_made.append(record_save_data_patch(0x0000FB8, data, b'\x1F'))
        await ps4.write_memory(pid,libSceSaveDataBase + 0x0000FB8, b'\x1F') # sb

    elif fw_version == 1200:
        data = await ps4.read_memory(pid, libSceSaveDataBase + 0x00035CF1, length=1)
        _debug(f"libSceSaveData 0x35CF1 old={data.hex()}")
        if data == b'\x00':
           raise PS4MemoryAlreadyPatched(
            'PS4 memory is already patched, or lingering patches exist, please restart ps4'
           )
        sceunderscore_patch = record_save_data_patch(0x00035CF1, data, b'\x00')
        await ps4.write_memory(pid, libSceSaveDataBase + 0x00035CF1, b'\x00')

        data = await ps4.read_memory(pid, libSceSaveDataBase + 0x00034289, length=1)
        _debug(f"libSceSaveData 0x34289 old={data.hex()}")
        patches_made.append(record_save_data_patch(0x00034289, data, b'\x00'))
        await ps4.write_memory(pid, libSceSaveDataBase + 0x00034289, b'\x00')

        data = await ps4.read_memory(pid, libSceSaveDataBase + 0x00035CF6, length=1)
        _debug(f"libSceSaveData 0x35CF6 old={data.hex()}")
        patches_made.append(record_save_data_patch(0x00035CF6, data, b'\x00'))
        await ps4.write_memory(pid, libSceSaveDataBase + 0x00035CF6, b'\x00')

        data = await ps4.read_memory(pid, libSceSaveDataBase + 0x00027E00, length=5)
        _debug(f"libSceSaveData 0x27E00 old={data.hex()}")
        patches_made.append(record_save_data_patch(0x00027E00, data, b"\x89\xD0\x90\x90\x90"))
        await ps4.write_memory(pid, libSceSaveDataBase + 0x00027E00, b"\x89\xD0\x90\x90\x90")
        if DEBUG_SAVE_MOUNT:
            verify = await ps4.read_memory(pid, libSceSaveDataBase + 0x00027E00, length=5)
            _debug(f"libSceSaveData 0x27E00 verify={verify.hex()}")

        data = await ps4.read_memory(pid, libSceSaveDataBase + 0x0002E150, length=3)
        _debug(f"libSceSaveData 0x2E150 old={data.hex()}")
        patches_made.append(record_save_data_patch(0x0002E150, data, b"\x31\xC0\xC3"))
        await ps4.write_memory(
            pid,
            libSceSaveDataBase + 0x0002E150,
            b"\x31\xC0\xC3"
        )
        if DEBUG_SAVE_MOUNT:
            verify = await ps4.read_memory(pid, libSceSaveDataBase + 0x0002E150, length=3)
            _debug(f"libSceSaveData 0x2E150 verify={verify.hex()}")

    l = await ps4.get_processes()

    s = next((p for p in l if p.name == u'SceShellCore\x00elf'), None)
    assert s is not None

    m = await ps4.get_process_maps(s.pid)
    ex = next((p for p in m if p.name == 'executable'), None) # theres mutiple wtf, lets hope this works

    # SHELLCORE PATCHES (SceShellCore)
    if fw_version == 9:
        shell_core_patches_to_do = (
            (0x00E351D9, b'\x00', 1),  # 'sce_sdmemory' patch
            (0x00E35218, b'\x00', 1),  # 'sce_sdmemory1' patch
            (0x00E35226, b'\x00', 1),  # 'sce_sdmemory2' patch
            (0x00E35234, b'\x00', 1),  # 'sce_sdmemory3' patch
            (0x008AEAE0, b'\x48\x32\xC0\xC3', 4),  # verify keystone patch
            (0x0006C560, b'\x31\xC0\xC3', 3),  # transfer mount permission patch
            (0x000C9000, b'\x31\xC0\xC3', 3),  # patch psn check
            (0x0006DC5D, b'\x90\x90', 2),  # ^
            (0x0006C0A8, b'\x90\x90\x90\x90\x90\x90', 6),  # something something patches
            (0x0006BA62, b'\x90\x90\x90\x90\x90\x90', 6),  # don't even remember doing this
            (0x0006B2C4, b'\x90\x90', 2),  # nevah jump
            (0x0006B51E, b'\x90\xE9', 2),  # always jump
        )

    elif fw_version == 11:
        shell_core_patches_to_do = (
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

    elif fw_version == 1050:
        shell_core_patches_to_do = (
            (0x0E149B9, b"\x00", 1),                        # 'sce_sdmemory' patch 1
            (0x0E149F8, b"\x00", 1),                        # 'sce_sdmemory1' patch
            (0x0E14A06, b"\x00", 1),                        # 'sce_sdmemory2' patch
            (0x0E14A14, b"\x00", 1),                        # 'sce_sdmemory3' patch
            (0x08AAC00, b"\x48\x31\xC0\xC3", 4),            #verify keystone patch
            (0x006B630, b"\x31\xC0\xC3", 3),                #transfer mount permission patch eg mount foreign saves with write permission
            (0x00C7060, b"\x31\xC0\xC3", 3),                #patch psn check to load saves saves foreign to current account
            (0x006CFA5, b"\x90\x90", 2),                    # ^ (thanks to GRModSave_Username)
            (0x006B177, b"\x90\x90\x90\x90\x90\x90", 6),    # something something patches...
            (0x006AB32, b"\x90\x90\x90\x90\x90\x90", 6),    # don't even remember doing this
            (0x006a394, b"\x90\x90", 2),                    #nevah jump
            (0x006A5EE, b"\xE9\xC8\x00", 3),                #always jump
        )

    elif fw_version == 1200:
        # FW 12.00 SceShellCore patches confirmed on real hardware.
        # Do not use the old 0x0006E460 bypass: it returns success with an
        # empty mount result.
        shell_core_patches_to_do = (
            (0x00E2CE99, b"\x00", 1),  # sce_sdmemory patch 1
            (0x00E2CED8, b"\x00", 1),  # sce_sdmemory patch 2
            (0x00E2CEE6, b"\x00", 1),  # sce_sdmemory patch 3
            (0x00E2CEF4, b"\x00", 1),  # sce_sdmemory patch 4
            (0x008C2970, b"\x48\x31\xC0\xC3", 4),  # verify keystone stub
            (0x000B49B1, b"\x90\x90", 2),  # branch bypass
            (0x003FD6C6, b"\x90\x90", 2),  # legacy 0x80A40005 branch bypass
            (0x003E71BD, b"\xE9\x63\x01\x00\x00\x90", 6),  # app lookup fallback
            (0x0006CD1C, b"\xEB", 1),  # mount arg flag bypass
            (0x000B9F90, b"\x31\xC0\xC3", 3),  # create keystone check stub
            (0x000BA000, b"\x31\xC0\xC3", 3),  # open keystone check stub
            (0x0006E6EE, b"\xEB", 1),  # metadata check bypass
            (0x000C99FF, b"\x90\x90", 2),  # param.sfo owner bypass
        )

    for patch_address, patch_data, patch_data_length in shell_core_patches_to_do:
        data = await ps4.read_memory(
           s.pid,
           ex.start + patch_address,
           length=patch_data_length
        )

        _debug(
            f"ShellCore patch 0x{patch_address:08X} "
            f"addr=0x{ex.start + patch_address:X} "
            f"old={data.hex()} new={patch_data.hex()}"
        )

        patches_made.append(
            patch_state.record_patch(
                process_name=s.name,
                pid=s.pid,
                map_name=ex.name,
                map_base=ex.start,
                module_offset=patch_address,
                old_data=data,
                patched_data=patch_data,
            )
        )

        await ps4.write_memory(
           s.pid,
           ex.start + patch_address,
           patch_data
        )

        if DEBUG_SAVE_MOUNT:
            check = await ps4.read_memory(
               s.pid,
               ex.start + patch_address,
               length=patch_data_length
            )
            _debug(f"ShellCore patch 0x{patch_address:08X} verify={check.hex()}")


    # WRITE CUSTOM FUNCTIONS (libSceLibcInternal)
    # Select libc offsets based on firmware version
    if fw_version == 1200:
        libc_opendir  = 0x00088170
        libc_readdir  = 0x00088F30
        libc_closedir = 0x00086F00
        libc_strcpy   = 0x000D3660
    else:
        libc_opendir  = 0x000AF370
        libc_readdir  = 0x000B0100
        libc_closedir = 0x000AE100
        libc_strcpy   = 0x000BB930

    GetSaveDirectoriesAddr_length = 0x8000
    GetSaveDirectoriesAddr = await ps4.allocate_memory(pid, GetSaveDirectoriesAddr_length)
    patch_state.record_allocation(
        process_name=su.name,
        pid=pid,
        address=GetSaveDirectoriesAddr,
        length=GetSaveDirectoriesAddr_length,
    )
    await ps4.write_memory(pid, GetSaveDirectoriesAddr, fu.GetSaveDirectories)
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x12, libSceLibcInternalBase + libc_opendir)  # opendir
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x20, libSceLibcInternalBase + libc_readdir)  # readdir
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x2E, libSceLibcInternalBase + libc_closedir) # closedir
    await ps4.write_int64(pid, GetSaveDirectoriesAddr + 0x3C, libSceLibcInternalBase + libc_strcpy)   # strcpy

    GetUsersAddr = GetSaveDirectoriesAddr + len(fu.GetSaveDirectories) + 0x20
    await ps4.write_memory(pid, GetUsersAddr, fu.GetUsers)
    await ps4.write_int64(pid, GetUsersAddr + 0x15, libSceUserServiceBase + of.sceUserServiceGetLoginUserIdList)
    await ps4.write_int64(pid, GetUsersAddr + 0x23, libSceUserServiceBase + of.sceUserServiceGetUserName)
    await ps4.write_int64(pid, GetUsersAddr + 0x31, libSceLibcInternalBase + libc_strcpy) # strcpy


    async with ps4.memory(pid,length=1) as memory:
        ret = await ps4.call(pid, GetUsersAddr, memory.address, rpc_stub = stub)

    patch_state.mark_complete()
    print('PS4 Save patches applied to memory')
    await ps4.notify('PS4 Save patches applied to memory')

    return MemoryIsPatched(pid = pid,
                            libSceSaveDataBase = libSceSaveDataBase,
                            libSceUserServiceBase = libSceUserServiceBase,
                            libSceLibcInternalBase = libSceLibcInternalBase,
                            stub = stub,
                            GetSaveDirectoriesAddr = GetSaveDirectoriesAddr,
                            GetSaveDirectoriesAddr_length = GetSaveDirectoriesAddr_length,
                            patches_made = tuple(patches_made),
                            sceunderscore_patch=sceunderscore_patch
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

async def mount_save(ps4: PS4Debug, mem: MemoryIsPatched, user_id: int, cusa_game_id: str, savedir: str, mountMode: int = 0x8, blocks: int = 32_768) -> SceSaveDataMountResult:
    with SAVE_MOUNT_LOCk:
        size_of_SceSaveDataDirName = 32
        size_of_SceSaveDataMount = 0x80
        size_of_SceSaveDataMountResult = 64

        total_size = (
            size_of_SceSaveDataMount +
            size_of_SceSaveDataMountResult +
            size_of_SceSaveDataDirName +
            0x10 +
            0x41
        )

        async with ps4.memory(mem.pid, total_size) as memory:
            mountAddr = memory.address
            mountResultAddr = mountAddr + size_of_SceSaveDataMount
            dirNameAddr = mountResultAddr + size_of_SceSaveDataMountResult
            titleIdAddr = dirNameAddr + size_of_SceSaveDataDirName
            fingerprintAddr = titleIdAddr + 0x10

            await ps4.write_memory(mem.pid, mountAddr, b'\x00' * total_size)

            dir_data = savedir.encode('utf-8')[:31] + b'\x00'
            title_data = cusa_game_id.encode('utf-8')[:15] + b'\x00'
            fp_data = b"0" * 64 + b'\x00'

            await ps4.write_memory(mem.pid, dirNameAddr, dir_data)
            await ps4.write_memory(mem.pid, titleIdAddr, title_data)
            await ps4.write_memory(mem.pid, fingerprintAddr, fp_data)

            mount = SceSaveDataMount(
               userId=user_id,
               titleId=titleIdAddr,
               dirName=dirNameAddr,
               fingerprint=fingerprintAddr,
               blocks=blocks,
               mount_mode=mountMode,
            )

            mount_bytes = mount.to_bytes()
            await ps4.write_memory(mem.pid, mountAddr, mount_bytes)
            _debug(
                f"mount {cusa_game_id}/{savedir} mode=0x{mountMode:X} "
                f"user=0x{user_id:X} mount=0x{mountAddr:X} result=0x{mountResultAddr:X}"
            )

            ret = await ps4.call(
                mem.pid,
                mem.libSceSaveDataBase + of.sceSaveDataMount,
                mountAddr,
                mountResultAddr,
                rpc_stub=mem.stub
            )

            _debug(
                f"sceSaveDataMount addr=0x{mem.libSceSaveDataBase + of.sceSaveDataMount:X} "
                f"ret=0x{ret[0] & 0xffffffff:X}"
            )
            if ret[0] != 0:
                return SceSaveDataMountResult(
                    SceSaveDataMountPoint=b'\x00' * size_of_SceSaveDataDirName,
                    requiredBlocks=0,
                    mountStatus=0,
                    error_code=ret[0]
                )

            mount_bytes = await ps4.read_memory(
                mem.pid,
                mountResultAddr,
                size_of_SceSaveDataMountResult
            )

            mount_point = mount_bytes[:0x20]
            required_blocks = struct.unpack('<Q', mount_bytes[0x20:0x28])[0]
            mount_status = struct.unpack('<I', mount_bytes[0x28:0x2C])[0]
            clean_mount_point = mount_point.split(b'\x00', 1)[0]

            _debug(
                f"mount result point={clean_mount_point!r} "
                f"required_blocks={required_blocks} status=0x{mount_status:X}"
            )

            return SceSaveDataMountResult(
                SceSaveDataMountPoint=mount_point,
                requiredBlocks=required_blocks,
                mountStatus=mount_status,
                error_code=ret[0]
            )

async def unmount_save(ps4: PS4Debug, mem: MemoryIsPatched, mp: SceSaveDataMountResult) -> int:
    with SAVE_MOUNT_LOCk:
        async with ps4.memory(mem.pid, length = len(mp.SceSaveDataMountPoint)) as memory:
            await memory.write(mp.SceSaveDataMountPoint)
            ret = await ps4.call(mem.pid,mem.libSceSaveDataBase + of.sceSaveDataUmount,memory.address,rpc_stub = mem.stub)
            return ret[0]
