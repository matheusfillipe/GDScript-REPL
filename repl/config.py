from find_godot import find_godot
### GODOT optiosn
# Godot executable
GODOT = find_godot()

# Websocket server port. Has to match the one in gdserever.gd
PORT = 9080
HOST = "127.0.0.1"

### CLI prompt options
# If set to false the prompt will have emacs bindings
VI = False