import asyncio
from pathlib import Path
import json
import sys 

try:
    __file__ = sys._MEIPASS
except:
    pass
else:
    __file__ = str(Path(__file__,'huh.huh'))

ERROR_CODE_LONG_NAMES: dict[int,str] = {int(key):value for key,value in  json.loads(Path(Path(__file__).parent / 'error_codes.json').read_text()).items()}
PS4_DEBUG = (Path(__file__).parent / 'ps4debug.bin').read_bytes()

async def send_ps4debug(ip: str,/,port: int = 9090):
    """
    Simple function to send over da ps4 debug bin
    """
    _, writer = await asyncio.open_connection(ip, port)
    writer.write(PS4_DEBUG)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    await asyncio.sleep(1)
