import os
import re
import subprocess as sb
from pathlib import Path

import click
import pexpect
from dataclasses import dataclass
from click_default_group import DefaultGroup
from prompt_toolkit.completion import (Completer, Completion, NestedCompleter,
                                       PathCompleter, WordCompleter,
                                       merge_completers)
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import prompt
from pygments.lexers.gdscript import GDScriptLexer

from .client import client as wsclient
from .constants import GODOT, KEYWORDS, PORT, VI

STDOUT_MARKER_START = "----------------STDOUT-----------------------"
STDOUT_MARKER_END = "----------------STDOUT END-----------------------"
TIMEOUT = 0.2


def script_dir():
    return str(Path(__file__).parent.resolve() / Path("gdserver.gd"))


repl_script_path = script_dir()

history = InMemoryHistory()


@dataclass
class Command:
    completer: Completer = None
    help: str = ""


@dataclass
class PromptOptions:
    vi: bool = False
    timeout: int = TIMEOUT


class CustomCompleter(Completer):
    commands = {
        "load": Command(completer=PathCompleter(), help="Load .gd file into this session"),
    }

    def __init__(self):
        self.word_completer = WordCompleter(KEYWORDS, WORD=True)
        self.document = None
        self.iterator = None

    def _create_iterator(self, completer, document, complete_event):
        self.iterator = completer.get_completions(document, complete_event)

    def get_completions(self, document, complete_event):
        # Only complete after 1st character of last word
        if len(document.text_before_cursor.split(" ")[-1]) < 1:
            return

        if document != self.document:
            self.document = document
            if document.text.strip() in CustomCompleter.commands:
                self._create_iterator(CustomCompleter.commands[document.text.strip()].completer,
                                      document, complete_event)
            else:
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
