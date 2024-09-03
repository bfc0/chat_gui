import asyncio
from dataclasses import dataclass
from datetime import datetime


TIMEOUT_S = 1
READ_TIMEOUT = 2
URL = "minechat.dvmn.org"
PORT = 5050
HASH_FNAME = "credentials.json"


async def send_line(writer: asyncio.StreamWriter, message: bytes | str):
    if isinstance(message, str):
        message = serialize(message)

    writer.write(message)
    try:
        await asyncio.wait_for(writer.drain(), READ_TIMEOUT)

    except asyncio.TimeoutError:
        return


async def read_line(reader: asyncio.StreamReader) -> str:
    try:
        line = await asyncio.wait_for(reader.readline(), READ_TIMEOUT)

    except asyncio.TimeoutError:
        return

    return line.decode("utf-8").rstrip()


def sanitize(msg: str) -> str:
    return msg.replace("\n", "")


def serialize(msg: str) -> bytes:
    return f"{sanitize(msg)}\n\n".encode()


def unserialize(msg: bytes) -> str:
    return msg.decode("utf-8").rstrip()


def logify(msg: str) -> str:
    now = f"[{datetime.strftime(datetime.now(), '%d.%m.%Y %H:%M')}]"
    if not msg.endswith("\n"):
        return f"{now} {msg}\n"
    return f"{now} {msg}"


@ dataclass
class Queues:
    receive: asyncio.Queue
    send: asyncio.Queue
    status: asyncio.Queue
    watchdog: asyncio.Queue
