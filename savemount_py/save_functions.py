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


async def is_tcp_port_open(ip: str, port: int) -> bool:
    try:
        _, writer = await asyncio.open_connection(ip, port)
        writer.close()
        await writer.wait_closed()
        return True
    except ConnectionRefusedError:
        return False


async def send_ps4debug(ip: str,/,port: int = 9090) -> None:
    """
    Simple function to send over da ps4 debug bin
    """
    is_ps4_debug_injected = await is_tcp_port_open(ip,744)
    if is_ps4_debug_injected:
        print('ps4debug already injected, no need to inject again')
        return
    _, writer = await asyncio.open_connection(ip, port)
    writer.write(PS4_DEBUG)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    await asyncio.sleep(1)


async def main() -> int:
    while True:
        ip = input('Enter the ip of your ps4 to inject ps4debug: ')
        if not ip:
            print('Please enter an ip')
            continue
        break
    
    while True:
        port = input('Enter in bin loader port (default 9090): ') or '9090'
        try:
            port_num = int(port)
        except ValueError:
            print(f'Invalid port number {port}')
            continue
        break
    
    await send_ps4debug(ip,port)
    input('Injected, press enter to exit... ')#
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))