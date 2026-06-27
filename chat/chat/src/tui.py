from client import Client
import os
import threading
from classes import Cmd


class TUI:
    def __init__(self):
        self.previous_messages: list[str] = []
        self.client: Client = Client()
        self.client.connect("127.0.0.1", 8080)
        self.start()

    @staticmethod
    def _clear_terminal():
        os.system("cls" if os.name == "nt" else "clear")

    def start(self):
        try:
            if not self.client.user:
                self.auth()
            self._clear_terminal()
            if self.client.user:
                self.chat_loop()
        except KeyboardInterrupt:
            print("\n[!] Chat finalizado.")
        finally:
            self.client.disconnect()

    def chat_loop(self):
        for m in self.previous_messages:
            print(m)
        threading.Thread(target=self.listen_to_server, daemon=True).start()
        while True:
            entry = input(f"[{self.client.user.name}@chat]$ ")
            if entry:
                self.client.process_message(entry)

    def auth(self):
        try:
            data: list = ["", ""]
            for i in range(2):
                label = "Nombre de usuario: " if i == 0 else "Contraseña: "
                while not data[i]:
                    data[i] = input(label)
            un, pw = data
            req = {"command": Cmd.AUTH, "data": {"username": un, "password": pw}}
            self.client.send(req)
            res = self.client.receive()
            if res and res["command"] == Cmd.AUTH and res["success"]:
                self.client.set_user(res["data"]["user"])
                self.previous_messages = res["data"]["messages"]
        except KeyboardInterrupt:
            raise

    def listen_to_server(self):
        while True:
            res = self.client.receive()
            if not res:
                break
            if res["command"] == Cmd.MSG:
                print(
                    f"\r{res['data']['message']}\n[{self.client.user.name}@chat]$ ",
                    end="",
                )


if __name__ == "__main__":
    TUI()
