import argparse
import logging
import asyncio
import tkinter as tk
from anyio import create_task_group
from gui import TkAppClosed
from common import URL
from send import register


async def process_registration(name, status_text):
    if name:
        print(name)
        status_text.insert(tk.END, f"Регистрируем {name}...\n")
        await register(name=name)
        status_text.insert(tk.END, f"{name} зарегистрировано!\n")
    else:
        status_text.insert(tk.END, "Введите имя.\n")
    status_text.yview_moveto(1.0)


def schedule_registration(input_field, status_label, queue):
    name = input_field.get()
    asyncio.create_task(process_registration(name, status_label))


async def draw(queue):

    root = tk.Tk()
    root.title('Registration')
    root.geometry("500x300")

    root_frame = tk.Frame(root, padx=20, pady=20)
    root_frame.pack(fill="both", expand=True)

    input_frame = tk.Frame(root_frame, pady=30)
    input_frame.pack(side="bottom", fill=tk.X)

    label = tk.Label(input_frame, text="Введите Имя:")
    label.pack(side="left")

    input_field = tk.Entry(input_frame)
    input_field.pack(side="left", fill=tk.X, expand=True)

    status_text = tk.Text(root_frame, wrap="word", height=10)
    status_text.pack(side="top", fill="both", expand=True, padx=10, pady=10)
    status_text.insert(tk.END, "Введите имя:\n")

    register_button = tk.Button(
        input_frame, text="Регистрация", command=lambda: schedule_registration(input_field, status_text, queue))
    register_button.pack(side="left")

    async with create_task_group() as tg:
        tg.start_soon(update_tk, root)


async def update_tk(root):
    while True:
        try:
            root.winfo_exists()  # this throws when the window is closed
            root.update()
        except tk.TclError:
            return
        await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="server address", default=URL)
    parser.add_argument("--port", "-p", help="server port", default=5050)
    parser.add_argument(
        "--credentials", help="credentials file", default="./credentials.json"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
    )

    queue = asyncio.Queue()

    async with create_task_group() as tg:
        tg.start_soon(draw, queue)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except BaseExceptionGroup as e:
        for exc in e.exceptions:
            logging.error(f"Exception: {exc}")

    except (KeyboardInterrupt):
        logging.debug("Shutting down")

    except TkAppClosed:
        logging.debug("gui error")
