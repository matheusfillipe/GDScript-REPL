from gdrepl.ui import ToolbarStyler


class TestToolbarStyler:
    def test_colorful_toolbar(self):
        """Test colorful toolbar returns correct format"""
        result = ToolbarStyler.colorful("Vi")

        assert isinstance(result, str)
        assert "[F4]" in result
        assert "Vi" in result
        assert "[Ctrl+D]" in result
        assert "Quit" in result
        assert "[!help]" in result

    def test_minimal_toolbar(self):
        """Test minimal toolbar returns correct format"""
        result = ToolbarStyler.minimal("Emacs")

        assert isinstance(result, str)
        assert "[F4]" in result
        assert "Emacs" in result
        assert "[Ctrl+D]" in result
        assert "[!help]" in result

    def test_compact_toolbar(self):
        """Test compact toolbar returns correct format"""
        result = ToolbarStyler.compact("Vi")

        assert isinstance(result, str)
        assert "[F4]" in result
        assert "Vi" in result
        assert "[Ctrl+D]" in result
