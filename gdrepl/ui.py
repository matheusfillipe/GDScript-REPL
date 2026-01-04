class ToolbarStyler:
    @staticmethod
    def colorful(mode: str) -> str:
        return f"[F4] {mode}  [Ctrl+X Ctrl+E] Editor  [Ctrl+D] Quit  [!help] Commands"

    @staticmethod
    def minimal(mode: str) -> str:
        return f"[F4] {mode}  [Ctrl+D] Quit  [!help] Commands"

    @staticmethod
    def compact(mode: str) -> str:
        return f"[F4] {mode}  [Ctrl+D] Quit"
