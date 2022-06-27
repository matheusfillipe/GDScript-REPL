from shutil import which

POSSIBLE_COMMANDS = [
    "godot3-server",
    "godot --no-window",
    "godot-editor --no-window",
]

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is not None

def find_godot():
    """Finds the godot executable."""
    for cmd in POSSIBLE_COMMANDS:
        if is_tool(cmd.split()[0]):
            return cmd
    print("Cannot find godot executable. You may use --godot")
    return ""
