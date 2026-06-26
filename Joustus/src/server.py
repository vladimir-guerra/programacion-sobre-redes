from __future__ import annotations
import random
import socket
import threading
from client import Client
from classes import Card, TurnRes, Slot, SlotType, TurnReq, Matrix, Hand


class Server:
    def __init__(self):
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wp: Client | None = None
        self.lock: threading.Lock = threading.Lock()

    def start(self, host: str, port: int):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen()
        print(f"[+] Servidor listo en {host}:{port}")
        while True:
            try:
                client_socket, address = self.socket.accept()
                p = Client(client_socket, address)
                print(f"[+] Nueva conexión física desde {address}")
                threading.Thread(target=self.matchmake, args=(p,), daemon=True).start()
            except Exception as e:
                print(f"[-] Error en el bucle principal: {e}")

    def matchmake(self, p: Client):
        try:
            with self.lock:
                if self.wp:
                    p.name = "Jugador 2"
                    threading.Thread(
                        target=self._handle_game, args=(self.wp, p)
                    ).start()
                    self.wp = None
                else:
                    p.name = "Jugador 1"
                    self.wp = p
        except Exception as e:
            print(e)

    def _create_matrix(self) -> Matrix:
        matrix = [[Slot(SlotType.BORDER) for _ in range(5)] for _ in range(5)]
        for row, col in ((0, 0), (0, 4), (4, 4), (4, 0)):
            matrix[row][col].type = SlotType.NO_SLOT
        normal_coords = []
        for row in range(1, 4):
            for col in range(1, 4):
                matrix[row][col].type = SlotType.NORMAL
                normal_coords.append((row, col))
        for row, col in random.sample(normal_coords, k=3):
            matrix[row][col].type = SlotType.GEM
        return matrix

    def _check_movement(self, mv: TurnReq) -> bool:
        def _check_pos(x: int, y: int) -> bool:
            return 0 <= x < len(mv.matrix) and 0 <= y < len(mv.matrix[0])

        if (
            not _check_pos(mv.x, mv.y)
            or not (abs(mv.vx) in (0, 1))
            or not (abs(mv.vy) in (0, 1))
        ):
            return False

        slot: Slot = mv.matrix[mv.x][mv.y]
        if slot.card:
            if not mv.is_pushed and (mv.vx, mv.vy) not in mv.card.directions:
                return False

            nx, ny = mv.get_next_pos()
            if not _check_pos(nx, ny):
                n_card = None
            else:
                n_card = mv.matrix[nx][ny].card

            if n_card and (-mv.vx, -mv.vy) in n_card.directions:
                return False

            nmv = TurnReq(slot.card, mv.matrix, nx, ny, mv.vx, mv.vy, True)
            return self._check_movement(nmv)

        if slot.type == SlotType.NO_SLOT:
            return False
        elif slot.type == SlotType.BORDER or slot.type == SlotType.GEM:
            return mv.is_pushed
        else:
            return True

    def _valid_movements(self, matrix: Matrix) -> bool:
        for x in range(1, 4):
            for y in range(1, 4):
                slot: Slot = matrix[x][y]
                if slot.card is None and slot.type == SlotType.NORMAL:
                    return True
                if slot.card is not None:
                    for d in slot.card.directions:
                        if d != None:
                            nx, ny = (x + d[0], y + d[1])
                            mv = TurnReq(slot.card, matrix, nx, ny, d[0], d[1])
                            if self._check_movement(mv):
                                return True
        return False

    def _execute_movement(self, mv: TurnReq) -> Matrix:
        mlen = len(mv.matrix)
        prev_card: Card | None = None
        if (0 <= mv.x < mlen) and (0 <= mv.y < mlen):
            prev_card = mv.matrix[mv.x][mv.y].card
            if mv.matrix[mv.x][mv.y].type != SlotType.NO_SLOT:
                mv.matrix[mv.x][mv.y].card = mv.card

        if not mv.is_pushed:
            px, py = mv.get_prev_pos()
            if (0 <= px < mlen) and (0 <= py < mlen):
                mv.matrix[px][py].card = None

        if prev_card:
            nx, ny = mv.get_next_pos()
            next_mv = TurnReq(prev_card, mv.matrix, nx, ny, mv.vx, mv.vy, True)
            return self._execute_movement(next_mv)
        return mv.matrix

    def _handle_endgame(self, matrix: Matrix) -> str:
        p = {
            "Jugador 1": 0,
            "Jugador 2": 0,
        }
        for x in range(1, 4):
            for y in range(1, 4):
                slot: Slot = matrix[x][y]
                if slot.type == SlotType.GEM and slot.card:
                    idx = slot.card.player
                    if idx in p:
                        p[idx] += 1
        if p["Jugador 1"] == p["Jugador 2"]:
            return "EMP"
        return max(p, key=lambda k: p.get(k, 0))

    def _toggle_turns(
        self,
        ap: Client,
        wp: Client,
        matrix: Matrix,
        turn_hand: tuple[list[Card], list[Card]] | tuple[Card, Card],
        winner: str = "",
    ):
        for p in (ap, wp):
            if winner == "":
                msg = "Tu turno" if p == ap else "Turno del rival"
                turn = p == ap
            else:
                msg = (
                    "Empate"
                    if winner == "EMP"
                    else "Ganaste" if p.name == winner else "Rival ganó"
                )
                turn = False
            data = {"matrix": matrix, "turn": turn, "message": msg}
            pos1, pos2 = turn_hand
            if type(pos1) == Card and type(pos2) == Card:
                res = TurnRes(newcard=pos1, precard=pos2, **data)
            elif type(pos1) == list[Card] and type(pos2) == list[Card]:
                if p == ap:
                    pos1, pos2 = pos2, pos1
                res = Hand(hand=pos1, rhand=pos2, **data)
            else:
                return
            p.send(res.to_dict())

    def _handle_game(self, p1: Client, p2: Client):
        try:
            hands = ([Card.create(p1.name) for _ in range(3)], [Card.create(p2.name) for _ in range(3)])
            is_playing: bool = True
            matrix: Matrix = self._create_matrix()

            ap, wp = p1, p2
            self._toggle_turns(ap, wp, matrix, hands)
            while is_playing:
                data = ap.receive()
                if not data:
                    c = Card.create("[SYSTEM]")
                    data = {
                        "message": "Partida interrumpida",
                        "turn": False,
                        "newcard": c,
                        "precard": c,
                    }
                    wp.send(TurnRes(matrix=matrix, **data).to_dict())
                    break
                req: TurnReq = TurnReq.create(**data)
                if not self._check_movement(req):
                    data = {
                        "message": "Movimiento inválido",
                        "turn": True,
                        "newcard": req.card,
                        "precard": req.card,
                    }
                    res = TurnRes(matrix=matrix, **data)
                    ap.send(res.to_dict())
                    continue
                matrix: Matrix = self._execute_movement(req)
                winner = ""
                if not self._valid_movements(matrix):
                    winner = self._handle_endgame(matrix)
                    is_playing = False
                new_card = Card.create(ap.name)
                self._toggle_turns(ap, wp, matrix, (new_card, req.card), winner)
                ap, wp = wp, ap
        except Exception as e:
            print(e)
        finally:
            p1.disconnect()
            p2.disconnect()


if __name__ == "__main__":
    Server().start("0.0.0.0", 8091)
