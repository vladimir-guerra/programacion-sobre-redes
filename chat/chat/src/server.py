import socket
import threading
from orm import User, get_session, Message, UserMessage
from client import Client
from classes import Cmd
from datetime import datetime


class Server:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.active_clients: list[Client] = []
        self.lock = threading.Lock()

    def start(self, host: str, port: int):
        init_db()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen()

        while True:
            try:
                client_socket, address = self.socket.accept()
                c = Client(client_socket, address)
                threading.Thread(target=self.handle_client, args=(c,)).start()
                with self.lock:
                    self.active_clients.append(c)
            except Exception as e:
                print(f"[-] Error al aceptar conexión: {e}")
                break
        self.socket.close()
        print(f"[-] Servidor cerrado")

    def _sys_msg(self, msg: str) -> str:
        return f"[SYSTEM] ({datetime.now().strftime("%H:%M | %d/%m/%Y")}):\n{msg}"

    def _sys(self, client: Client, msg: str, cmd: Cmd):
        client.send(self._fmt(cmd, self._sys_msg(msg)), True)

    def handle_client(self, c: Client):
        try:
            while True:
                data = c.receive()
                if not data or not "command" in data:
                    continue
                cmd = data.pop("command")
                req: dict = data.pop("data")

                match cmd:
                    case Cmd.AUTH:
                        with get_session() as s:
                            u = User.auth(s, req["username"], req["password"])
                            if u:
                                msgs: list[Message] = Message.get_from_user(s, u.id)
                                u_dict = {
                                    "messages": [m.fmt_message for m in msgs],
                                    "user": {"name": u.name, "id": u.id},
                                }
                                c.set_user(u_dict["user"])
                                c.send(self._fmt(cmd, u_dict, True))
                            else:
                                self._sys(c, "Credenciales inválidas.", cmd)
                    case Cmd.MSG:
                        if not c.user:
                            return self._sys(c, "No estás autenticado", cmd)
                        with get_session() as s:
                            recv: list[str] = req.get("receivers", [])
                            msg: Message = Message.send(
                                s, req["message"], c.user.id, recv
                            )
                        data = {
                            "message": msg.fmt_message,
                            "to": recv,
                            "from": msg.author.name,
                        }
                        self.broadcast(self._fmt(cmd, data, True))
                    case Cmd.HELP:
                        if not c.user:
                            return self._sys(c, "No estás autenticado", cmd)
                        help = "/dm <usuario1> ... <usuarioN> <mensaje> | envía un mensaje privado\n/help | ver comandos\n/exit | cerrar sesión"
                        self._sys(c, help, cmd)
                    case Cmd.EXIT:
                        if not c.user:
                            return self._sys(c, "No estás autenticado.", cmd)
                        data = {
                            "message": self._sys_msg(f"{c.user.name} ha salido."),
                            "from": "[SYSTEM]",
                        }
                        self.broadcast(self._fmt(Cmd.MSG, data, True))
                        c.set_user()
                        self._sys(c, "Saliste.", cmd)
                        break
                    case _:
                        self._sys(c, "Comando inexistente.", cmd)
        except Exception as e:
            print(f"[-] Error manejando cliente: {e}")
        finally:
            with self.lock:
                self.active_clients.remove(c)
            c.disconnect()
            print("[+] Socket del cliente cerrado y removido.")

    def _fmt(self, cmd: Cmd, data: dict, succes: bool = False) -> dict:
        return {"succes": succes, "command": cmd, "data": data}

    def broadcast(self, data: dict):
        with self.lock:
            ac = self.active_clients
        for c in ac:
            try:
                if c.check_courier(data):
                    c.send(data)
            except:
                c.disconnect()
                with self.lock:
                    self.active_clients.remove(c)


if __name__ == "__main__":
    from orm import init_db
    init_db()
    Server().start("0.0.0.0", 8080)
