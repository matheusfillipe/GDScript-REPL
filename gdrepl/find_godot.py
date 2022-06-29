import os
from pathlib import Path
import subprocess
from shutil import which

POSSIBLE_COMMANDS = [
    "godot3-server",
    "godot --no-window",
    "godot-editor --no-window",
    "/Applications/Godot.app/Contents/MacOS/Godot --no-window",
    "godot4 --headless",
]


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
    if output.startswith("3"):
        godot.replace("--headless", "--no-window")
        godot += " --no-window"

    if output.startswith("4"):
        godot.replace("--no-window", "--headless")
        godot += " --headless"
        script = script_file_v4()

    return f"{godot} --script {script}"
