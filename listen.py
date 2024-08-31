import asyncio
import argparse
import logging
import aiofiles
from common import unserialize, logify

TIMEOUT_S = 1
URL = "minechat.dvmn.org"


async def listen_forever(host: str, port: int, logfile: str, messages: asyncio.Queue):

    async with aiofiles.open(logfile, "a", encoding="utf-8") as file:
        while True:
            writer = None
            try:
                reader, writer = await asyncio.open_connection(host, port)
                line = unserialize(await reader.readline())
                await messages.put(line)
                await file.write(line+"\n")
                await file.flush()
                logging.debug(line)

            except asyncio.CancelledError:
                return

            except Exception as e:
                logging.exception(f"Something went wrong: {e}")
                await asyncio.sleep(TIMEOUT_S)

            finally:
                if writer:
                    writer.close()
                    await writer.wait_closed()


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
