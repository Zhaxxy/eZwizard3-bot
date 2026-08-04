import asyncio
import struct
from typing import Any

from ps4debug import PS4Debug


class FirmwareDetectionError(RuntimeError):
    pass


class FirmwareDetectionTimeout(FirmwareDetectionError):
    pass


SYS___SYSCTL = 202
CTL_SYSCTL = 0
CTL_SYSCTL_NAME2OID = 3
CTL_MAXNAME = 24
DEBUG_FIRMWARE_DETECTION = False


def _debug(message: str) -> None:
    if DEBUG_FIRMWARE_DETECTION:
        print(f"DEBUG: {message}", flush=True)


async def _timeout(label: str, awaitable: Any, seconds: float = 10) -> Any:
    try:
        return await asyncio.wait_for(awaitable, timeout=seconds)
    except asyncio.TimeoutError as exc:
        raise FirmwareDetectionTimeout(f"{label} timed out after {seconds:g}s") from exc

# ps4debug.call passes args as rdi, rsi, rdx, rcx, rbx, rax.
# The amd64 syscall ABI expects rdi, rsi, rdx, r10, r8, r9, with the syscall
# number in rax. This stub adapts the register layout and executes __sysctl.
_SYSCTL_STUB = bytes.fromhex(
    "4989CA"          # mov r10, rcx
    "4989D8"          # mov r8, rbx
    "4989C1"          # mov r9, rax
    "B8CA000000"      # mov eax, 202
    "0F05"            # syscall
    "C3"              # ret
)


def normalize_kernel_fw_version(raw_fw_version: int) -> int:
    # Confirmed on FW 12.00. Needs real-console validation on FW 9.00,
    # 10.50, and 11.00.
    if raw_fw_version <= 0:
        raise FirmwareDetectionError(f"invalid raw firmware value: 0x{raw_fw_version:X}")

    if raw_fw_version <= 9999:
        fw_version = raw_fw_version
    else:
        fw_version = int(
            f"{(raw_fw_version >> 24) & 0xFF:02x}"
            f"{(raw_fw_version >> 16) & 0xFF:02x}"
        )

    return {
        900: 9,
        1100: 11,
    }.get(fw_version, fw_version)


def _process_name(process: Any) -> str:
    return str(getattr(process, "name", "")).replace("\x00", "").rstrip("\x00")


async def _get_sysctl_process(ps4: PS4Debug) -> Any:
    processes = await _timeout("get_processes", ps4.get_processes())

    preferred_names = ("SceShellUI", "SceShellCoreelf")
    for preferred_name in preferred_names:
        process = next((p for p in processes if _process_name(p) == preferred_name), None)
        if process is not None:
            return process

    process = next((p for p in processes if _process_name(p).startswith("SceShellCore")), None)
    if process is not None:
        return process

    raise FirmwareDetectionError("could not find SceShellUI/SceShellCore process")


async def _sysctl(
    ps4: PS4Debug,
    pid: int,
    stub_addr: int,
    rpc_stub: int,
    name_addr: int,
    name_count: int,
    oldp_addr: int,
    oldlenp_addr: int,
    newp_addr: int,
    newlen: int,
) -> int:
    result = await _timeout(
        "__sysctl RPC call",
        ps4.call(
            pid,
            stub_addr,
            name_addr,
            name_count,
            oldp_addr,
            oldlenp_addr,
            newp_addr,
            newlen,
            rpc_stub=rpc_stub,
        ),
    )

    if result is None:
        raise FirmwareDetectionError("__sysctl RPC call failed")

    return int(result[0])


def _map_name(process_map: Any) -> str:
    return str(getattr(process_map, "name", "")).replace("\x00", "").rstrip("\x00")


def _map_len(process_map: Any) -> int:
    return int(process_map.end) - int(process_map.start)


async def _read_map(ps4: PS4Debug, pid: int, process_map: Any) -> bytes | None:
    return await _timeout(
        f"read map {_map_name(process_map)} 0x{int(process_map.start):X}",
        ps4.read_memory(pid, int(process_map.start), _map_len(process_map)),
    )


async def _find_libkernel_string(ps4: PS4Debug, pid: int, maps: list[Any], needle: bytes) -> int:
    for process_map in maps:
        if not (_map_name(process_map) == "libkernel_sys.sprx" and process_map.prot & 1):
            continue

        data = await _read_map(ps4, pid, process_map)
        if data is None:
            continue

        offset = data.find(needle)
        if offset != -1:
            return int(process_map.start) + offset

    raise FirmwareDetectionError(f"could not find {needle!r} in libkernel_sys.sprx")


async def _find_libkernel_xref_function(ps4: PS4Debug, pid: int, maps: list[Any], target_addr: int) -> int:
    prologue = b"\x55\x48\x89\xE5"

    for process_map in maps:
        if not (_map_name(process_map) == "libkernel_sys.sprx" and process_map.prot & 4):
            continue

        data = await _read_map(ps4, pid, process_map)
        if data is None:
            continue

        base = int(process_map.start)
        for disp_offset in range(0, len(data) - 4):
            disp = struct.unpack_from("<i", data, disp_offset)[0]
            if base + disp_offset + 4 + disp != target_addr:
                continue

            instr_offset = disp_offset - 3
            if instr_offset < 0 or data[instr_offset:disp_offset] != b"\x48\x8D\x3D":
                continue

            search_start = max(0, instr_offset - 0x180)
            prologue_offset = data.rfind(prologue, search_start, instr_offset)
            if prologue_offset != -1:
                return base + prologue_offset

    raise FirmwareDetectionError("could not find libkernel updater-version wrapper")


async def _get_process_maps(ps4: PS4Debug, pid: int) -> list[Any]:
    return await _timeout("get_process_maps", ps4.get_process_maps(pid))


async def _get_or_install_rpc_stub(ps4: PS4Debug, pid: int, maps: list[Any]) -> int:
    existing_stub = next(
        (int(process_map.start) for process_map in maps if _map_name(process_map) == "(NoName)clienthandler"),
        None,
    )
    if existing_stub is not None:
        _debug(f"firmware detection existing rpc_stub = 0x{existing_stub:X}")
        return existing_stub

    _debug("firmware detection installing rpc_stub")
    rpc_stub = await _timeout("install_rpc", ps4.install_rpc(pid))
    if rpc_stub is None:
        raise FirmwareDetectionError("could not install ps4debug RPC stub")

    _debug(f"firmware detection rpc_stub = 0x{int(rpc_stub):X}")
    return int(rpc_stub)


async def _detect_via_libkernel_wrapper(ps4: PS4Debug, pid: int, rpc_stub: int, maps: list[Any]) -> int:
    _debug("trying libkernel wrapper firmware detection")
    string_addr = await _find_libkernel_string(ps4, pid, maps, b"machdep.upd_version\x00")
    _debug(f"machdep.upd_version string = 0x{string_addr:X}")
    function_addr = await _find_libkernel_xref_function(ps4, pid, maps, string_addr)
    _debug(f"updater-version wrapper = 0x{function_addr:X}")

    value_addr = await _timeout("allocate firmware value memory", ps4.allocate_memory(pid, 8))
    if value_addr is None:
        raise FirmwareDetectionError("could not allocate firmware value memory")

    try:
        await _timeout("zero firmware value memory", ps4.write_memory(pid, value_addr, b"\x00" * 8))
        result = await _timeout(
            "libkernel updater-version wrapper call",
            ps4.call(pid, function_addr, value_addr, rpc_stub=rpc_stub),
        )
        if result is None:
            raise FirmwareDetectionError("libkernel updater-version wrapper call failed")

        ret = int(result[0]) & 0xFFFFFFFF
        if ret != 0:
            raise FirmwareDetectionError(f"libkernel updater-version wrapper failed: 0x{ret:08X}")

        raw_value = await _timeout("read firmware value", ps4.read_memory(pid, value_addr, 8))
        if raw_value is None:
            raise FirmwareDetectionError("could not read firmware value")

        raw_fw_version = int.from_bytes(raw_value[:4], "little")
        _debug(f"raw firmware from libkernel wrapper = 0x{raw_fw_version:X}")
        return normalize_kernel_fw_version(raw_fw_version)
    finally:
        await ps4.free_memory(pid, value_addr, 8)


async def detect_ps4_firmware_version(ps4: PS4Debug) -> int:
    process = await _get_sysctl_process(ps4)
    pid = int(process.pid)
    _debug(f"firmware detection process = {_process_name(process)} pid={pid}")

    maps = await _get_process_maps(ps4, pid)
    rpc_stub = await _get_or_install_rpc_stub(ps4, pid, maps)

    try:
        return await _detect_via_libkernel_wrapper(ps4, pid, rpc_stub, maps)
    except FirmwareDetectionTimeout:
        raise
    except FirmwareDetectionError as wrapper_error:
        _debug(f"libkernel wrapper failed: {wrapper_error}, trying direct sysctl")

    stub_addr = await _timeout("allocate sysctl stub memory", ps4.allocate_memory(pid, len(_SYSCTL_STUB)))
    if stub_addr is None:
        raise FirmwareDetectionError("could not allocate sysctl stub memory")

    data_addr = await _timeout("allocate sysctl data memory", ps4.allocate_memory(pid, 0x100))
    if data_addr is None:
        await ps4.free_memory(pid, stub_addr, len(_SYSCTL_STUB))
        raise FirmwareDetectionError("could not allocate sysctl data memory")

    try:
        await _timeout("write sysctl stub", ps4.write_memory(pid, stub_addr, _SYSCTL_STUB))

        ctl_name_addr = data_addr
        mib_addr = data_addr + 0x10
        mib_len_addr = data_addr + 0x80
        value_addr = data_addr + 0x90
        value_len_addr = data_addr + 0x98
        sysctl_name_addr = data_addr + 0xA0

        sysctl_name = b"machdep.upd_version\x00"

        await _timeout("write sysctl name", ps4.write_memory(pid, ctl_name_addr, struct.pack("<II", CTL_SYSCTL, CTL_SYSCTL_NAME2OID)))
        await _timeout("write sysctl mib length", ps4.write_memory(pid, mib_len_addr, struct.pack("<Q", CTL_MAXNAME * 4)))
        await _timeout("write sysctl string", ps4.write_memory(pid, sysctl_name_addr, sysctl_name))

        result = await _sysctl(
            ps4,
            pid,
            stub_addr,
            rpc_stub,
            ctl_name_addr,
            2,
            mib_addr,
            mib_len_addr,
            sysctl_name_addr,
            len(sysctl_name) - 1,
        )
        if result != 0:
            raise FirmwareDetectionError(f"name2oid sysctl failed: errno={result}")

        mib_len_bytes = struct.unpack("<Q", await _timeout("read sysctl mib length", ps4.read_memory(pid, mib_len_addr, 8)))[0]
        if mib_len_bytes == 0 or mib_len_bytes % 4 != 0 or mib_len_bytes > CTL_MAXNAME * 4:
            raise FirmwareDetectionError(f"invalid machdep.upd_version mib length: {mib_len_bytes}")

        mib_count = mib_len_bytes // 4

        await _timeout("zero sysctl value memory", ps4.write_memory(pid, value_addr, b"\x00" * 8))
        await _timeout("write sysctl value length", ps4.write_memory(pid, value_len_addr, struct.pack("<Q", 8)))

        result = await _sysctl(
            ps4,
            pid,
            stub_addr,
            rpc_stub,
            mib_addr,
            mib_count,
            value_addr,
            value_len_addr,
            0,
            0,
        )
        if result != 0:
            raise FirmwareDetectionError(f"machdep.upd_version sysctl failed: errno={result}")

        value_len = struct.unpack("<Q", await _timeout("read sysctl value length", ps4.read_memory(pid, value_len_addr, 8)))[0]
        if value_len == 0 or value_len > 8:
            raise FirmwareDetectionError(f"invalid machdep.upd_version value length: {value_len}")

        raw_value = await _timeout("read sysctl firmware value", ps4.read_memory(pid, value_addr, 8))
        raw_fw_version = int.from_bytes(raw_value[:value_len], "little")

        _debug(f"raw firmware from machdep.upd_version = 0x{raw_fw_version:X}")
        return normalize_kernel_fw_version(raw_fw_version)
    finally:
        await ps4.free_memory(pid, data_addr, 0x100)
        await ps4.free_memory(pid, stub_addr, len(_SYSCTL_STUB))
