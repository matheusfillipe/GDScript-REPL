from websocket import create_connection
from .config import HOST, PORT

class client:
    def __init__(self, host=HOST, port=PORT):
        self.ws = create_connection(f"ws://{host}:{port}")

    def close(self):
        self.ws.close()

    def send(self, msg: str) -> str:
        """Converts ';' to '\n' and sends the message to the server, returning its response"""

        self.ws.send(msg.replace(";", "\n"))
        resp = self.ws.recv().decode()

        # Return response
        if resp.startswith(">> "):
            if len(resp) > 3:
                if resp[3:] == "Err: 43":
                    return
                return "  -> " + resp[3:]
            return

        if resp == "Cleared":
            return "Environment cleared!"