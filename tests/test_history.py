import tempfile
from pathlib import Path

from gdrepl.history import RotatingFileHistory


class TestRotatingFileHistory:
    def test_history_creation(self):
        """Test RotatingFileHistory initialization"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            history = RotatingFileHistory(temp_file.name, max_entries=100, backup_count=2)

            assert history.max_entries == 100
            assert history.backup_count == 2
            assert history.filename == temp_file.name

    def test_count_entries_empty_file(self):
        """Test counting entries in empty file"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            history = RotatingFileHistory(temp_file.name)
            count = history._count_entries()

            assert count == 0

    def test_count_entries_with_content(self):
        """Test counting entries with content"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("line1\nline2\nline3\n")
            temp_file.flush()

            history = RotatingFileHistory(temp_file.name)
            count = history._count_entries()

            assert count == 3

    def test_rotation_when_needed(self):
        """Test rotation when max entries exceeded"""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = Path(temp_dir) / "history"

            # Create history with 5 entries (max is 3 for test)
            with open(history_file, "w") as f:
                f.write("line1\nline2\nline3\nline4\nline5\n")

            history = RotatingFileHistory(str(history_file), max_entries=3, backup_count=2)
            history._ensure_rotation()

            # Should rotate: history -> history.1
            assert not history_file.exists()
            assert (Path(temp_dir) / "history.1").exists()

    def test_multiple_rotations(self):
        """Test multiple backup rotations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = Path(temp_dir) / "history"
            backup1 = Path(temp_dir) / "history.1"
            backup2 = Path(temp_dir) / "history.2"

            # Create existing backups
            backup1.write_text("old backup 1")
            backup2.write_text("old backup 2")

            # Create current history
            with open(history_file, "w") as f:
                f.write("line1\nline2\nline3\nline4\nline5\n")

            history = RotatingFileHistory(str(history_file), max_entries=3, backup_count=2)
            history._ensure_rotation()

            # Should shift backups: history.1 -> history.2, history -> history.1
            assert not history_file.exists()
            assert backup1.exists()
            assert backup2.exists()

    def test_store_string_triggers_rotation(self):
        """Test that storing string triggers rotation when needed"""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = Path(temp_dir) / "history"

            # Create history with max entries
            with open(history_file, "w") as f:
                f.write("line1\nline2\nline3\n")

            history = RotatingFileHistory(str(history_file), max_entries=3, backup_count=2)
            history.store_string("line4")  # This should trigger rotation

            # Should have rotated
            assert not history_file.exists()
            assert (Path(temp_dir) / "history.1").exists()
