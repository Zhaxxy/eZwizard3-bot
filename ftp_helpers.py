# import asyncio
# import aioftp
# from pathlib import Path

# FTP_IP = '192.168.1.221'


# # async def upload_folder_contents(ftp: aioftp.Client,folder2upload: Path | str, dest: Path | str = ''):
# #     folder2upload = Path(folder2upload)
# #     for file in folder2upload.rglob('*'):
# #         if file.is_dir():
# #             await ftp.make_directory(Path('/',file.relative_to(folder2upload)))
# #             continue
# #         file = file.relative_to(folder2upload)
# #         new_folder = Path('/',dest,file.parent).as_posix()
# #         # print(new_folder)
# #         await ftp.make_directory(new_folder)
# #         await ftp.change_directory(new_folder)
# #         await ftp.upload(file)

    
# async def main():
#     async with aioftp.Client.context(FTP_IP, 2121) as ftp:
#         mount_dir = '/mnt/sandbox/NPXS20001_000/savedata0'
#         decrypted_save_file = Path(r'C:\coding_projects\PS4 4.50 SDK Offline Installer\PlayStation 4 SDK 4.50 Manual')
#         parent_mount, mount_last_name = Path(mount_dir).parent.as_posix(), Path(mount_dir).name
#         await ftp.change_directory(parent_mount)
        
        
#         await ftp.upload(decrypted_save_file / 'savedata0',mount_last_name,write_into=True)


# if __name__ == '__main__':
#     asyncio.run(main())