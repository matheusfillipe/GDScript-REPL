[![Pypi](https://badge.fury.io/py/re-ircbot.svg)](https://pypi.org/project/re-ircbot/)
[![Chat with me on irc](https://img.shields.io/badge/-IRC-gray?logo=gitter)](https://mangle.ga/irc)


[![asciicast](https://asciinema.org/a/9Ks2kbs2QYxO56GoqW11GL8qk.svg)](https://asciinema.org/a/9Ks2kbs2QYxO56GoqW11GL8qk)
# GDScript REPL

This project contains:

- A dockerfile to run godot from alpine
- A simple docker file to build godot server for alpine
- A proof of concept gdscript REPL
- A IRC gdscript REPL bot 

Notice that if all you want is run gdscript files from the command line you don't need this project. Check out: https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html 

## Motivation

Gdscript is a python like language but it lacks a reply. Godot has a built in `godot -s script.gd` to run scripts but it is overkill when you just want to test out the difference between a `PoolStringArray` and a normal `Array` of strings and play around like you can do with so many languages.

That inspired me to try to turn `godot -s` into a repl, creating a [websocket server](https://docs.godotengine.org/en/stable/classes/class_websocketserver.html) that will take any string from any client in, evaluate it by creating new [GDScript](https://docs.godotengine.org/en/stable/classes/class_script.html), attaching that script to a resource node and then calling a function of that node. That requires a lot of hacky string manipulations to keep stuff working and have a separated local and global scopes allowing you to create functions, enums and classes from the repl. 

This is this still very work in progress and experimental but serves to prove the point that a repl for godot would be awesome.

## Installation

Simply:
```bash
pip3 install gdrepl

gdrepl
```

If you want to use the irc bot you will need to clone this repos and follow the instructions for the bot bellow.


## Usage

The gdscript server is implemented in a way that it will send the return output to the client but not stdout. So if you type `1+1` you will receive `2` but you can't receive `print(2)` event though that will be still shown on the server's output.

Currently this does support multiline and it wouldn't be trivial to implement but you can fake multiline input in a single line in both the irc bot and REPL by using a `;`. Those will be replaced to `\n` at runtime, for example:

```gdscript
func inc(value):; var new = value + 1; return value
```

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
  repl*   Launch the godot server and start teh repl
  client  Connects to a running godot repl server
  server  Starts the gdscript repl websocket server

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

### Environtment variables

If `DEBUG=1` is set then the server will keep writing the formed script to stdout.

If `TEST=1` the websocket serevr wont run and simple test functions will be executed.

### Why the weird approach

My main goal was to make a safe to host irc bot repl, spawning a docker image for each command. The `OS` module contains dangerous functions that allow you to run shell commands. In that process I realized it would be easy to make a normal CLI repl as well.

## Run the IRC bot

Requires python3

1. Build a docker image for it (See section bellow).
2. Copy bot_`config.py.example` to bot_`config.py`
3. Edit it for your needs. 
4. You can create a virtual environment or not: `pip3 install bot_requirements.py`  
5. Run `./bot.py`



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

