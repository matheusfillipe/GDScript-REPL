# Client commands for the repl

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.shortcuts import clear

from .client import client
from .constants import SCRIPT_LOAD_REMOVE_KWDS
from .constants import STDOUT_MARKER_END
from .constants import STDOUT_MARKER_START


EMPTY_COMPLETER = WordCompleter([])


def EMPTYFUNC(*args: Any) -> None:
    pass


@dataclass
class Command:
    completer: Completer = EMPTY_COMPLETER
    help: str = ""
    do: Callable[..., Any] = EMPTYFUNC  # type: ignore[assignment]
    send_to_server: bool = False


# COMMANDS


def _help(*args):
    print("REPL SPECIAL COMMANDS")
    for cmd in COMMANDS:
        print(f"{cmd}: {COMMANDS[cmd].help}")


def _mode(*args):
    mode = "Vi" if get_app().editing_mode == EditingMode.VI else "Emacs"
    print(f"Current editing mode: {mode}")


def _history(*args):
    from .config import ConfigManager

    config_manager = ConfigManager()
    print(f"History file: {config_manager.config.history_file}")
    print(f"Max entries: {config_manager.config.max_history}")
    print(f"Rotation: {'enabled' if config_manager.config.history_rotation else 'disabled'}")


def loadscript(c: client, args):
    """Reads all contents from each of the args file and sends it to the server."""
    for file in args:
        file = str(Path(file).expanduser())
        if not os.path.isfile(file):
            print("File does not exist")
            return
        with open(file) as f:
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

    with open(args[0], "w") as f:
        f.write(script_global)
        local_buffer = ""
        for line in script_local.split("\n"):
            # Remove STDOUT print lines
            if line.strip() == 'print("' + STDOUT_MARKER_START + '")':
                continue
            if line.strip() == 'print("' + STDOUT_MARKER_END + '")':
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
    "mode": Command(help="Show current editing mode", do=_mode),
    "history": Command(help="Show history configuration", do=_history),
}
