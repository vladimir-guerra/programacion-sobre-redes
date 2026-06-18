import json
import socket as sock
from io import TextIOWrapper


class Client:
    def __init__(self, socket: sock.socket | None = None, address=None, name: str = ""):
        self.socket: sock.socket = (
            socket if socket else sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        )
        self.address = address
        self.name: str = name

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
