import tempfile
from pathlib import Path
from unittest.mock import patch

from gdrepl.config import ConfigManager


class TestConfigManager:
    def setUp(self):
        """Test configuration data"""
        return {"editor": "nano", "max_history": 5000, "toolbar_style": "minimal"}

    def test_default_config_creation(self):
        """Test that default config is created with correct values"""
        config_manager = ConfigManager()
        config = config_manager.config

        assert config.editor == "vim"
        assert config.history_file == "~/.config/gdrepl/history"
        assert config.max_history == 10000
        assert config.history_rotation is True
        assert config.backup_count == 3
        assert config.toolbar_style == "colorful"
        assert config.auto_suggest is True
        assert config.temp_suffix == ".gd"

    def test_config_file_creation(self):
        """Test that config file is created when it doesn't exist"""
        config_manager = ConfigManager()
        config_file = config_manager.config_file

        assert config_file.exists()
        assert config_file.parent.exists()

    def test_config_loading(self):
        """Test loading configuration from file"""
        test_config = {
            "editor": "nano",
            "max_history": 5000,
            "toolbar_style": "minimal",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".config" / "gdrepl"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.yaml"

            import yaml

            with open(config_file, "w") as f:
                yaml.dump(test_config, f)

            # Patch Path.home to return our temp directory
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                config_manager = ConfigManager()
                config = config_manager.config

                assert config.editor == "nano"
                assert config.max_history == 5000
                assert config.toolbar_style == "minimal"

    def test_invalid_config_handling(self):
        """Test that invalid config falls back to defaults"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".config" / "gdrepl"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.yaml"

            # Write invalid YAML
            with open(config_file, "w") as f:
                f.write("invalid: yaml: content: [")

            # Patch Path.home to return our temp directory
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                config_manager = ConfigManager()
                config = config_manager.config

                # Should fall back to defaults
                assert config.editor == "vim"
                assert config.max_history == 10000
