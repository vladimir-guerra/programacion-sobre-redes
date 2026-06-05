import socket
import threading
import json
from orm import User, get_session


class Server:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.active_clients = []
        self.lock = threading.Lock()

    def start(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen()

        while True:
            try:
                client_socket, address = self.socket.accept()
                thread = threading.Thread(
                    target=self.handle_client, args=(client_socket,)
                )
                thread.start()
                with self.lock:
                    self.active_clients.append(client_socket)
            except Exception as e:
                print(f"[-] Error al aceptar conexión: {e}")

    def handle_client(self, client_socket):
        rfile = client_socket.makefile("r", encoding="utf-8")
        try:
            while True:
                raw_data = rfile.readline()
                if not raw_data:
                    print("[-] El cliente se desconectó voluntariamente.")
                    break

                req: dict = json.loads(raw_data)
                action = req.get("action")

                match action:
                    case "auth":
                        with get_session() as s:
                            user = User.auth(
                                s, req.get("username"), req.get("password")
                            )
                        if user:
                            forum_data = {}
                            if user.members:
                                forum_data = {
                                    "name": user.members[0].forum.name,
                                    "role": user.members[0].role,
                                }
                            res = {
                                "success": True,
                                "data": {
                                    "username": user.name,
                                    "forum": forum_data,
                                },
                            }
                        else:
                            res = {"success": False}
                        self.unicast(res, client_socket)
                    case "message":
                        self.broadcast(req, client_socket)
        except Exception as e:
            print(f"[-] Error manejando cliente: {e}")
        finally:
            try:
                rfile.close()
            except:
                pass
            with self.lock:
                if client_socket in self.active_clients:
                    self.active_clients.remove(client_socket)
            client_socket.close()
            print("[+] Socket del cliente cerrado y removido.")

    def unicast(self, res: dict, client_socket):
        try:
            payload = json.dumps(res) + "\n"
            client_socket.sendall(payload.encode("utf-8"))
        except Exception as e:
            with self.lock:
                if client_socket in self.active_clients:
                    self.active_clients.remove(client_socket)
            print(f"[-] Error en unicast: {e}")

    def broadcast(self, res: dict, sender_socket):
        with self.lock:
            targets = list(self.active_clients)
        for client_socket in targets:
            if client_socket != sender_socket:
                self.unicast(res, client_socket)


if __name__ == "__main__":
    Server("0.0.0.0", 8080).start()
