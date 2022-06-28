import os
import re
import subprocess as sb
from pathlib import Path

import click
import pexpect
from click_default_group import DefaultGroup
from prompt_toolkit.completion import WordCompleter
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

    history = InMemoryHistory()
    completer = WordCompleter(KEYWORDS, WORD=True)
    while True:
        try:
            cmd = prompt(
                ">>> ",
                vi_mode=vi,
                history=history,
                lexer=PygmentsLexer(GDScriptLexer),
                completer=completer,
            )
        except (EOFError, KeyboardInterrupt):
            client.close()
            break

        if len(cmd.strip()) == 0:
            continue

        if cmd == "quit":
            client.send(cmd, False)
            client.close()
            break

        history._loaded_strings = list(dict.fromkeys(history._loaded_strings))
        resp = client.send(cmd)
        if resp:
            print(resp)

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
            error = re.sub("\r\n" + r".*ERROR:.* Method failed\..*" + "\r\n.*", "", error)
            print(error)
        except pexpect.exceptions.TIMEOUT:
            pass


@cli.command(help="Connects to a running godot repl server")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--port", default=PORT, help="Port to listen on")
def client(vi, port):
    print(
        "Welcome to GDScript REPL. Hit Ctrl+C to exit. If you start having errors type 'clear'"
    )
    print("Not launching server..")

    # TODO avoid repeating this whole code here again
    client = wsclient(port=port)
    history = InMemoryHistory()
    completer = WordCompleter(KEYWORDS, WORD=True)
    while True:
        try:
            cmd = prompt(
                ">>> ",
                vi_mode=vi,
                history=history,
                lexer=PygmentsLexer(GDScriptLexer),
                completer=completer,
            )
        except (EOFError, KeyboardInterrupt):
            client.close()
            break

        if len(cmd.strip()) == 0:
            continue

        if cmd == "quit":
            client.send(cmd, False)
            client.close()
            break

        resp = client.send(cmd)
        if resp:
            print(resp)

        history._loaded_strings = list(dict.fromkeys(history._loaded_strings))


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
