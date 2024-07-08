import struct
from typing import NamedTuple, BinaryIO

class _SelfHeader(NamedTuple):
    """
    https://github.com/Scene-Collective/ps4-payload-sdk/blob/ffcd53412e40d9b5d80775912ce4d071faa68d96/libPS4/include/elf.h#L23
    """
    magic: int # File magic
    
    # unknown: int # Always 00 01 01 12.
    version: int
    mode: int
    endian: int
    attr: int
    
    content_type: int # 1 ib Self, 4 on PUP Entry
    program_type: int # 0x0 PUP, 0x8 NPDRM Application, 0x9 PLUGIN, 0xC Kernel, 0xE Security Module, 0xF Secure Kernel
    padding: int 
    header_size: int
    signature_size: int # Metadata size?
    self_size: int 
    num_of_segments: int # Number of Segments, 1 Kernel, 2 SL and Modules, 4 Kernel ELFs, 6 .selfs, 2 .sdll, 6 .sprx, 6 ShellCore, 6 eboot.bin, 2 sexe. 
    flags: int # Always 0x22
    reserved: int
    
    STRUCT_FORMAT_STR = '<I6B3HQ2HI'
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT_STR)
    
    @classmethod
    def from_bytes(cls, the_bytes: bytes) -> '_SelfHeader':
        return cls(*struct.unpack(cls.STRUCT_FORMAT_STR,the_bytes))

    @classmethod
    def from_buffer(cls, the_buffer: BinaryIO) -> '_SelfHeader':
        return cls.from_bytes(the_buffer.read(cls.STRUCT_SIZE))


class _Elf64_Ehdr(NamedTuple):
    e_ident: bytes # File identification of length 16
    e_type: int # File type
    e_machine: int # Machine architecture
    e_version: int # ELF format version.
    e_entry: int # Entry point
    e_phoff: int # Program header file offset
    e_shoff: int # Section header file offset
    e_flags: int # Architecture-specific flags.
    e_ehsize: int # Size of ELF header in bytes.
    e_phentsize: int # Size of program header entry.
    e_phnum: int # Number of program header entries.
    e_shentsize: int # Size of section header entry.
    e_shnum: int # Number of section header entries
    e_shstrndx: int # Section name strings section

    STRUCT_FORMAT_STR = '<16s2HI3QI6H'
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT_STR)
    
    @classmethod
    def from_bytes(cls, the_bytes: bytes) -> '_Elf64_Ehdr':
        return cls(*struct.unpack(cls.STRUCT_FORMAT_STR,the_bytes))

    @classmethod
    def from_buffer(cls, the_buffer: BinaryIO) -> '_Elf64_Ehdr':
        return cls.from_bytes(the_buffer.read(cls.STRUCT_SIZE))


class _SceHeader(NamedTuple):
    """
    // SCE Header from: https://www.psdevwiki.com/ps4/SELF_File_Format#SCE_Special
    """
    program_authority_id: int
    program_type: int
    app_version: int
    fw_version: int
    digest: bytes
    
    STRUCT_FORMAT_STR = '<4Q32s'
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT_STR)
    
    @classmethod
    def from_bytes(cls, the_bytes: bytes) -> '_SceHeader':
        return cls(*struct.unpack(cls.STRUCT_FORMAT_STR,the_bytes))

    @classmethod
    def from_buffer(cls, the_buffer: BinaryIO) -> '_SceHeader':
        return cls.from_bytes(the_buffer.read(cls.STRUCT_SIZE))


_SELF_ENTRY_SIZE = 4 + 4 + 8 + 8 + 8 # uint32_t props; uint32_t reserved; uint64_t offset; uint64_t file_size; uint64_t memory_size;


def get_fw_version(libc_sprx_file: BinaryIO) -> int:
    self_header = _SelfHeader.from_buffer(libc_sprx_file)
    elf_header_offset = self_header.STRUCT_SIZE + self_header.num_of_segments * _SELF_ENTRY_SIZE

    libc_sprx_file.seek(elf_header_offset)

    elf_header = _Elf64_Ehdr.from_buffer(libc_sprx_file)

    sce_header_offset = elf_header_offset + elf_header.e_ehsize + elf_header.e_phnum * elf_header.e_phentsize

    while sce_header_offset % 0x10 != 0:
        sce_header_offset += 1

    libc_sprx_file.seek(sce_header_offset)
    raw_fw_version = _SceHeader.from_buffer(libc_sprx_file).fw_version
    if raw_fw_version <= 9999:
        return raw_fw_version
    string_fw = f'{(raw_fw_version >> (5 * 8)) & 0xFF:02x}{(raw_fw_version >> (4 * 8)) & 0xFF:02x}'
    return int(string_fw)


def main() -> int:
    with open('libc.sprx','rb') as f:
        e = get_fw_version(f)
    print(e)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
