import asyncio
from dataclasses import dataclass
from datetime import datetime


async def send_line(writer: asyncio.StreamWriter, message: bytes | str):
    if isinstance(message, str):
        message = serialize(message)

    writer.write(message)
    await writer.drain()


async def read_line(reader: asyncio.StreamReader) -> str:
    line = await reader.readline()
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


@dataclass
class Queues:
    receive: asyncio.Queue
    send: asyncio.Queue
    status: asyncio.Queue
