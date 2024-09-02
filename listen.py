import asyncio
import argparse
import logging
import aiofiles
import gui
from common import Queues, unserialize, logify

TIMEOUT_S = 1
URL = "minechat.dvmn.org"


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


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="server address", default=URL)
    parser.add_argument("--port", "-p", help="server port", default=5000)
    parser.add_argument("--logfile", "-l",
                        help="log filepath", default="./chat.log")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
    )

    await listen_forever(args.host, args.port, args.logfile)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.debug("Shutting down")
