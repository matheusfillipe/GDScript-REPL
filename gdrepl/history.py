import os
import shutil
from pathlib import Path

from prompt_toolkit.history import FileHistory


class RotatingFileHistory(FileHistory):
    def __init__(self, filename: str, max_entries: int = 10000, backup_count: int = 3) -> None:
        expanded_filename = os.path.expanduser(filename)
        # Ensure parent directory exists
        Path(expanded_filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(expanded_filename)
        self.max_entries = max_entries
        self.backup_count = backup_count
        self._ensure_rotation()

    def _ensure_rotation(self) -> None:
        if self._count_entries() > self.max_entries:
            self._rotate_history()

    def _rotate_history(self) -> None:
        history_path = Path(str(self.filename))

        for i in range(self.backup_count - 1, 0, -1):
            old_file = history_path.with_suffix(f".{i}")
            new_file = history_path.with_suffix(f".{i + 1}")
            if old_file.exists():
                shutil.move(str(old_file), str(new_file))

        if history_path.exists():
            shutil.move(str(history_path), str(history_path.with_suffix(".1")))

    def _count_entries(self) -> int:
        try:
            with open(self.filename) as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            return 0

    def store_string(self, string: str) -> None:
        super().store_string(string)
        self._ensure_rotation()
