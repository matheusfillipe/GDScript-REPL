################################################################################
#      ____  ___    ____  ________     ____  ____  ______
#     / __ \/   |  / __ \/  _/ __ \   / __ )/ __ \/_  __/
#    / /_/ / /| | / / / // // / / /  / __  / / / / / /
#   / _, _/ ___ |/ /_/ // // /_/ /  / /_/ / /_/ / / /
#  /_/ |_/_/  |_/_____/___/\____/  /_____/\____/ /_/
#
#
# Matheus Fillipe 18/05/2022
# MIT License
################################################################################


import asyncio
import atexit
import os
import stat
from typing import Callable

import trio


loop = True
FIFO = "/tmp/gdrepl-bot.fifo"


def stop_loop():
    global loop, FIFO
    loop = False
    with open(FIFO, "w") as f:
        f.write(".")
    os.remove(FIFO)


atexit.register(stop_loop)


async def listen_loop(fifo_path: str, handler: Callable):
    global loop, FIFO
    if os.path.exists(fifo_path):
        os.remove(fifo_path)

    os.mkfifo(fifo_path)
    os.chmod(fifo_path, stat.S_IRWXO | stat.S_IRWXU | stat.S_IRWXG)
    FIFO = fifo_path
    print("Message Relay listening at fifo: " + fifo_path)
    while loop:
        async with await trio.open_file(fifo_path) as fifo:
            async for line in fifo:
                line = line.strip()
                if asyncio.iscoroutinefunction(handler):
                    await handler(line)
                else:
                    handler(line)
