# Simple implementation for a exec/eval function in gdscript
# that can accept functions and classes and will return the output

extends SceneTree

const WebSocketServer = preload("websocketserver.gd")

# Simple protocol:
# Send anything else to evaluate as godot code
# Commands:
const commands = {
  "reset": "clears the script buffer for the current session",
  "script_local": "Sends back the generated local",
  "script_global": "Sends back the generated global",
  "script_code": "Sends back the generated full runtime script code",
  "dellast_local": "Deletes last local scope or code block",
  "delline_local": "Deletes certain line number from the local script",
  "delline_global": "Deletes certain line number from the global script",
  "delglobal": "Deletes the entire global scope",
  "dellocal": "Deletes the entire local scope",
  "quit": "stops this server",
}

const STDOUT_MARKER_START = "----------------STDOUT-----------------------"
const STDOUT_MARKER_END = "----------------STDOUT END-----------------------"

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
const keywords_local = ["if", "else", "while", "for", "break", "continue", "var", "const"]

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
  var last_scope_begin_index

  # Another reason not to add return is if in a local scope like if, elif, for...
  var local_scope_lock = false

  func is_global() -> bool:
    return scope == Scope.Global

  func dellast_local():
    var i = 0
    var new_local = ""
    for line in local.strip_edges().split("\n"):
      if i >= last_scope_begin_index:
        break
      new_local += line + "\n"
      i += 1
    local = new_local

  func check_scope(line: String, index: int):
    var has_keyword = line.split(" ")[0] in keywords_local
    var is_continuation = line.split(" ")[0].rstrip(":") in ["else", "elif"]

    if not local_scope_lock:
      last_scope_begin_index = index
    if has_keyword and not is_continuation:
      local_scope_lock = true
    elif not is_continuation and local_scope_lock and not line.begins_with(" "):
      local_scope_lock = false
      last_scope_begin_index = index
    return has_keyword

  func get_last_scope_index():
    var i = 0
    for line in local.strip_edges().split("\n"):
      check_scope(line, i)
      i += 1
    return last_scope_begin_index


  # Generates script code for the session
  func code(with_return: bool = true) -> String:
    if len(local.strip_edges()) == 0:
      return global

    var _local = main
    var lines = Array(local.strip_edges().split("\n"))
    var last_stripped = lines[-1].strip_edges()

    # In the local scope
    var last_index = get_last_scope_index()
    var i = 0
    if len(lines) > 1:
      local_scope_lock = false
      for line in lines.slice(0, len(lines)-1):
        var has_keyword = check_scope(line, i)

        # Removes all calls to print except the last one or keyword one
        if i == last_index:
          var identation = " ".repeat(len(line.rstrip(" ")) - len(line.rstrip(" ").lstrip(" ")))
          _local += "  " + identation + "print(\"" + STDOUT_MARKER_START + "\")" + "\n"
        _local += "  " + line + "\n"

        i += 1

    # Removes all calls to print except the last one or keyword one
    if i == last_index:
      _local += "  " + "print(\"" + STDOUT_MARKER_START + "\")" + "\n"

    var has_keyword = check_scope(lines[-1], len(lines) - 1)

    # Only put return on local if it is really needed
    var is_assignment = "=" in last_stripped and not "==" in last_stripped
    var should_skip_return = has_keyword or is_assignment or local_scope_lock or lines[-1].begins_with(" ")
    if should_skip_return or not with_return:
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
  script.source_code = sessions[session].code(true)
  print_script(script, session)

  var err = script.reload()
  if err != OK:
    # Retry without return (handles void-returning functions like print())
    script.source_code = sessions[session].code(false)
    print_script(script, session)
    err = script.reload()
    if err != OK:
      sessions[session].dellast_local()
      return "Err: " + str(err)

  var obj = RefCounted.new()
  obj.set_script(script)

  if mainfunc in script.source_code:
    print(STDOUT_MARKER_START)
    var res = str(obj.call(mainfunc))
    print(STDOUT_MARKER_END)
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


  _server.message_received.connect(_on_message)

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

const cmd5 = "print(\"hello from void function\")"

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
  clear(session)
  print(exec(cmd5, session))
  debug = false


func _on_message(id, message):
  if debug:
    print("Got message from client %d: %s" % [id, message])

  var session = "main"
  if OS.has_environment("SESSION") and session == "main":
    session = OS.get_environment("SESSION")


  # Commands without arguments
  var cmd = message.strip_edges().to_lower()
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

    "reset":
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

    "dellast_local":
      sessions[session].dellast_local()

    "delglobal":
      sessions[session].global = ""

    "dellocal": 
      sessions[session].local = ""

    _: 
      has_command = false

  if has_command:
    if len(response) == 0:
      response = "-"
    send(id, response)
    return

  # Commands with arguments
  cmd = message.strip_edges().split(" ")[0].to_lower()
  match cmd:
    "delline_local":
      sessions[session].dellocal((message.split(" ")[1]).to_int())
      response = "Deleted line"

    "delline_global":
      sessions[session].delglobal((message.split(" ")[1]).to_int())
      response = "Deleted line"

    _:
      response = exec(message, session)
      send(id, ">> " + response)
      return

  send(id, response)


func send(id, data):
  _server.peers.get(id).put_packet(data.to_utf8_buffer())

func _process(_delta):
  _server.poll()

func free():
  _server.stop()
  # super().free()
