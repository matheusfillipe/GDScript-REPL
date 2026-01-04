from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class REPLConfig:
    editor: str = "vim"
    history_file: str = "~/.config/gdrepl/history"
    max_history: int = 10000
    history_rotation: bool = True
    backup_count: int = 3
    toolbar_style: str = "colorful"
    auto_suggest: bool = True
    temp_suffix: str = ".gd"


class ConfigManager:
    def __init__(self) -> None:
        self.config_dir = Path.home() / ".config" / "gdrepl"
        self.config_file = self.config_dir / "config.yaml"
        self.config = self._load_config()

    def _load_config(self) -> REPLConfig:
        if not self.config_file.exists():
            self._create_default_config()

        try:
            with open(self.config_file) as f:
                data = yaml.safe_load(f) or {}
                return REPLConfig(**data)
        except Exception:
            return REPLConfig()

    def _create_default_config(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        default_config = REPLConfig()
        self._save_config(default_config)

    def _save_config(self, config: REPLConfig) -> None:
        with open(self.config_file, "w") as f:
            yaml.dump(config.__dict__, f, default_flow_style=False)
