import enum
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class User:
    id: int
    name: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def create(cls, data: dict) -> User:
        return cls(**data)


class Cmd(enum.IntEnum):
    AUTH = 1
    MSG = 2
    ERR = 0
    HELP = 3
    EXIT = 4
