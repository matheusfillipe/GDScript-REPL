[![CircleCI Build Status](https://circleci.com/gh/matheusfillipe/GDScript-REPL.svg?style=shield)](https://circleci.com/gh/matheusfillipe/GDScript-REPL)
[![Pypi](https://badge.fury.io/py/gdrepl.svg)](https://pypi.org/project/gdrepl/)
[![Chat with me on irc](https://img.shields.io/badge/-IRC-gray?logo=gitter)](https://mangle.ga/irc)

[![demo](https://user-images.githubusercontent.com/24435787/176273963-dfce8324-665d-4136-a155-66d8db687332.gif)](https://asciinema.org/a/504811)

# GDScript REPL

This repository contains:

- A proof of concept GDScript REPL
- A dockerfile to build godot server for alpine
- A dockerfile to run godot from alpine
- A IRC GDScript REPL bot 

Notice that if all you want is run GDScript files from the command line you don't need this project. Check out: https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html 


## Motivation

GDScript is a python like language but it lacks a REPL. Godot has a built in `godot -s script.gd` to run scripts but it is overkill when you just want to test out the difference between a `PoolStringArray` and a normal `Array` of strings and play around like you can do with so many languages.

That inspired me to try to turn `godot -s` into a REPL, creating a [websocket server](https://docs.godotengine.org/en/stable/classes/class_websocketserver.html) that will take any string from any client in, evaluate it by creating new [GDScript](https://docs.godotengine.org/en/stable/classes/class_script.html), attaching that script to a resource node and then calling a function of that node. That requires a lot of hacky string manipulations to keep stuff working and have a separated local and global scopes allowing you to create functions, enums and classes from the REPL. 

This is this still very work in progress and experimental but serves to prove the point that a REPL for godot would be awesome.

## Installation

Simply:
```bash
pip3 install gdrepl

gdrepl
```

If you want to use the irc bot you will need to clone this repo and follow the instructions bellow.


## Usage

The GDScript server is implemented in a way that it will send the return output to the client but not stdout. So if you type `1+1` you will receive `2` but you can't receive `print(2)` event though that will be still shown on the server's output.

Currently this doesn't perfectly support multiline and you have to manually fix the indentation sometimes. You can also "fake" multiline input in a single line in both the irc bot and REPL by using a `;`. Those will be replaced to `\n` at runtime, for example:

```GDScript
func inc(value):; var new = value + 1; return value
```

It supports godot 3 and 4. If you don't have godot on your path use the `--godot` parameter to pass it or `--command` to completely change the godot command, like if you don't want it headless, and in that case you have to manually specify `-s path/sto/gdserver.gd`. Example:

```bash
gdrepl --godot /home/user/programs/godot/godot
```

If you are having problems try running the server and client separately. In one terminal run:

```bash
gdrepl server --verbose # You can also pass --godot or --command
```

In another one:

```bash
gdrepl client  # maybe --port N
```

Notice that multiple clients can be connected to the same server.

For more information check `gdrepl --help`, `gdrepl server --help` etc.


## Development

### CLI

Requires python3

1. Install godot headless. Ubuntu has `sudo apt install godot3-server` which is very suitable for this. In another distros without that the script will fallback to `godot --no-window` to run it headlessly.
3. You can create a virtual environment or not: `pip3 install requirements.py`  
4. Run `python -m gdrepl`

With this you will see both stdout and return output in the same window.

### Server

Start the server with:

```bash
gdrepl server
```

```bash
$ python -m gdrepl --help
Welcome to GDScript REPL. Hit Ctrl+C to exit. If you start having errors type 'clear'
Usage: python -m gdrepl [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  REPL*   Launch the godot server and start the REPL
  client  Connects to a running godot REPL server
  server  Starts the GDScript REPL websocket server

```


Alternatively you can directly run the godot script:
```bash
godot3-server --script gdserver.gd
# or
godot --no-window --script gdserver.gd
```

You can connect to this server using any websocket client. I recommend [websocat](https://github.com/vi/websocat):

```bash
websocat ws://127.0.0.1:9080

# Or if you have rlwrap installed (You should)
rlwrap websocat ws://127.0.0.1:9080
```

The problem with this is that stdout and stderr will be displayed on the server while only the return will be shown on the client.

To connect to the server you can run: `gdrepl client`. You can then type `help` to see what special server commands you can run like `script_code` to check what currently generated script is.

Custom server commands are:

```json
{
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

```


### Environtment variables

If `DEBUG=1` is set then the server will keep writing the formed script to stdout.

If `TEST=1` the websocket server won't run and simple test functions will be executed.

### Why the weird approach

My main goal was to make a safe to host irc bot REPL, spawning a docker image for each command. The `OS` module contains dangerous functions that allow you to run shell commands. In that process I realized it would be easy to make a normal CLI REPL as well.

## Run the IRC bot

Requires python3 and a godot image. Use the `irc_bot` folder.

1. Install gdrepl: `pip3 install gdrepl`
2. Build a docker image for it (See section bellow).
3. Copy `config.py.example` to `config.py`
4. Edit it for your needs. 
5. You can create a virtual environment or not: `pip3 install bot/requirements.py`  
6. Run `./bot.py`

To keep it running and manage it i recommend pm2: https://pm2.keymetrics.io/



## Docker

### Build GODOT

To build godot for your platform run  `docker-compose build` inside the `build/` directory. Then run `./copy.sh` and the resulting binary will be inside `build/bin/`.

This was only tested on AARCH64. If you want to run the irc bot in a supported platform simply grab godot-server from https://godotengine.org/download/server

### Build and image for the irc bot

If you build godot, put the binary inside the `docker` folder and rename it to `godot`. Then inside `docker/` run `docker-compose build` and you will have it. You can also use the same docker image you build it from, just update the bot config accordingly.

### Why the dockerfile doesn't download godot binary automatically?

Because I hate when I try to use one of those docker images but they are x86_64 only. Godot is fairly easy to build.
If you are on aarch64 like me (Raspberry Pi 4, oracle Ampere A1) this is how I build godot:
```bash
scons arch=arm64 platform=server target=release_debug use_llvm=no colored=yes pulseaudio=no CFLAGS="$CFLAGS -fPIC -Wl,-z,relro,-z,now"  CXXFLAGS="$CXXFLAGS -fPIC -Wl,-z,relro,-z,now" LINKFLAGS="$LDFLAGS"  -j4
strip bin/godot*
```


# TODO

- [ ] Have the GDScript websocket server be a proper api or protoccol using json or something less hacky than we have now
- [ ] GDScript methods and properties auto completion using godot lsp
- [ ] Auto unindent (like with else, elif)
