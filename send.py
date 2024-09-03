import asyncio
import json
import logging
import argparse
import aiofiles
from tkinter import messagebox
from common import Queues, send_line, read_line, TIMEOUT_S, URL, PORT
import gui


class InvalidToken(Exception):
    pass


async def register(host: str = URL, port: int = PORT, name: str = "") -> bool:
    reader = writer = None
    try:

        reader, writer = await asyncio.open_connection(host, port)
        await read_line(reader)
        await send_line(writer, "\n".encode("utf-8"))
        line = await read_line(reader)
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


async def pingpong(queues: Queues):
    while True:
        queues.send.put_nowait("")
        await asyncio.sleep(TIMEOUT_S)


async def authorize(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, hash: str, queues: Queues
) -> bool:
    _ = await read_line(reader)
    await send_line(writer, f"{hash}\n")
    data = await read_line(reader)
    credentials = json.loads(data)

    if name := credentials.get("nickname"):
        queues.status.put_nowait(gui.NicknameReceived(name))
        queues.watchdog.put_nowait("Authorized")

    return bool(credentials)


async def get_hash_from_file(filename: str) -> str | None:
    try:
        async with aiofiles.open(filename, "r") as f:
            credentials = json.loads(await f.read())
        hash = credentials["account_hash"]
    except Exception:
        logging.debug("Could not get account hash from credentials file")
        messagebox.showerror(
            "Exception",
            "Необходимо зарегистрироваться."
        )
        raise InvalidToken
    return hash


async def send_forever(host: str, port: int, hash: str, queues: Queues):
    writer = None

    while True:
        try:
            if not writer or writer.is_closing():
                queues.status.put_nowait(
                    gui.SendingConnectionStateChanged.INITIATED)

                reader, writer = await asyncio.open_connection(host, port)
                result = await authorize(reader, writer, hash, queues)

                if not result:
                    logging.error("Failed to authorize")
                    messagebox.showerror(
                        "Exception",
                        "Не удалось авторизоваться. Неверный токен."
                    )
                    raise InvalidToken
                _ = await read_line(reader)
                queues.status.put_nowait(
                    gui.SendingConnectionStateChanged.ESTABLISHED)
                queues.watchdog.put_nowait("connection established")

            message = await queues.send.get()
            _ = await read_line(reader)
            await send_line(writer, message)
            resp = await read_line(reader)

            if not resp.startswith("Message send"):
                logging.debug(f"Unexpected response: {resp}")

        except asyncio.CancelledError:
            if writer:
                writer.close()
                await writer.wait_closed()

        except Exception as e:
            logging.warning(f"An error occured: {e}")
            await asyncio.sleep(TIMEOUT_S)

        await asyncio.sleep(0.1)
