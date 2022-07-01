# Client commands for the repl

import os
from pathlib import Path
from .client import client
from .constants import SCRIPT_LOAD_REMOVE_KWDS, STDOUT_MARKER_END, STDOUT_MARKER_START
from types import FunctionType

from dataclasses import dataclass

from prompt_toolkit.completion import (Completer, PathCompleter, WordCompleter)
from prompt_toolkit.shortcuts import clear

EMPTY_COMPLETER = WordCompleter([])


def EMPTYFUNC(*args):
    pass


@dataclass
class Command:
    completer: Completer = EMPTY_COMPLETER
    help: str = ""
    do: FunctionType = EMPTYFUNC
    send_to_server: bool = False


# COMMANDS

def _help(*args):
    print("REPL SPECIAL COMMANDS")
    for cmd in COMMANDS:
        print(f"{cmd}: {COMMANDS[cmd].help}")


def loadscript(c: client, args):
    """Reads all contents from each of the args file and sends it to the server."""
    for file in args:
        file = str(Path(file).expanduser())
        if not os.path.isfile(file):
            print("File does not exist")
            return
        with open(file, 'r') as f:
            for line in f.readlines():
                if line.strip() and line.split()[0] in SCRIPT_LOAD_REMOVE_KWDS:
                    continue
                c.send(line)
        c.send("\n")
    print("\n\nSuccessfully loaded script(s)")


def savescript(c: client, args):
    """Saves the contents of the server to the file specified by the args."""
    script_global = c.send("script_global")
    script_local = c.send("script_local")
    # Check if directory exists
    if not os.path.isdir(Path(args[0]).parent):
        print("Directory does not exist")
        return

    with open(args[0], 'w') as f:
        f.write(script_global)
        local_buffer = ""
        for line in script_local.split("\n"):
            # Remove STDOUT print lines
            if line.strip() == "print(\"" + STDOUT_MARKER_START + "\")":
                continue
            if line.strip() == "print(\"" + STDOUT_MARKER_END + "\")":
                continue
            local_buffer += line + "\n"
        f.write(script_local)
    print("\n\nSuccessfully saved script to " + args[0])


COMMANDS = {
    "load": Command(completer=PathCompleter(), help="Load .gd file into this session", do=loadscript),
    "save": Command(completer=PathCompleter(), help="Save this session to .gd file", do=savescript),
    "quit": Command(help="Finishes this repl"),
    "help": Command(help="Displays this message", do=_help),
    "clear": Command(help="Clears the screen", do=lambda _, __: clear()),
}
