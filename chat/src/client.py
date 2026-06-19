import json
import socket as sock
from io import TextIOWrapper
from classes import User, Cmd


class Client:
    def __init__(
        self,
        socket: sock.socket | None = None,
        address=None,
        user: User | None = None,
    ):
        self.socket: sock.socket = (
            socket if socket else sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        )
        self.address = address
        self.user = user
        self.rfile: TextIOWrapper | None = None
        self.wfile: TextIOWrapper | None = None

        if socket:
            self._init_streams()

    def _init_streams(self):
        self.rfile = self.socket.makefile("r", encoding="utf-8")
        self.wfile = self.socket.makefile("w", encoding="utf-8")

    def connect(self, host: str, port: int) -> bool:
        try:
            self.socket.connect((host, port))
            self.address = (host, port)
            self._init_streams()
            print(f"[+] Conectado exitosamente a {host}:{port}")
            return True
        except Exception as e:
            print(f"[-] No se pudo conectar a {host}:{port}: {e}")
            return False

    def send(self, data: dict):
        try:
            if self.wfile:
                if self.user:
                    data["user"] = self.user.to_dict()
                self.wfile.write(f"{json.dumps(data)}\n")
                self.wfile.flush()
        except Exception as e:
            print(f"[-] Error al enviar a {self.address}: {e}")

    def receive(self) -> dict | None:
        try:
            if not self.rfile:
                return None
            raw = self.rfile.readline()
            if not raw:
                raise ConnectionAbortedError(
                    "La conexión fue cerrada por el extremo remoto."
                )
            return json.loads(raw)
        except Exception as e:
            print(f"[-] Error al recibir de {self.address}: {e}")
            return None

    def check_courier(self, res: dict) -> bool:
        if not self.user:
            return False
        if not res["data"].get("to", []):
            return True
        data = res["data"]
        is_author = self.user.name == data["from"]
        is_recipient = self.user.name in data["to"]
        return is_author or is_recipient

    def set_user(self, data: dict | None = None):
        if data is None:
            self.user = None
        else:
            self.user = User.create(data)

    def process_message(self, msg: str):
        if msg.startswith("/"):
            parts = msg[1:].split(" ")
            cmd = parts[0].lower()

            match cmd:
                case "dm":
                    if len(parts) < 3:
                        print("[-] Uso: /dm <usuario1> <usuario2> ... <mensaje>")
                        return
                    content = parts[-1]
                    recvs = parts[1:-1]
                    req = {
                        "command": Cmd.MSG,
                        "data": {"receivers": recvs, "message": content},
                    }
                    self.send(req)
                case "exit":
                    req = {"command": Cmd.EXIT, "data": {}}
                    self.send(req)
                case _:
                    print(f"[-] Comando desconocido: {cmd}")
        else:
            req = {"command": Cmd.MSG, "data": {"receivers": [], "message": msg}}
            self.send(req)

    def disconnect(self):
        try:
            if self.rfile:
                self.rfile.close()
            if self.wfile:
                self.wfile.close()
            self.socket.close()
            print(f"[#] Conexión cerrada limpiamente con {self.address}")
        except Exception as e:
            print(f"[-] Error al desconectar a {self.address}: {e}")
