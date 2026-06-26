from __future__ import annotations
import random
import enum
from dataclasses import dataclass, asdict

# Corrección de tipo: list[int, int] no es válido, usamos tuple[int, int]
type Matrix = list[list["Slot"]]


class SlotType(enum.IntEnum):
    NO_SLOT = 0
    BORDER = 1
    NORMAL = 2
    GEM = 3


@dataclass(frozen=True)
class Card:
    directions: list[tuple[int, int] | None]  # Corregido a tuple
    player: str

    @classmethod
    def create(cls, player: str):
        d = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dirs = [random.choice((d[i], None)) for i in range(4)]
        return cls(dirs, player)

    def to_dict(self):
        return asdict(self)


@dataclass
class Slot:
    type: SlotType
    card: Card | None = None

    def to_dict(self) -> dict:
        kwargs = asdict(self)
        kwargs["card"] = self.card.to_dict() if self.card else None
        return kwargs


@dataclass
class TurnReq:
    card: Card
    matrix: Matrix
    x: int
    y: int
    vx: int
    vy: int
    is_pushed: bool = False

    def get_next_pos(self) -> tuple[int, int]:  # Corregido a tuple
        return (self.x + self.vx, self.y + self.vy)

    def get_prev_pos(self) -> tuple[int, int]:  # Corregido a tuple
        return (self.x - self.vx, self.y - self.vy)

    def to_dict(self) -> dict:
        kwargs = asdict(self)
        kwargs["card"] = self.card.to_dict()
        kwargs["matrix"] = [[col.to_dict() for col in row] for row in self.matrix]
        return kwargs

    @classmethod
    def create(cls, **kwargs):
        if kwargs.get("card"):
            kwargs["card"] = Card(**kwargs["card"])
        new_matrix = []
        for row in kwargs["matrix"]:
            new_row = []
            for col in row:
                s_card = Card(**col["card"]) if col.get("card") else None
                new_row.append(Slot(type=SlotType(col["type"]), card=s_card))
            new_matrix.append(new_row)
        kwargs["matrix"] = new_matrix
        return cls(**kwargs)


@dataclass(frozen=True, kw_only=True)
class MixIn:
    matrix: Matrix
    message: str
    turn: bool = True

    @classmethod
    def _serialize_matrix(cls, matrix):  # Corregido self -> cls y self.matrix -> matrix
        return [
            [
                Slot(
                    type=SlotType(col["type"]),
                    card=Card(**col["card"]) if col.get("card") else None,
                )
                for col in row
            ]
            for row in matrix
        ]


@dataclass(frozen=True, kw_only=True)
class Hand(MixIn):
    hand: list[Card]
    rhand: list[Card]

    def to_dict(self) -> dict:
        return {
            "hand": [c.to_dict() for c in self.hand],
            "rhand": [c.to_dict() for c in self.rhand],
            "matrix": [[col.to_dict() for col in row] for row in self.matrix],
            "turn": self.turn,
            "message": self.message,
        }

    @classmethod
    def create(cls, **kwargs):
        for h in ("hand", "rhand"):
            kwargs[h] = [Card(**c) for c in kwargs.get(h, [])]
        kwargs["matrix"] = cls._serialize_matrix(kwargs["matrix"])  # Corregido "matrix"
        return cls(**kwargs)


@dataclass(frozen=True, kw_only=True)
class TurnRes(MixIn):
    newcard: Card
    precard: Card

    def to_dict(self) -> dict:
        return {
            "newcard": self.newcard.to_dict(),
            "matrix": [[col.to_dict() for col in row] for row in self.matrix],
            "turn": self.turn,
            "message": self.message,
            "precard": self.precard.to_dict(),
        }

    @classmethod
    def create(cls, **kwargs):
        kwargs["newcard"] = Card(**kwargs["newcard"])
        kwargs["precard"] = Card(**kwargs["precard"])
        kwargs["matrix"] = cls._serialize_matrix(kwargs["matrix"])  # Corregido "matrix"
        return cls(**kwargs)
