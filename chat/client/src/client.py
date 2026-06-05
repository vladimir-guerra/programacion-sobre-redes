import json
import socket


class Client:
    def __init__(self, host: str, port: int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.file = self.socket.makefile("rw", encoding="utf-8")

    def request(self, data: dict) -> dict:
        self.send(data)
        return self.recv()

    def send(self, data: dict) -> None:
        json_data = json.dumps(data)
        self.file.write(json_data + "\n")
        self.file.flush()

    def recv(self) -> dict:
        raw_response = self.file.readline()
        if not raw_response:
            raise ConnectionError("El servidor cerró la conexión.")
        return json.loads(raw_response)

    def close(self):
        self.file.close()
        self.socket.close()
