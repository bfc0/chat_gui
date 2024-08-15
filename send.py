import asyncio
import json
import logging
import argparse

import aiofiles
from common import send_line, read_line

URL = "minechat.dvmn.org"


async def register(host: str, port: int, name: str):
    r, w = await asyncio.open_connection(host, port)
    await read_line(r)
    await send_line(w, "\n")
    await read_line(r)
    name = name or input()
    await send_line(w, name)
    result = await read_line(r)

    async with aiofiles.open("credentials.json", "w") as f:
        await f.write(result)

    credentials = json.loads(result)
    hash = credentials["account_hash"]
    logging.debug(f"Your hash is {hash}")


async def authorize(
    r: asyncio.StreamReader, w: asyncio.StreamWriter, hash: str
) -> bool:
    _ = await read_line(r)
    await send_line(w, f"{hash}\n")
    data = await read_line(r)
    credentials = json.loads(data)

    return bool(credentials)


async def get_hash_from_file(filename: str) -> str | None:
    try:
        async with aiofiles.open(filename, "r") as f:
            credentials = json.loads(await f.read())
        hash = credentials["account_hash"]
    except Exception:
        logging.debug("Could not get account hash from credentials file")
        return None
    return hash


async def send_message(host: str, port: int, message: str, hash: str) -> bool:
    try:
        r, w = await asyncio.open_connection(host, port)
        result = await authorize(r, w, hash)
        if not result:
            logging.error("Failed to authorize")
            return False
        _ = await read_line(r)
        await send_line(w, message)

        resp = await read_line(r)
        if resp.startswith("Message send"):
            logging.debug("Message sent succefully")
            return True

    except Exception as e:
        logging.exception(f"something went wrong: {e}")
        return False

    logging.error("Message not sent")
    return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="server address", default=URL)
    parser.add_argument("--port", "-p", help="server port", default=5050)
    parser.add_argument("--register", "-r", help="register [name]", action="store_true")
    parser.add_argument("message", help="message", nargs="+", type=str)
    parser.add_argument(
        "--credentials", help="credentials file", default="./credentials.json"
    )
    args = parser.parse_args()
    message = " ".join(args.message)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
    )

    if args.register:
        await register(args.host, args.port, message)
        return

    hash = await get_hash_from_file(args.credentials)
    if not hash:
        await register(args.host, args.port, "")
        hash = await get_hash_from_file(args.credentials)
        if not hash:
            logging.error("failed to register")
            return

    await send_message(args.host, args.port, message, hash)


if __name__ == "__main__":
    asyncio.run(main())
