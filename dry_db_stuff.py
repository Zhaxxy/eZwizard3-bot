import tempfile 
from typing import BinaryIO, NamedTuple
from pathlib import Path
import subprocess
import hashlib

from lbptoolspy.l0_dec_enc import decrypt_ps4_l0, encrypt_ps4_l0
from lbptoolspy import extract_far4, SaveKey, pack_far4
from lbptoolspy.binary_files import JSONINATOR_ARGS
import ujson as json

L0_SAVE_KEY = 'f9031802000000004e8f3f1000000000000000000000000000000000000000000000000000000000000000000000000000000000000300001d0000000000000000000000000000003b3b44be9f7f591342484b3c6210100c37263f1100000000000000000000000000000000000000000000000000000000000000000000000000000000'

class LevelNameLevelDesc(NamedTuple):
    name: str
    desc: str
    is_adventure: bool
    icon0: Path | None | bytes
    
UMWHATDASIGMA = """
{
  "revision": 35128313,
  "type": "SLOT_LIST",
  "resource": {
    "slots": [
      {
        "id": "FAKE:0",
        "root": {
          "value": "ceb0b24130019a7b133b5625b80c21d19d7a69e3",
          "type": "LEVEL"
        },
        "adventure": null,
        "icon": {
          "value": 288514,
          "type": "TEXTURE"
        },
        "location": [
          0.4678959,
          0.87881374,
          0.09359398,
          0.0
        ],
        "authorID": "",
        "authorName": "",
        "translationTag": "",
        "name": "Ben",
        "description": "Ggg",
        "primaryLinkLevel": "NONE",
        "group": "NONE",
        "initiallyLocked": false,
        "shareable": false,
        "backgroundGUID": 405678,
        "developerLevelType": "MAIN_PATH",
        "planetDecorations": {
          "value": 250423,
          "type": "PLAN"
        },
        "labels": [],
        "collectabubblesRequired": [
          {
            "plan": null,
            "count": 0
          },
          {
            "plan": null,
            "count": 0
          },
          {
            "plan": null,
            "count": 0
          }
        ],
        "collectabubblesContained": [],
        "isSubLevel": false,
        "minPlayers": 1,
        "maxPlayers": 4,
        "moveRecommended": false,
        "crossCompatible": false,
        "showOnPlanet": true,
        "livesOverride": 0,
        "enforceMinMaxPlayers": false,
        "gameMode": 0,
        "isGameKit": false,
        "entranceName": "",
        "originalSlotID": "NONE",
        "customBadgeSize": 1,
        "localPath": "",
        "thumbPath": ""
      }
    ],
    "fromProductionBuild": true
  }
}"""


def ps3_level_backup_to_l0_ps4(level_backup_folder_path: Path | str, l0_output: BinaryIO) -> LevelNameLevelDesc:
    level_backup_folder_path = Path(level_backup_folder_path)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        decrypted_files = Path(temp_dir,'decrypted_files')
        decrypted_files.mkdir()
        far4s = Path(temp_dir,'far4s')
        far4s.mkdir()
        icon0_thing = None
        save_files = []
        for file in level_backup_folder_path.iterdir():
            if file.name.upper() in ('PARAM.PFD','PARAM.SFO','ICON0.PNG'):
                if file.name.upper() == 'ICON0.PNG':
                    icon0_thing = file
                continue
            save_files.append(file)
        
        save_files.sort(key = lambda x: int(x.name))
        enc_bytes = []
        for i,save_file in enumerate(save_files):
            if i == len(save_files)-1:
                enc_bytes.append(decrypt_ps4_l0(save_file.read_bytes()))
            else:
                enc_bytes.append(decrypt_ps4_l0(save_file.read_bytes(),has_footer=False))
        enc_bytes = b''.join(enc_bytes)
        
        (decrypted_files / 'PARAM.PFD').write_bytes((enc_bytes))
        
        slt_savekey = extract_far4(decrypted_files / 'PARAM.PFD',far4s)
        
        slt_file = far4s / (slt_savekey.root_resource_hash.hex() + '.slt')
        if not slt_file.is_file():
            raise ValueError('Could not find slt file, possible is a malicous level backup')
        

        json_res = subprocess.run(JSONINATOR_ARGS + (slt_file,slt_file.with_suffix('.json')),capture_output = True, shell=False)
        succy = True
        if not json_res.returncode:
            try:
                new_slt_dict = json.loads(slt_file.with_suffix('.json').read_text(encoding="utf-8"))
            except Exception:
                raise
            else:
                try:
                    level_name = new_slt_dict["resource"]["slots"][0]["name"]
                except (KeyError,IndexError):
                    level_name = 'Unnamed Level'
                try:
                    level_desc = new_slt_dict["resource"]["slots"][0]["description"]
                except (KeyError,IndexError):
                    level_desc = 'There is no description for this level'
                # try:
                    # is_adventure = bool(new_slt_dict["resource"]["slots"][0]["adventure"])
                # except (KeyError,IndexError):
                    # is_adventure = False
                try:
                    icon_tex_hash = new_slt_dict["resource"]["slots"][0]["icon"]["value"]
                    if not (isinstance(icon_tex_hash,str) and len(icon_tex_hash) == 40):
                        icon_tex_hash = None
                except (KeyError,IndexError):
                    icon_tex_hash = None
                succy = False
        if succy:
            level_name = 'Failed to parse slt file'
            level_desc = f'{json_res.returncode} error: {json_res.stdout}{json_res.stderr}'
            icon_tex_hash = None
        is_adventure = 'ADV' in level_backup_folder_path.name.upper()
        # new_slt_dict['revision'] = 35128313
        # new_slt_dict = json.loads(UMWHATDASIGMA)
        
        # for file in far4s.iterdir():
            # if file.suffix == '.bin':
                # new_slt_dict['resource']['slots'][0]['root']['value'] = file.stem
                # break
        # else:
            # raise ValueError('UMWHATDASIGMA')
        # slt_file.with_suffix('.json').write_text(json.dumps(new_slt_dict))
        
        # a = subprocess.run(JSONINATOR_ARGS + (slt_file.with_suffix('.json'),slt_file),capture_output = True, shell=False)

        # assert not a.returncode, a.returncode
        
        decrypted_l0 = Path(temp_dir,'decrypted_l0')
        
        slt_file_hash = hashlib.sha1()
        slt_file_hash.update(slt_file.read_bytes())
        
        # Path(far4s,'ben.bin').write_bytes(b'g'*(34603008))
        
        if icon_tex_hash:
            if Path(far4s / icon_tex_hash).is_file():
                icon0_thing = Path(far4s / icon_tex_hash).name
        
        pack_far4(far4s,decrypted_l0,SaveKey.from_string(L0_SAVE_KEY),slt_file_hash.digest())
        l0_output.write(encrypt_ps4_l0(decrypted_l0.read_bytes()))
        
        return LevelNameLevelDesc(level_name,level_desc,is_adventure,icon0_thing)


# with open('cart23.bin','wb') as f:
    # ps3_level_backup_to_l0_ps4('BCES00850LEVEL008CEDA6',f)