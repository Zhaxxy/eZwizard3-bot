import argparse
import asyncio

from ps4debug import PS4Debug

from string_helpers import load_config

try:
    from ._raw_save_mount_functions import PS4MemoryNotPatched, restore_memory_patches_from_state
    from .save_functions import send_ps4debug
except ImportError:
    from _raw_save_mount_functions import PS4MemoryNotPatched, restore_memory_patches_from_state
    from save_functions import send_ps4debug


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Restore PS4 save-mount memory patches recorded by this bot."
    )
    parser.add_argument("--ip", help="PS4 IP address. Defaults to config.yaml ps4_ip.")
    parser.add_argument("--port", type=int, default=9090, help="Bin loader port.")
    parser.add_argument(
        "--no-inject",
        action="store_true",
        help="Do not send the bundled ps4debug payload before restoring patches.",
    )
    args = parser.parse_args(argv)

    ps4_ip = args.ip
    if not ps4_ip:
        ps4_ip = load_config()["ps4_ip"]

    if not args.no_inject:
        print("attempting to inject ps4debug payload")
        await send_ps4debug(ps4_ip, port=args.port)
        print("ps4debug payload ready")

    ps4 = PS4Debug(ps4_ip)
    try:
        result = await restore_memory_patches_from_state(ps4)
    except PS4MemoryNotPatched:
        print("PS4 memory already clean; no saved patch state file was found.")
        return 0

    print(
        "PS4 memory restore done: "
        f"{result['restored_patches']} restored, "
        f"{result['already_restored_patches']} already clean, "
        f"{result['freed_allocations']} allocation(s) freed, "
        f"{result['skipped_allocations']} allocation(s) skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
