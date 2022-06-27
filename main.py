#!/usr/bin/env python3

import time

import pexpect
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

from sys import argv

from client import client as wsclient
from config import GODOT, VI

STDOUT_MARKER_START = "----------------STDOUT-----------------------"
STDOUT_MARKER_END = "----------------STDOUT END-----------------------"

def main():
    server = pexpect.spawn(f"{GODOT} --script gdserver.gd")
    server.expect("Godot Engine v.*")
    time.sleep(1)
    client = wsclient()

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

def simple_repl():
    print("Not launching server..")
    client = wsclient()
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

if __name__ == '__main__':
    print("Welcome to GDScript REPL. Hit Ctrl+C to exit. If you start having errors type 'clear'")
    if len(argv) > 1:
        simple_repl()
    else:
        main()
