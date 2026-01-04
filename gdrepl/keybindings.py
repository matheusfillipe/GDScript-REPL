import os
import subprocess
import tempfile
from typing import Any

from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings

from .config import REPLConfig


class REPLKeyBindings:
    def __init__(self, config: REPLConfig) -> None:
        self.config = config
        self.bindings = KeyBindings()
        self._setup_bindings()

    def _setup_bindings(self) -> None:
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=self.config.temp_suffix, delete=False) as f:
            f.write(current_text)
            temp_file = f.name

        try:
            editor = os.environ.get("EDITOR", self.config.editor)
            event.app.suspend_to_background()
            subprocess.call([editor, temp_file])

            with open(temp_file) as f:
                buffer.text = f.read()
        finally:
            os.unlink(temp_file)
