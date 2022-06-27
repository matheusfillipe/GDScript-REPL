import os
from shutil import which

POSSIBLE_COMMANDS = [
    "godot3-server",
    "godot --no-window",
    "godot-editor --no-window",
    "/Applications/Godot.app/Contents/MacOS/Godot --no-window",
]

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    # Check if name is a path that exists as executable or is a command
    return (which(name) is not None) or (os.path.exists(name) and os.access(name, os.X_OK))

def find_godot():
    """Finds the godot executable."""
    for cmd in POSSIBLE_COMMANDS:
        if is_tool(cmd.split()[0]):
            return cmd
    print("Cannot find godot executable. You may use --godot")
    return ""
