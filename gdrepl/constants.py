from .find_godot import find_godot

### GODOT options ###
# Godot executable
GODOT = find_godot()

# Websocket server port. Has to match the one in gdserever.gd
PORT = 9080
HOST = "127.0.0.1"

# CLI prompt options
# If set to false the prompt will have emacs bindings
VI = False

# Godot keywords
KEYWORDS = ["if", "elif", "else", "for", "while", "match", "break", "continue", "pass", "return", "class",
            "class_name", "extends", "is", "as", "self", "tool", "signal", "func", "static", "const", "enum", "var", "print"]
