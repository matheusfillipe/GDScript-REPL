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

    @patch("subprocess.call")
    @patch("os.environ.get")
    def test_external_editor_with_env_var(self, mock_env_get, mock_subprocess):
        """Test external editor opens with environment variable"""
        mock_env_get.return_value = "nano"

        config = REPLConfig()
        key_bindings = REPLKeyBindings(config)

        # Mock event and buffer
        mock_event = MagicMock()
        mock_event.app.current_buffer.text = "test content"
        mock_event.app.suspend_to_background = MagicMock()

        # Find and call the open_editor function
        for binding in key_bindings.bindings.bindings:
            if hasattr(binding, "handler") and binding.handler.__name__ == "open_editor":
                binding.handler(mock_event)
                break

        mock_env_get.assert_called_with("EDITOR", "vim")
        mock_subprocess.assert_called_once()

    @patch("subprocess.call")
    @patch("os.environ.get")
    def test_external_editor_fallback(self, mock_env_get, mock_subprocess):
        """Test external editor falls back to config default"""
        mock_env_get.return_value = None

        config = REPLConfig(editor="emacs")
        key_bindings = REPLKeyBindings(config)

        mock_event = MagicMock()
        mock_event.app.current_buffer.text = "test content"
        mock_event.app.suspend_to_background = MagicMock()

        # Find and call the open_editor function
        for binding in key_bindings.bindings.bindings:
            if hasattr(binding, "handler") and binding.handler.__name__ == "open_editor":
                binding.handler(mock_event)
                break

        mock_env_get.assert_called_with("EDITOR", "emacs")
        mock_subprocess.assert_called_once()

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
