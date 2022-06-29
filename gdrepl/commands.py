# Client commands for the repl

import os
from pathlib import Path
from .client import client


def loadscript(c: client, args):
    """Reads all contents from each of the args file and sends it to the server."""
    for file in args:
        with open(file, 'r') as f:
            c.send(f.read(), False)
        c.send("\n")
    print("\n\nSuccessfully loaded script(s)")


def savescript(c: client, args):
    """Saves the contents of the server to the file specified by the args."""
    code = c.send("script_code")
    # Check if directory exists
    if not os.path.isdir(Path(args[0]).parent):
        print("Directory does not exist")
        return

    with open(args[0], 'w') as f:
        f.write(code)
    print("\n\nSuccessfully saved script to " + args[0])
