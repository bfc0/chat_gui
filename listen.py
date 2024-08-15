import asyncio
import argparse
import logging
import aiofiles
from common import unserialize, logify

TIMEOUT_S = 1
URL = "minechat.dvmn.org"


async def listen_forever(host: str, port: int, logfile: str):

    async with aiofiles.open(logfile, "a") as file:
        while True:
            try:
                r, _ = await asyncio.open_connection(host, port)
                line = unserialize(await r.readline())
                await file.write(logify(line))
                logging.debug(line)

            except Exception as e:
                logging.exception(f"Something went wrong: {e}")
                await asyncio.sleep(TIMEOUT_S)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="server address", default=URL)
    parser.add_argument("--port", "-p", help="server port", default=5000)
    parser.add_argument("--logfile", "-l", help="log filepath", default="./chat.log")
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
