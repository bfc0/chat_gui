import asyncio
import json
import logging
import argparse

import aiofiles
from common import send_line, read_line

URL = "minechat.dvmn.org"


async def register(host: str, port: int, name: str):
    reader = writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        await read_line(reader)
        await send_line(writer, "\n")
        await read_line(reader)
        await send_line(writer, name)
        result = await read_line(reader)

        async with aiofiles.open("credentials.json", "w") as f:
            await f.write(result)

        credentials = json.loads(result)
        hash = credentials["account_hash"]
        logging.debug(f"Your hash is {hash}")

    finally:
        if writer:
            writer.close()
            await writer.wait_closed()


async def authorize(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, hash: str
) -> bool:
    _ = await read_line(reader)
    await send_line(writer, f"{hash}\n")
    data = await read_line(reader)
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
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        result = await authorize(reader, writer, hash)
        if not result:
            logging.error("Failed to authorize")
            return False
        _ = await read_line(reader)
        await send_line(writer, message)

        resp = await read_line(reader)
        if resp.startswith("Message send"):
            logging.debug("Message sent succefully")
            return True

    except Exception as e:
        logging.exception(f"something went wrong: {e}")
        return False

    finally:
        if writer:
            writer.close()
            await writer.wait_closed()

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
