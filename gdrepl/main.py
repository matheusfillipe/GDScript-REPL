import os
import re
import subprocess as sb
from pathlib import Path

import click
import pexpect
from types import FunctionType
from dataclasses import dataclass
from click_default_group import DefaultGroup
from prompt_toolkit.completion import (Completer, PathCompleter, WordCompleter)
from prompt_toolkit.document import Document
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import prompt
from pygments.lexers.gdscript import GDScriptLexer

from .client import client as wsclient
from .constants import GODOT, KEYWORDS, PORT, VI
from .commands import loadscript, savescript

STDOUT_MARKER_START = "----------------STDOUT-----------------------"
STDOUT_MARKER_END = "----------------STDOUT END-----------------------"
TIMEOUT = 0.2
EMPTY_COMPLETER = WordCompleter([])


def script_dir():
    return str(Path(__file__).parent.resolve() / Path("gdserver.gd"))


repl_script_path = script_dir()

history = InMemoryHistory()

def EMPTYFUNC(*args):
    pass

@dataclass
class Command:
    completer: Completer = EMPTY_COMPLETER
    help: str = ""
    do: FunctionType = EMPTYFUNC


@dataclass
class PromptOptions:
    vi: bool = False
    timeout: int = TIMEOUT


class CustomCompleter(Completer):
    """Auto completion and commands"""

    commands = {
        "load": Command(completer=PathCompleter(), help="Load .gd file into this session", do=loadscript),
        "save": Command(completer=PathCompleter(), help="Save this session to .gd file", do=savescript),
        "quit": Command(help="Finishes this repl"),
        "help": Command(help="Displays this message"),
    }

    def __init__(self):
        self.word_completer = WordCompleter(
            KEYWORDS + list(CustomCompleter.commands.keys()), WORD=True)
        self.document = None
        self.iterator = None

    def _create_iterator(self, completer, document, complete_event):
        self.iterator = completer.get_completions(document, complete_event)

    def get_completions(self, document, complete_event):
        # Only complete after 1st character of last word
        if len(document.text_before_cursor.split(" ")[-1]) < 1:
            return

        cmd = document.text.split()[0]
        if cmd in CustomCompleter.commands and len(document.text_before_cursor.strip()) > len(cmd):
            sub_doc = Document(document.text[len(cmd) + 1:])
            self._create_iterator(CustomCompleter.commands[cmd].completer,
                                  sub_doc, complete_event)

        elif document != self.document:
            self.document = document
            self._create_iterator(self.word_completer,
                                  document, complete_event)
        for w in self.iterator:
            yield w


completer = CustomCompleter()


def _prompt(vi):
    return prompt(
        ">>> ",
        vi_mode=vi,
        history=history,
        lexer=PygmentsLexer(GDScriptLexer),
        completer=completer,
    )


def wait_and_print_server(server, timeout):
    try:
        server.expect(STDOUT_MARKER_START, timeout=timeout)
        server.expect(STDOUT_MARKER_END, timeout=timeout)
        output = server.before.decode()
        if output.strip():
            print(output.strip())
    except pexpect.exceptions.TIMEOUT:
        pass
    try:
        server.expect(r"SCRIPT ERROR:(.+)", timeout=timeout)
        error = server.match.group(1).decode().strip()
        error = re.sub(
            "\r\n" + r".*ERROR:.* Method failed\..*" + "\r\n.*", "", error
        )
        print(error)
    except pexpect.exceptions.TIMEOUT:
        pass


def repl_loop(client, options: PromptOptions, server=None):
    while True:
        try:
            cmd = _prompt(options.vi)
        except (EOFError, KeyboardInterrupt):
            client.close()
            break

        if len(cmd.strip()) == 0:
            continue

        if cmd.strip() == "quit":
            client.send(cmd, False)
            client.close()
            break

        if cmd.split()[0] != "help" and cmd.split()[0] in CustomCompleter.commands:
            command = CustomCompleter.commands[cmd.split()[0]]
            command.do(client, cmd.split()[1:])
            continue

        history._loaded_strings = list(dict.fromkeys(history._loaded_strings))
        resp = client.send(cmd)
        if resp:
            print(resp)

        if server is not None:
            wait_and_print_server(server, options.timeout)

        if cmd.strip() == "help":
            print("CLIENT COMMANDS")
            for cmd in CustomCompleter.commands:
                print(f"{cmd}: {CustomCompleter.commands[cmd].help}")


@click.group(cls=DefaultGroup, default="run", default_if_no_args=True)
def cli():
    pass


@cli.command(help="Launch the godot server and starts the repl")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--godot", default=GODOT, help="Path to godot executable")
@click.option(
    "--command", default="", help="Custom command to run the server script with"
)
@click.option("--timeout", default=TIMEOUT, help="Time to wait for godot output")
def run(vi, godot, command, timeout):
    print(
        "Welcome to GDScript REPL. Hit Ctrl+C to exit. If you start having errors type 'clear'"
    )
    if not godot:
        return
    server = None
    if command:
        server = pexpect.spawn(command)
    else:
        server = pexpect.spawn(f"{godot} --script {repl_script_path}")
    server.expect("Gdrepl Listening on .*")
    client = wsclient()

    repl_loop(client, PromptOptions(vi=vi, timeout=timeout), server)


@cli.command(help="Connects to a running godot repl server")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--port", default=PORT, help="Port to listen on")
def client(vi, port):
    print(
        "Welcome to GDScript REPL. Hit Ctrl+C to exit. If you start having errors type 'clear'"
    )
    print("Not launching server..")

    client = wsclient(port=port)

    repl_loop(client, PromptOptions(vi=vi))


@cli.command(help="Starts the gdscript repl websocket server")
@click.option("--godot", default=GODOT, help="Path to godot executable")
@click.option("--port", default=PORT, help="Port to listen on")
@click.option("--verbose", is_flag=True, default=False, help="Enable debug output")
def server(port, godot, verbose):
    if not godot:
        return
    env = os.environ.copy()
    if port:
        env["PORT"] = str(port)
    if verbose:
        env["DEBUG"] = "1"
    sb.run(f"{godot} --script {repl_script_path}", shell=True, env=env)
