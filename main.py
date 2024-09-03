import argparse
import asyncio
import logging
import socket
import aiofiles
import gui
from tkinter import TclError, messagebox
from anyio import create_task_group
from listen import listen_forever
from send import InvalidToken, send_forever, get_hash_from_file, pingpong
from common import Queues, TIMEOUT_S, URL

WATCH_DOG_TIMEOUT_S = 5


async def restore_chat(chatlog: str, queues: Queues):
    try:
        async with aiofiles.open(chatlog, "r", encoding="utf-8") as f:
            async for line in f:
                await queues.receive.put(line.strip())
    except Exception:
        pass


class ConnectionError(Exception):
    pass


async def watch_for_connection(queues: Queues):
    while True:
        try:
            await asyncio.wait_for(queues.watchdog.get(), WATCH_DOG_TIMEOUT_S)

        except asyncio.TimeoutError:
            logging.error("connection timed out")
            raise ConnectionError

        await asyncio.sleep(0.1)


async def handle_connection(
        host: str, port: int, send_port: int,
        queues: Queues, hash: str, logfile: str
):
    while True:
        try:
            async with create_task_group() as tg:
                tg.start_soon(send_forever, host, send_port, hash, queues)
                tg.start_soon(listen_forever, host, port, logfile, queues)
                tg.start_soon(watch_for_connection, queues)
                tg.start_soon(pingpong, queues)

        except (ConnectionError, socket.gaierror):
            logging.warning("Restarting connection")
            queues.status.put(gui.SendingConnectionStateChanged.CLOSED)
            queues.status.put(gui.ReadConnectionStateChanged.CLOSED)
            await asyncio.sleep(TIMEOUT_S)

        except asyncio.CancelledError:
            return


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="server address", default=URL)
    parser.add_argument("--port", "-p", help="server port", default=5000)
    parser.add_argument("--sendport", "-sp", help="send port", default=5050)
    parser.add_argument(
        "--logfile", "-l", help="log filepath", default="./chat.log")
    parser.add_argument(
        "--credentials", help="credentials file", default="./credentials.json"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
    )

    queues = Queues(
        asyncio.Queue(), asyncio.Queue(), asyncio.Queue(), asyncio.Queue()
    )
    await restore_chat(args.logfile, queues)
    hash = await get_hash_from_file(args.credentials)

    async with create_task_group() as tg:
        tg.start_soon(gui.draw, queues.receive,
                      queues.send, queues.status)
        tg.start_soon(handle_connection, args.host, args.port,
                      args.sendport, queues, hash, args.logfile)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except InvalidToken:
        SystemExit(1)
    except (KeyboardInterrupt, BaseExceptionGroup):
        logging.debug("Shutting down")
    except TclError:
        logging.debug("gui error")
