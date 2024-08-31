import argparse
import asyncio
import logging
import aiofiles
import gui
from listen import listen_forever
from send import

TIMEOUT_S = 1
URL = "minechat.dvmn.org"


async def restore_chat(chatlog: str, messages: asyncio.Queue):
    try:
        async with aiofiles.open(chatlog, "r", encoding="utf-8") as f:
            async for line in f:
                await messages.put(line.strip())
    except Exception:
        pass


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
    loop = asyncio.get_event_loop()

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    await restore_chat(args.logfile, messages_queue)

    listen = loop.create_task(listen_forever(
        args.host, args.port, args.logfile, messages_queue))
    draw = loop.create_task(
        gui.draw(messages_queue, sending_queue, status_updates_queue))
    await draw
    return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.debug("Shutting down")
