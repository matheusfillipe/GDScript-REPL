from unittest.mock import MagicMock
from unittest.mock import patch

from prompt_toolkit.enums import EditingMode

from gdrepl.config import REPLConfig
from gdrepl.keybindings import REPLKeyBindings


class TestREPLKeyBindings:
    def test_key_bindings_initialization(self):
        """Test that key bindings are properly initialized"""
        config = REPLConfig()
        key_bindings = REPLKeyBindings(config)

        assert key_bindings.config == config
        assert key_bindings.bindings is not None

    @patch("gdrepl.keybindings.run_in_terminal")
    @patch("subprocess.call")
    def test_external_editor_with_env_var(self, mock_subprocess, mock_run_in_terminal):
        """Test external editor opens with environment variable"""
        config = REPLConfig()
        key_bindings = REPLKeyBindings(config)

        # Mock event and buffer
        mock_event = MagicMock()
        mock_event.app.current_buffer.text = "test content"

        # Mock run_in_terminal to execute callback immediately
        def run_in_terminal_side_effect(callback):
            callback()

        mock_run_in_terminal.side_effect = run_in_terminal_side_effect

        # Set EDITOR env var
        with patch.dict("os.environ", {"EDITOR": "nvim"}):
            # Find and call the open_editor function
            for binding in key_bindings.bindings.bindings:
                if hasattr(binding, "handler") and binding.handler.__name__ == "open_editor":
                    binding.handler(mock_event)
                    break

            # Should call subprocess with nvim
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0][0]
            assert args[0] == "nvim"

    @patch("gdrepl.keybindings.run_in_terminal")
    @patch("subprocess.call")
    def test_external_editor_fallback(self, mock_subprocess, mock_run_in_terminal):
        """Test external editor falls back to config default"""
        config = REPLConfig(editor="emacs")
        key_bindings = REPLKeyBindings(config)

        mock_event = MagicMock()
        mock_event.app.current_buffer.text = "test content"

        # Mock run_in_terminal to execute callback immediately
        def run_in_terminal_side_effect(callback):
            callback()

        mock_run_in_terminal.side_effect = run_in_terminal_side_effect

        # No EDITOR env var - should use config default
        with patch.dict("os.environ", {}, clear=True):
            # Find and call the open_editor function
            for binding in key_bindings.bindings.bindings:
                if hasattr(binding, "handler") and binding.handler.__name__ == "open_editor":
                    binding.handler(mock_event)
                    break

            # Should call subprocess with emacs (config default)
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0][0]
            assert args[0] == "emacs"

    def test_mode_toggle(self):
        """Test F4 mode toggle functionality"""
        config = REPLConfig()
        key_bindings = REPLKeyBindings(config)

        # Mock event with Emacs mode
        mock_event = MagicMock()
        mock_app = MagicMock()
        mock_app.editing_mode = EditingMode.EMACS
        mock_event.app = mock_app

        # Find and call the toggle_mode function
        for binding in key_bindings.bindings.bindings:
            if hasattr(binding, "handler") and binding.handler.__name__ == "toggle_mode":
                binding.handler(mock_event)
                break

        # Should switch to VI
        assert mock_app.editing_mode == EditingMode.VI

        # Toggle back to Emacs
        binding.handler(mock_event)
        assert mock_app.editing_mode == EditingMode.EMACS

    def test_tab_accepts_suggestion(self):
        """Test that Tab accepts auto-suggestion when available"""
        config = REPLConfig()
        key_bindings = REPLKeyBindings(config)

        mock_event = MagicMock()
        mock_buffer = MagicMock()
        mock_suggestion = MagicMock()
        mock_suggestion.text = "suggested_text"
        mock_buffer.suggestion = mock_suggestion
        mock_event.current_buffer = mock_buffer

        for binding in key_bindings.bindings.bindings:
            if hasattr(binding, "handler") and binding.handler.__name__ == "insert_tab":
                binding.handler(mock_event)
                break

        mock_buffer.insert_text.assert_called_once_with("suggested_text")

    def test_tab_inserts_spaces_without_suggestion(self):
        """Test that Tab inserts spaces when no suggestion is available"""
        config = REPLConfig()
        key_bindings = REPLKeyBindings(config)

        mock_event = MagicMock()
        mock_buffer = MagicMock()
        mock_buffer.suggestion = None
        mock_event.current_buffer = mock_buffer

        for binding in key_bindings.bindings.bindings:
            if hasattr(binding, "handler") and binding.handler.__name__ == "insert_tab":
                binding.handler(mock_event)
                break

        mock_buffer.insert_text.assert_called_once_with("    ")
