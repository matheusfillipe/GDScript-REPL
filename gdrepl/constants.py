# Godot executable
GODOT = "godot"

# Websocket server
PORT = 1580
HOST = "127.0.0.1"

# When trying to find a port the godot server can bind on
# This also means that this is the maximum simultaneous repls that can run
MAX_PORT_BIND_ATTEMPTS = 100


# Possible commands to launch godot
POSSIBLE_COMMANDS = [
    "godot3-server",
    "godot --no-window",
    "godot-editor --no-window",
    "/Applications/Godot.app/Contents/MacOS/Godot --no-window",
    "godot4 --headless",
]


# CLI prompt options
# If set to false the prompt will have emacs bindings
VI = False

# GDScript keywords (Godot 4.x)
# Reference: https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html
KEYWORDS = [
    # Control flow
    "if",
    "elif",
    "else",
    "for",
    "while",
    "match",
    "when",
    "break",
    "continue",
    "pass",
    "return",
    # Class definition
    "class",
    "class_name",
    "extends",
    # Type operations
    "is",
    "in",
    "as",
    # Self reference
    "self",
    "super",
    # Declarations
    "signal",
    "func",
    "static",
    "const",
    "enum",
    "var",
    # Special keywords
    "breakpoint",
    "preload",
    "await",
    "yield",
    "assert",
    "void",
    # Constants
    "PI",
    "TAU",
    "INF",
    "NAN",
    # Built-in functions (commonly used)
    "print",
    "printerr",
]

SCRIPT_LOAD_REMOVE_KWDS = ["tool", "extends", "onready", "@onready"]


STDOUT_MARKER_START = "----------------STDOUT-----------------------"
STDOUT_MARKER_END = "----------------STDOUT END-----------------------"
