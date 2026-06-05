from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, Label
from client import Client


class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Iniciar Sesión / Registrarse", id="login-title")
        yield Input(placeholder="Nombre de usuario", id="username")
        yield Input(placeholder="Contraseña", password=True, id="password")
        yield Button("Enviar", variant="success", id="btn_send")
        yield Label("", id="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_send":
            username = self.query_one("#username", Input).value
            password = self.query_one("#password", Input).value

            if username and password:
                req = {
                    "action": "auth",
                    "username": username,
                    "password": password,
                }
                user: dict = self.app.client.request(req)
                if user.get("success"):
                    print(user)
                    #self.app.switch_screen()
                else:
                    self.query_one("#error", Label).update(
                        "[red]Credenciales inválidas.[/red]"
                    )
            else:
                self.query_one("#error", Label).update("[red]Campos faltantes.[/red]")


class Tui(App):
    def on_mount(self) -> None:
        try:
            self.client = Client("0.0.0.0", 8080)
        except Exception as e:
            print(f"No se pudo conectar al servidor: {e}")
            self.exit()
            return
        self.push_screen(LoginScreen())

    def on_unmount(self) -> None:
        if hasattr(self, "network_client"):
            self.network_client.close()


if __name__ == "__main__":
    Tui().run()
