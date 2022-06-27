import time

import click
import pexpect
import os
import subprocess as sb
from click_default_group import DefaultGroup
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

from .client import client as wsclient
from .config import GODOT, VI, PORT

STDOUT_MARKER_START = "----------------STDOUT-----------------------"
STDOUT_MARKER_END = "----------------STDOUT END-----------------------"


print("Welcome to GDScript REPL. Hit Ctrl+C to exit. If you start having errors type 'clear'")

repl_script_path = str(Path(__file__).parent.resolve() / Path("gdserver.gd"))


@click.group(cls=DefaultGroup, default='repl', default_if_no_args=True)
def cli():
    pass

@cli.command(help="Launch the godot server and start teh repl")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--godot", default=GODOT, help="Path to godot executable")
def repl(vi, godot):
    if not godot:
        return
    server = pexpect.spawn(f"{godot} --script {repl_script_path}")
    server.expect("Godot Engine v.*")
    time.sleep(1)
    client = wsclient()

    history = InMemoryHistory()
    while True:
        try:
            cmd = prompt(">>> ", vi_mode=vi, history=history)
        except (EOFError, KeyboardInterrupt):
            client.close()
            break

        if len(cmd.strip()) == 0:
            continue

        resp = client.send(cmd)
        if resp:
            print(resp)
        history.append_string(cmd)

        try:
            server.expect(STDOUT_MARKER_START, 0.2)
            time.sleep(0.1)
            server.expect(STDOUT_MARKER_END, 0.1)
            output = server.before.decode()
            if output.strip():
                print(output.strip())
        except pexpect.exceptions.TIMEOUT:
            pass
        try:
            server.expect("SCRIPT ERROR: (.+)", 0.2)
            print(server.match.group(1).decode())
        except pexpect.exceptions.TIMEOUT:
            pass

@cli.command(help="Connects to a running godot repl server")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--port", default=PORT, help="Port to listen on")
def client(vi, port):
    print("Not launching server..")
    client = wsclient(port=port)
    history = InMemoryHistory()
    while True:
        try:
            cmd = prompt(">>> ", vi_mode=VI, history=history)
        except (EOFError, KeyboardInterrupt):
            client.close()
            break

        if len(cmd.strip()) == 0:
            continue

        resp = client.send(cmd)
        if resp:
            print(resp)
        history.append_string(cmd)

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
