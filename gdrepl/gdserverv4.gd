# Simple implementation for a exec/eval function in gdscript
# that can accept functions and classes and will return the output

extends SceneTree

# Simple protocol:
# Send anything else to evaluate as godot code
# Commands:
const commands = {
  "clear": "clears the script buffer for the current session",
  "script_local": "Sends back the generated local",
  "script_global": "Sends back the generated global",
  "script_code": "Sends back the generated full runtime script code",
  "delline_local": "Deletes certain line number from the local script",
  "delline_global": "Deletes certain line number from the global script",
  "quit": "stops this server",
}


# The port we will listen to.
const PORT = 9080
# Our WebSocketServer instance.
var _server = WebSocketServer.new()
var port = PORT

var sessions = {}
var debug = false

var loop = true

# These are scope initializer keywords_global. In gdscript these can't
# go inside another one of themselves
const keywords_global = ["func", "class", "enum", "static", "const", "export"]

# Wont try to return if last line starts with any of those
const keywords_local = ["return", "if", "else", "while", "for", "break", "continue", "var", "const"]

# Function that will be called on eval
# This means that users wont be able to define this name
const mainfunc = "___eval"
const main = "func " + mainfunc + "():\n"

enum Scope {
  Global,
  Yellow,
  Local,
}

class Session:
  var global = ""
  var local = ""
  var scope = Scope.Local

  func is_global() -> bool:
    return scope == Scope.Global

  # Generates script code for the session
  func code() -> String:
    if len(local.strip_edges()) == 0:
      return global

    var _local = main
    var lines = Array(local.strip_edges().split("\n"))
    var last = lines[-1].strip_edges()

    # In the local scope
    for line in lines.slice(0, len(lines)-1):
      # Removes all calls to print except the last one
      if line.strip_edges().begins_with("print(") or line.strip_edges().begins_with("printerr("):
        continue
      _local += "  " + line + "\n"

    # Only put return on local if it is really needed
    if last.split(" ")[0] in keywords_local:
      _local += lines[-1]
    elif "=" in "  " + last and not "==" in last:
      _local += "  " + lines[-1]
    else:
      _local += "  return " + lines[-1]

    return global + "\n" + _local

  func delline(num: int, code: String) -> String:
    var lines = Array(code.split("\n"))
    var new_code = ""
    var i = 1
    for line in lines:
      if i == num:
        continue
      new_code += line + "\n"
      i += 1
    return new_code

  func dellocal(line: int):
    local = delline(line, local)

  func delglobal(line: int):
    global = delline(line, global)

  func copy():
    var s = Session.new()
    s.global = global
    s.local = local
    return s
    


# Useful for debuging
func print_script(script, session):
  if not debug:
    return
  print(">>>> ", session)
  print("-----------------------------------")
  print(script.source_code)
  print("-----------------------------------\n")

func add_code(code: String, session: String = "main"):
  # Switch to global scope on keywords_global
  if code != main and code.strip_edges().split(" ")[0] in keywords_global:
    sessions[session].scope = Scope.Global
    if debug:
      print(">>--------global switch-----------<<")

  elif sessions[session].is_global() and not code.begins_with(" "):
    sessions[session].scope = Scope.Local
    if debug:
      print(">>---------global off-------------<<")

  if sessions[session].is_global() or sessions[session].scope == Scope.Yellow:
    sessions[session].global += code
  else:
    sessions[session].local += code

# Executes the the input code and returns the output
# The code will accumulate on the session
func exec(input: String, session: String = "main") -> String:
  # Initializes a script for that session
  if not session in sessions:
    sessions[session] = Session.new()

  var before = sessions[session].copy()
  var lines = Array(input.split("\n"))

  # Appends each input line correctly idented to the eval funcion of the script
  for line in lines.slice(0, len(lines)):
    if len(line) > 0:
      add_code(line + "\n", session)

  if sessions[session].is_global():
    return ""

  if sessions[session].scope == Scope.Yellow:
    sessions[session].scope = Scope.Local
    return ""

  var script = GDScript.new()
  script.source_code = sessions[session].code()
  print_script(script, session)

  var err = script.reload()
  if err != OK:
    sessions[session] = before
    return "Err: " + str(err)

  var obj = RefCounted.new()
  obj.set_script(script)

  if mainfunc in script.source_code:
    print("----------------STDOUT-----------------------")
    var res = str(obj.call(mainfunc))
    print("----------------STDOUT END-----------------------")
    return res
  return ""

# Clear a session
func clear(session: String = "main"):
  sessions.erase(session)

func _init():
  if OS.has_environment("TEST") and OS.get_environment("TEST").to_lower() in ["true", "1"]:
    test()
    quit()
    return

  if OS.has_environment("DEBUG") and OS.get_environment("DEBUG").to_lower() in ["true", "1"]:
    debug = true

  if OS.has_environment("PORT"):
    port = OS.get_environment("PORT").to_int()


  # We dont need those but good to know
  _server.data_received.connect(_on_data)

  # Start listening on the given port.
  var err = _server.listen(port)
  if err != OK:
    print("Unable to start server")
  print("Gdrepl Listening on ", port)
  while loop:
    OS.delay_msec(50)
    _process(0)

  free()
  quit()


# Tests
#############
const cmd0 = "1+1"
const cmd1 = "Array(\"what is this man\".split(' '))[-1]"
const cmd2 = """
var a = Array(\"hello world man\".split(\" \"))
a.sort()
print(a[0])
a
"""
const cmd21 = "var a = 1"
const cmd22 = "a+3"
const cmd3 = """
func hi():
  print('hi')
  return 24

hi()
"""

const cmd4 = """
func add(a, b):
  return a+b+hi()
1 + add(2, 3)
"""

func test():
  debug = true

  var session = "main"
  if OS.has_environment("SESSION") and session == "main":
    session = OS.get_environment("SESSION")

  print(exec(cmd0, session))
  clear(session)
  print(exec(cmd1, session))
  clear(session)
  print(exec(cmd2, session))
  clear(session)
  print(exec(cmd21, session))
  print(exec(cmd22, session))
  print(exec(cmd3, session))
  print(exec(cmd4, session))
  debug = false


func _on_data(id):
  var pkt = _server.get_peer(id).get_packet()
  var data = pkt.get_string_from_utf8()
  if debug:
    print("Got data from client %d: %s" % [id, data])

  var session = "main"
  if OS.has_environment("SESSION") and session == "main":
    session = OS.get_environment("SESSION")


  # Commands without arguments
  var cmd = data.strip_edges().to_lower()
  var response = ""
  var has_command = true
  match cmd :
    "quit":
      _server.stop()
      loop = false
      quit()
      return
    "help":
      response = "GDREPL Server Help\n"
      for c in commands:
        response += c + ": " + commands[c] + "\n"
      response += "\n"

    "clear":
      clear(session)
      response = "Cleared"

    "script_local":
      if session in sessions:
        response = sessions[session].local

    "script_global":
      if session in sessions:
        response = sessions[session].global

    "script_code":
      if session in sessions:
        response = sessions[session].code()

    _: 
      has_command = false

  if has_command:
    if len(response) == 0:
      response = "-"
    send(id, response)
    return

  # Commands with arguments
  cmd = data.strip_edges().split(" ")[0].to_lower()
  match cmd:
    "delline_local":
      sessions[session].dellocal((data.split(" ")[1]).to_int())
      response = "Deleted line"

    "delline_global":
      sessions[session].delglobal((data.split(" ")[1]).to_int())
      response = "Deleted line"

    _:
      response = exec(data, session)
      send(id, ">> " + response)
      return

  send(id, response)


func send(id, data):
  _server.get_peer(id).put_packet(data.to_utf8_buffer())


func _process(_delta):
  _server.poll()

func free():
  _server.stop()
  # super().free()