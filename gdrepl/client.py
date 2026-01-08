from websocket import WebSocketTimeoutException
from websocket import create_connection

from .constants import HOST
from .constants import PORT


class client:
    def __init__(self, host=HOST, port=PORT):
        try:
            self.ws = create_connection(f"ws://{host}:{port}", timeout=30)
        except ConnectionRefusedError:
            print("Could not connect to server")
            exit(1)

    def close(self):
        self.ws.close()

    def send(self, msg: str, get_response=True) -> str:
        """Converts ';' to '\n' and sends the message to the server, returning its response"""

        self.ws.send(msg.replace(";", "\n"))

        if not get_response:
            return ""

        try:
            resp = self.ws.recv()
        except WebSocketTimeoutException:
            return "Error: Server timeout (took longer than 30 seconds to respond)"

        if isinstance(resp, bytes):
            resp = resp.decode()
        # Return response
        if resp.startswith(">> "):
            if len(resp) > 3:
                if resp[3:] == "Err: 43":
                    return ""
                return "  -> " + resp[3:]
            return ""

        if resp == "Cleared":
            return "Environment cleared!"

        return resp
