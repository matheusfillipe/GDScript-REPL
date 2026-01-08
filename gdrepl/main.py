import os
import re
import subprocess as sb
from dataclasses import dataclass

import click
import pexpect
from click_default_group import DefaultGroup
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import PromptSession
from pygments.lexers.gdscript import GDScriptLexer

from .client import client as wsclient
from .commands import COMMANDS
from .commands import Command
from .config import ConfigManager
from .constants import KEYWORDS
from .constants import PORT
from .constants import STDOUT_MARKER_END
from .constants import STDOUT_MARKER_START
from .constants import VI
from .find_godot import find_available_port
from .find_godot import find_godot
from .find_godot import godot_command
from .history import RotatingFileHistory
from .keybindings import REPLKeyBindings
from .styles import REPLStyles
from .ui import ToolbarStyler


TIMEOUT = 0

GODOT = find_godot()


@dataclass
class PromptOptions:
    vi: bool = False
    timeout: int = TIMEOUT


class CustomCompleter(Completer):
    """Auto completion and commands"""

    def __init__(self):
        # Add ! prefix to all commands for IPython-style completion
        command_list = ["!" + cmd for cmd in COMMANDS]
        self.word_completer = WordCompleter(KEYWORDS + command_list, WORD=True)
        self.document = None
        self.iterator = None

    def _create_iterator(self, completer, document, complete_event):
        self.iterator = completer.get_completions(document, complete_event)

    def get_completions(self, document, complete_event):
        # Don't complete at start of line (allow literal tabs for indentation)
        if document.cursor_position == 0 or document.text_before_cursor.isspace():
            return

        # Only complete after 1st character of last word
        if len(document.text_before_cursor.split(" ")[-1]) < 1:
            return

        cmd = document.text.split()[0] if document.text.strip() else ""
        # Handle IPython-style commands with ! prefix
        cmd_name = cmd[1:] if cmd.startswith("!") else cmd

        if cmd_name in COMMANDS and len(document.text_before_cursor.strip()) > len(cmd):
            sub_doc = Document(document.text[len(cmd) + 1 :])
            self._create_iterator(COMMANDS[cmd_name].completer, sub_doc, complete_event)

        elif document != self.document:
            self.document = document
            self._create_iterator(self.word_completer, document, complete_event)

        if self.iterator:
            yield from self.iterator


def wait_for_output(server, timeout):
    try:
        server.expect(STDOUT_MARKER_END, timeout=timeout)
        output = server.before.decode()
        # Remove any stdout markers from the output
        output = output.replace(STDOUT_MARKER_START, "")
        output = output.replace(STDOUT_MARKER_END, "")
        # Filter out void return errors (these are handled by retry logic)
        lines = output.split("\n")
        filtered_lines = []
        skip_next = 0
        for i, line in enumerate(lines):
            if skip_next > 0:
                skip_next -= 1
                continue
            # Skip "Cannot get return value" errors and their stack traces
            if "Cannot get return value" in line and 'returns "void"' in line:
                # Skip this line and the next few lines (stack trace)
                skip_next = 10  # Skip the stack trace
                continue
            if "SCRIPT ERROR:" in line and i + 1 < len(lines) and "Cannot get return value" in lines[i + 1]:
                skip_next = 11  # Skip SCRIPT ERROR line + stack trace
                continue
            filtered_lines.append(line)
        output = "\n".join(filtered_lines).strip()
        if output:
            print(output)
    except pexpect.exceptions.TIMEOUT:
        pass
    try:
        server.expect(r"SCRIPT ERROR:(?!.*Cannot get return value)(.+)", timeout=timeout)
        if server.match and server.match.group(1):
            error = server.match.group(1).decode().strip()
            error = re.sub("\r\n" + r".*ERROR:.* Method failed\..*" + "\r\n.*", "", error)
            print(error)
    except pexpect.exceptions.TIMEOUT:
        pass


def repl_loop(client, options: PromptOptions, server=None):
    config_manager = ConfigManager()
    config = config_manager.config

    history = RotatingFileHistory(
        os.path.expanduser(config.history_file),
        max_entries=config.max_history,
        backup_count=config.backup_count,
    )

    key_bindings = REPLKeyBindings(config).bindings
    auto_suggest = AutoSuggestFromHistory() if config.auto_suggest else None

    style = getattr(REPLStyles, config.toolbar_style.upper(), REPLStyles.COLORFUL)

    def get_toolbar():
        app = get_app()
        if app.editing_mode == EditingMode.VI:
            # Get Vi mode status (insert, navigation, replace)
            vi_mode = app.vi_state.input_mode.name.lower()
            mode = f"Vi [{vi_mode}]"
        else:
            mode = "Emacs"
        toolbar_func = getattr(ToolbarStyler, config.toolbar_style, ToolbarStyler.colorful)
        return toolbar_func(mode)

    # Fill out our auto completion with server commands as well
    helpmsg = client.send("help")
    for line in helpmsg.split("\n"):
        helplist = line.split(":")
        if len(helplist) != 2:
            continue

        cmd = helplist[0]
        help = helplist[1]

        # Let us override the server commands help message
        if cmd in COMMANDS:
            continue
        COMMANDS[cmd] = Command(help=help, send_to_server=True)

    # Configure cursor shapes for Vi mode: beam in insert, block in normal, underline in replace
    cursor_shape_config = ModalCursorShapeConfig()

    # Note: Tab completion is disabled to allow manual indentation with Tab key
    session: PromptSession[str] = PromptSession(
        history=history,
        key_bindings=key_bindings,
        auto_suggest=auto_suggest,
        bottom_toolbar=get_toolbar,
        lexer=PygmentsLexer(GDScriptLexer),
        completer=None,
        complete_while_typing=False,
        style=style,
        cursor=cursor_shape_config,
        editing_mode=EditingMode.VI if options.vi else EditingMode.EMACS,
    )

    multiline_buffer = ""
    multiline = False
    while True:
        try:
            # Use simple prompts - don't auto-insert indentation as it causes display issues
            cmd = session.prompt("... ") if multiline else session.prompt(">>> ")
        except KeyboardInterrupt:
            multiline = False
            multiline_buffer = ""
            continue
        except EOFError:
            try:
                confirm = input("\nAre you sure you want to quit? (y/n): ").strip().lower()
                if confirm in ["y", "yes"]:
                    client.close()
                    break
                else:
                    print("Continuing...")
                    continue
            except (EOFError, KeyboardInterrupt):
                client.close()
                break

        # Handle empty line - execute multiline buffer or skip
        if len(cmd.strip()) == 0:
            if not multiline:
                continue
            # Empty line in multiline mode - execute the buffer
            multiline = False
            # Force execution (semicolon terminates statement in GDScript)
            # Note: Tab key inserts spaces, but normalize any literal tabs just in case
            buffer_to_send = multiline_buffer.replace("\t", "    ") + ";"
            resp = client.send(buffer_to_send)
            multiline_buffer = ""
            if resp:
                print(resp)
            if server is not None:
                wait_for_output(server, options.timeout)
            continue

        if cmd.strip() in ["!quit", "!exit"]:
            client.send(cmd, False)
            client.close()
            break

        # Handle commands with ! prefix (IPython-style)
        if not multiline and cmd.strip().startswith("!"):
            cmd_name = cmd.strip()[1:].split()[0] if len(cmd.strip()) > 1 else ""
            if cmd_name in COMMANDS:
                command = COMMANDS[cmd_name]
                command.do(client, cmd.strip()[1:].split()[1:])
                if command.send_to_server:
                    # Send to server without the ! prefix
                    resp = client.send(cmd.strip()[1:])
                    if resp:
                        print(resp)
                continue
            else:
                print(f"Error: Unknown command '!{cmd_name}'. Type '!help' for available commands.")
                continue

        # Switch to multiline until return is pressed twice
        if cmd.strip().endswith(":"):
            multiline = True

        multiline_buffer += cmd
        if multiline:
            multiline_buffer += "\n"
            continue

        resp = client.send(multiline_buffer)
        multiline_buffer = ""

        if resp:
            print(resp)

        if server is not None:
            wait_for_output(server, options.timeout)


def start_message():
    pass


@click.group(cls=DefaultGroup, default="run", default_if_no_args=True)
def cli():
    pass


@cli.command(help="Launch the godot server and starts the repl")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--godot", default=GODOT, help="Path to godot executable")
@click.option("--command", default="", help="Custom command to run the server script with")
@click.option("--timeout", default=TIMEOUT, help="Time to wait for godot output")
def run(vi, godot, command, timeout):
    if not godot:
        return
    server = None

    port = find_available_port(PORT)
    env_copy = os.environ.copy()
    env_copy["PORT"] = str(port)

    server = pexpect.spawn(command, env=env_copy) if command else pexpect.spawn(godot_command(godot), env=env_copy)
    server.expect(r".*Godot Engine (\S+) .*")
    version = server.match.group(1).decode() if server.match and server.match.group(1) else ""
    print("Godot", version, "listening on:", port)

    server.expect("Gdrepl Listening on .*")

    start_message()
    client = wsclient(port=port)
    repl_loop(client, PromptOptions(vi=vi, timeout=timeout), server)


@cli.command(help="Connects to a running godot repl server")
@click.option("--vi", is_flag=True, default=VI, help="Use vi mode")
@click.option("--port", default=PORT, help="Port to connect to")
def client(vi, port):
    client = wsclient(port=port)
    start_message()
    print("Not launching server..")
    repl_loop(client, PromptOptions(vi=vi))


@cli.command(help="Starts the gdscript repl websocket server")
@click.option("--godot", default=GODOT, help="Path to godot executable")
@click.option("--port", default=PORT, help="Port to listen on")
@click.option("--verbose", is_flag=True, default=False, help="Enable debug output")
def server(port, godot, verbose):
    if not godot:
        return
    env_copy = os.environ.copy()
    if port:
        env_copy["PORT"] = str(port)
    else:
        env_copy["PORT"] = str(find_available_port(port))

    if verbose:
        env_copy["DEBUG"] = "1"

    sb.run(godot_command(godot), shell=True, env=env_copy)
