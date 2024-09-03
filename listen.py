import asyncio
import logging
import aiofiles
import gui
from common import Queues, unserialize, logify, TIMEOUT_S, URL


async def connect(
        host: str, port: int, queues: Queues
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    queues.status.put_nowait(
        gui.ReadConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(host, port)
    queues.status.put_nowait(
        gui.ReadConnectionStateChanged.ESTABLISHED)

    return reader, writer


async def listen_forever(host: str, port: int, logfile: str, queues: Queues):

    reader = writer = None
    async with aiofiles.open(logfile, "a", encoding="utf-8") as file:
        while True:
            try:
                if not writer:
                    reader, writer = await connect(host, port, queues)

                line = unserialize(await reader.readline())
                await queues.receive.put(line)
                queues.watchdog.put_nowait(line)
                await file.write(line+"\n")
                await file.flush()
                logging.debug(line)

            except asyncio.CancelledError:
                if writer:
                    writer.close()
                    await writer.wait_closed()
                return

            except Exception as e:
                logging.exception(f"Something went wrong: {e}")
                await asyncio.sleep(TIMEOUT_S)
