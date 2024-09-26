import json
import asyncio
from pathlib import Path
from typing import Sequence,Generator, NamedTuple
import os
import json

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import UserCreds, ClientCreds
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from string_helpers import is_ps4_title_id, extract_drive_folder_id, load_config


class GDriveFile(NamedTuple):
    """\
    This messes up when you use exact same file names in same path, but its your own fault for doing that lol, itll probs just chose one of the duplicates
    """
    file_name_as_path: Path
    file_id: Path
    size: int
    is_file: bool

    # def __hash__(self) -> int:
    #     return hash(self.file_name_as_path)

    # def __eq__(self, value: 'GDriveFile') -> bool:
    #     return self.file_name_as_path == value.file_name_as_path


class PS4GDriveFileSave(NamedTuple):
    bin_file: GDriveFile
    white_file: GDriveFile


def load_creds(cred_json_name: str = "credentials.json"):
    creds = None
    creds_file = Path("DO_NOT_DELETE_automatically_generated_gdrive_token.json")
    if creds_file.exists():
        creds = Credentials.from_authorized_user_file(
            "DO_NOT_DELETE_automatically_generated_gdrive_token.json",
            ["https://www.googleapis.com/auth/drive"],
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                cred_json_name, ["https://www.googleapis.com/auth/drive"]
            )
            creds = flow.run_local_server(port=0)
        with creds_file.open("w") as f:
            f.write(creds.to_json())
    build("drive", "v3", credentials=creds)

CONFIG = load_config()

try:
    load_creds(CONFIG['google_credentials_file'])
except Exception:
    try:
        os.remove("DO_NOT_DELETE_automatically_generated_gdrive_token.json")
    except Exception:
        pass
    load_creds(CONFIG['google_credentials_file'])

_user_creds_dict = json.load(open('DO_NOT_DELETE_automatically_generated_gdrive_token.json'))
_USER_CREDS = UserCreds(
    access_token = _user_creds_dict['token'],
    refresh_token = _user_creds_dict['refresh_token'],
    token_uri = _user_creds_dict['token_uri'],
    scopes = _user_creds_dict['scopes'],
    # id_token = _user_creds_dict['client_id'],
)


_client_creds_dict = json.load(open('credentials.json'))
try:
    _client_creds_dict = _client_creds_dict['installed']
except KeyError:
    _client_creds_dict = _client_creds_dict['web']
_CLIENT_CREDS = ClientCreds(
    client_id = _client_creds_dict['client_id'],
    client_secret = _client_creds_dict['client_secret'],
    scopes = _user_creds_dict['scopes'],
    redirect_uri = _client_creds_dict['redirect_uris'][0]
)
def agg() -> Aiogoogle:
    return Aiogoogle(user_creds=_USER_CREDS, client_creds=_CLIENT_CREDS)



async def make_gdrive_folder(foldername: str, parent_folder_id: str = '',make_public: bool = False) -> str:
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        if not parent_folder_id:
            response = await ag.as_user(service.files.list(q = f"name='{foldername}' and mimeType='application/vnd.google-apps.folder'", spaces= 'drive'))
            if not response['files']:
                result = (await ag.as_user(service.files.create(json={'name':foldername,'mimeType':'application/vnd.google-apps.folder'},fields='id')))['id']
            else:
                result = response['files'][0]['id']
        else:
            response = await ag.as_user(service.files.list(q=f"name='{foldername}' and '{parent_folder_id}' in parents",spaces='drive'))
            if not response['files']:
                result = await ag.as_user(service.files.create(json={'name':foldername,'mimeType':'application/vnd.google-apps.folder','parents': (parent_folder_id,)},fields='id'))['id']
            else:
                result = response['files'][0]['id']
        
        if make_public:
            await ag.as_user(service.permissions.create(fileId=result, json={'type':'anyone','role':'reader'}))
    return result


async def list_files_in_gdrive_folder(parent_folder_id: str, parent_path: str | Path,skip_folders:bool = True,*,_lst: dict = None) -> dict[Path,GDriveFile]:
    if _lst is None:
        root = await get_folder_info_from_id(parent_folder_id)
        _lst = {root.file_name_as_path: root}
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        results = await ag.as_user(service.files.list(q=f"'{parent_folder_id}' in parents",fields="files(id, name, mimeType, size)"))
        results = results.get('files', [])
    
    for file in results:
        file_name_path = Path(parent_path, file['name'])
        file_id = file['id']
        file_mime_type = file['mimeType']
        if 'application/vnd.google-apps.folder' in file_mime_type:
            folder_path = file_name_path
            await list_files_in_gdrive_folder(file_id, folder_path,_lst = _lst)
            if skip_folders:
                continue
        _lst[file_name_path] = GDriveFile(file_name_path,file_id,int(file.get('size',0)),'application/vnd.google-apps.folder' not in file_mime_type)
    return _lst


async def gdrive_folder_link_to_name(folder_id: str) -> str:
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        result = await ag.as_user(service.files.get(fileId=folder_id, fields="name"))
        return result['name']


class _PathWithNoIDInHash:
    def __init__(self,file_thing: GDriveFile):
        self.file_thing = file_thing
    
    def __hash__(self):
        return hash(self.file_thing[0])
    
    def __eq__(self,other):
        return self.file_thing[0] == other.file_thing[0]

    def __getitem__(self,index):
        return self.file_thing[index]
    
    def __repr__(self):
        return f'{type(self).__name__}({self.file_thing!r})'


def _get_valid_saves_out_names_only(the_folder: Sequence[GDriveFile]) -> Generator[PS4GDriveFileSave, None, None]:
    """
    this function messes up if you use exact same path, but who tf be doing that
    """
    no_ids = {_PathWithNoIDInHash(x): x for x in the_folder}

    if sum((not x.is_file) for x in the_folder) <= 1:
        res: list[PS4GDriveFileSave] = []
        for filepath in no_ids:
            if filepath.file_thing.file_name_as_path.name.startswith('._'): continue
            if not filepath.file_thing.is_file: continue
            
            if filepath.file_thing.file_name_as_path.suffix != '.bin':
                bin_file = no_ids.get(_PathWithNoIDInHash((filepath.file_thing.file_name_as_path.with_suffix('.bin'),'')))
                if not bin_file: # If we are gonna allow this, we are not gonna say its supported, and defiently not accepting any bad data, so say theres no saves
                    return
                res.append(PS4GDriveFileSave(bin_file,no_ids[filepath]))
        yield from res
        return
        
    for filepath in no_ids:
        if '__MACOSX' in filepath.file_thing.file_name_as_path.parts and (not filepath.file_thing.is_file): continue
        if filepath.file_thing.file_name_as_path.name.startswith('._'): continue
        if is_ps4_title_id(filepath.file_thing.file_name_as_path.parent.name):
            if filepath.file_thing.file_name_as_path.name.endswith('.bin') and filepath.file_thing.is_file:
                try:
                    white_file = no_ids[_PathWithNoIDInHash((filepath.file_thing.file_name_as_path.with_suffix(''),''))]
                except KeyError:
                    pass
                else:
                    if white_file.is_file:
                        yield PS4GDriveFileSave(no_ids[filepath],white_file)
            else:
                try:
                    bin_file = no_ids[_PathWithNoIDInHash((filepath.file_thing.file_name_as_path.with_suffix('.bin'),''))]
                except KeyError:
                    pass
                else:
                    if bin_file.is_file:
                        yield PS4GDriveFileSave(bin_file,no_ids[filepath])

def get_valid_saves_out_names_only(the_folder: Sequence[GDriveFile]) -> set[PS4GDriveFileSave]:
    return {x for x in _get_valid_saves_out_names_only(the_folder)}


async def get_gdrive_folder_size(folder_id: str) -> tuple[int, int]:
    total_size = 0
    total_files = 0

    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        results = await ag.as_user(
            service.files.list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, size, mimeType)"
            )
        )

    for file in results.get('files', []):
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            # If it's a folder, recursively get its size
            folder_size, num_files = await get_gdrive_folder_size(file['id'])
            total_size += folder_size
            total_files += num_files
        else:
            total_size += int(file.get('size', 0))
            total_files += 1

    return total_size, total_files


async def get_file_or_folder_info_from_id(file_id_or_folder_id: str) -> GDriveFile:
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        response = await ag.as_user(
            service.files.get(fileId=file_id_or_folder_id, fields='name, size, mimeType')
        )
        return GDriveFile(Path(response['name']),file_id_or_folder_id,int(response['size']),response['mimeType'] != 'application/vnd.google-apps.folder')


async def get_file_info_from_id(file_id: str) -> GDriveFile:
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        response = await ag.as_user(
            service.files.get(fileId=file_id, fields='name, size, mimeType')
        )

        if response['mimeType'] == 'application/vnd.google-apps.folder':
            raise ValueError('Folder id was passed, not a file id')

        return GDriveFile(Path(response['name']),file_id,int(response['size']),True)


async def get_folder_info_from_id(folder_id: str) -> GDriveFile:
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        response = await ag.as_user(
            service.files.get(fileId=folder_id, fields='name, mimeType')
        )

        if response['mimeType'] != 'application/vnd.google-apps.folder':
            raise ValueError('Folder id was not passed')

        return GDriveFile(Path(response['name']),folder_id,0,False)


async def download_folder(folder_id: str, dest_path: Path | str):
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        results = await ag.as_user(service.files.list(q=f"'{folder_id}' in parents and trashed=false",fields="files(id, name, mimeType)"))
    # if len(results['files']) > 0x6_4:
        # return False
    
    for file in results.get('files', []):
        file_name = file['name']
        file_id = file['id']
        file_mime_type = file['mimeType']

        file_path = Path(dest_path, file_name)

        if file_mime_type == 'application/vnd.google-apps.folder':
            os.makedirs(file_path, exist_ok=True)
            await download_folder(file_id, file_path)
        else:
            os.makedirs(Path(file_path).parent,exist_ok=True)
            await download_file(file_id,file_path)


async def download_file(file_id: str, dir_path: Path | str):
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        info_res = await ag.as_user(service.files.get(fileId=file_id))
        Path(dir_path).parent.mkdir(parents=True,exist_ok=True)
        await ag.as_user(
            service.files.get(fileId=file_id, download_file=dir_path, alt="media"),
            full_res=True,
        )
        # print("Downloaded file to {} successfully!".format(dir_path))


async def google_drive_upload_file(file2upload: Path, folder_id: str, make_public: bool = True) -> str:
    file2upload = Path(file2upload)
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        req = service.files.create(
            upload_file=file2upload,
            fields = ('id, webContentLink'),
            json={"name": file2upload.name, "parents":(folder_id,)}
        )
        # req.upload_file_content_type = mimetypes.guess_type(file2upload)[0]
        upload_res = await ag.as_user(req)
        if make_public:
            await ag.as_user(service.permissions.create(fileId=upload_res['id'], json={'type':'anyone','role':'reader'}))
    return upload_res['webContentLink']


async def delete_google_drive_file_or_file_permentaly(thefileid: str, /):
    async with agg() as ag:
        service = await ag.discover("drive", "v3")
        await ag.as_user(service.files.delete(fileId=thefileid))


async def main():
    # a = await list_files_in_gdrive_folder('17gymS1K07HYv5JpDvtdSSv67FOT-jG4Z',await gdrive_folder_link_to_name('17gymS1K07HYv5JpDvtdSSv67FOT-jG4Z'))
    # from pprint import pprint as pp
    
    # print('YO')
    # pp(a)

    # # pp(get_valid_saves_out_names_only(a))
    # # print(await get_gdrive_folder_size('17gymS1K07HYv5JpDvtdSSv67FOT-jG4Z'))
    
    # a = await google_drive_upload_file('requirements.txt','1LMTVk-QBYKgK4Fe7ajT4U_DTtpTXAp34')
    # print(a)
    # async with agg() as ag:
        # service = await ag.discover("drive", "v3")
        # await ag.as_user(service.files.delete(fileId='1HzrPW9l445zjYhO3lcexQCwAGY48nfvV'))

    print('why you running me lil bro')


if __name__ == "__main__":
    asyncio.run(main())
