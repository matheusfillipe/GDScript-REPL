import os
import subprocess
import tempfile
from typing import Any

from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings

from .config import REPLConfig


class REPLKeyBindings:
    def __init__(self, config: REPLConfig) -> None:
        self.config = config
        self.bindings = KeyBindings()
        self._setup_bindings()

    def _setup_bindings(self) -> None:
        @self.bindings.add("tab", eager=True)
        def insert_tab(event: Any) -> None:
            buffer = event.current_buffer

            if buffer.suggestion:
                buffer.insert_text(buffer.suggestion.text)
            else:
                buffer.insert_text("    ")

        @self.bindings.add("f4")
        def toggle_mode(event: Any) -> None:
            app = event.app
            if app.editing_mode == EditingMode.VI:
                app.editing_mode = EditingMode.EMACS
            else:
                app.editing_mode = EditingMode.VI

        @self.bindings.add("c-x", "c-e")
        def open_editor(event: Any) -> None:
            self._open_external_editor(event)

        @self.bindings.add("c-l")
        def clear_screen(event: Any) -> None:
            event.app.renderer.clear()

    def _open_external_editor(self, event: Any) -> None:
        buffer = event.app.current_buffer
        current_text = buffer.text

        with tempfile.NamedTemporaryFile(mode="w", suffix=self.config.temp_suffix, delete=False) as tmp:
            tmp.write(current_text)
            temp_file = tmp.name

        def edit_in_terminal() -> None:
            editor = os.environ.get("EDITOR", self.config.editor)
            subprocess.call([editor, temp_file])

            # Read the edited content back into the buffer
            # Convert tabs to spaces to avoid display issues and execution problems
            with open(temp_file) as f:
                content = f.read()
                buffer.text = content.replace("\t", "    ")

            # Clean up temp file
            os.unlink(temp_file)

        # Use run_in_terminal to properly suspend and resume the app
        run_in_terminal(edit_in_terminal)
