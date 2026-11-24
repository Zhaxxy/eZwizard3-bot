from ps4debug import PS4Debug

try:
    from ._raw_save_mount_functions import patch_memory_for_saves_900, mount_save, unmount_save, MemoryIsPatched, SceSaveDataMountResult
except ImportError:
    from _raw_save_mount_functions import patch_memory_for_saves_900, mount_save, unmount_save, MemoryIsPatched, SceSaveDataMountResult

class PatchMemoryPS4900:
    def __init__(self, ps4: PS4Debug, fw_version: int) -> None:
        self.ps4 = ps4
        self.fw_version = fw_version

    async def __aenter__(self) -> MemoryIsPatched:
        self.mem = await patch_memory_for_saves_900(self.ps4, self.fw_version)
        return self.mem

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await self.mem._remove_patches(self.ps4)

class MountSave:
    def __init__(
        self,
        ps4: PS4Debug,
        mem: MemoryIsPatched,
        user_id: int,
        title_id: str,
        save_dir: str,
        mount_mode: int = 0x8 | 2,
        blocks: int = 32_768,
    ) -> None:
        self.ps4 = ps4
        self.mem = mem
        self.user_id = user_id
        self.title_id = title_id
        self.save_dir = save_dir
        self.mount_mode = mount_mode
        self.blocks = blocks

    async def __aenter__(self) -> SceSaveDataMountResult:
        self.mp = await mount_save(
            self.ps4,
            self.mem,
            self.user_id,
            self.title_id,
            self.save_dir,
            self.mount_mode,
            self.blocks,
        )

        if self.mp:
            print(f'[OK] Mount done : {self.save_dir}')
        else:
            print(
                f'[FAIL] Mount false : {self.save_dir} | '
                f'error=0x{self.mp.error_code & 0xffffffff:08X} | '
                f'mount_point={self.mp.SceSaveDataMountPoint!r}'
            )

        return self.mp

    async def __aexit__(self, exc_type=None, exc_value=None, exc_traceback=None):
        if self.mp:
            await unmount_save(self.ps4, self.mem, self.mp)
