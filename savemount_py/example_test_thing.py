# import asyncio
# import time

# from ps4debug import PS4Debug

# from save_mount_unmount import PatchMemoryPS4900,MountSave

# async def main(ps4_ip: str = '1.1.1.2'):
    # #await PS4Debug.send_ps4debug(ps4_ip,port=9090)
    # ps4 = PS4Debug(ps4_ip)
    # time.sleep(1)
    
    # async with PatchMemoryPS4900(ps4) as mem:
        # async with MountSave(ps4,mem,0x1eb71bbd,'CUSA11456','infamousssAuto0') as mp:
            # input(mp)


# if __name__ == '__main__':
    # loop = asyncio.new_event_loop()
    # loop.run_until_complete(main())