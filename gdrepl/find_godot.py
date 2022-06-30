import os
import socket
from pathlib import Path
import subprocess
from shutil import which

from .constants import MAX_PORT_BIND_ATTEMPTS, POSSIBLE_COMMANDS

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    # Check if name is a path that exists as executable or is a command
    return (which(name) is not None) or (os.path.exists(name) and os.access(name, os.X_OK))


def script_file():
    return str(Path(__file__).parent.resolve() / Path("gdserver.gd"))


def script_file_v4():
    return str(Path(__file__).parent.resolve() / Path("gdserverv4.gd"))


def find_godot():
    """Finds the godot executable."""
    for cmd in POSSIBLE_COMMANDS:
        if is_tool(cmd.split()[0]):
            return cmd
    print("Cannot find godot executable. You may use --godot")
    return ""


def godot_command(godot: str) -> str:
    """Fixes the arguments for godot based on the version"""
    output = None
    try:
        output = subprocess.run(f"{godot} --version", stdout=subprocess.PIPE, timeout=None,
                                check=False, shell=True, stderr=subprocess.STDOUT).stdout.decode().strip()
    except subprocess.CalledProcessError:
        if not output:
            print("Failed to check godot version!")
            return godot

    script = script_file()

    # Godot doesn't care about repeated flags so just to make sure
    if output.startswith("3"):
        godot.replace("--headless", "--no-window")
        godot += " --no-window"

    if output.startswith("4"):
        godot.replace("--no-window", "--headless")
        godot += " --headless"
        script = script_file_v4()

    return f"{godot} --script {script}"


def find_available_port(start_port: int) -> int:
    """Starts checking if start_port is available to bind and increments 1 until it finds an available port."""
    port = start_port
    while True:
        if port - start_port > MAX_PORT_BIND_ATTEMPTS:
            print("Failed to find free port. Maybe I can't bind on localhost?")
            import sys
            sys.exit(1)
            return -1

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("localhost", port))
            sock.close()
            return port

        except OSError:
            # print(port, "is busy, trying next port")
            port += 1
