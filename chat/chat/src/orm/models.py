from __future__ import annotations
import bcrypt
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin, relationship
from sqlalchemy import func, ForeignKey, select, insert, String
from .main import Base


@declarative_mixin
class Timestamp:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


@declarative_mixin
class Id:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class UserMessage(Base):
    __tablename__ = "user_messages"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True
    )
    user: Mapped["User"] = relationship(back_populates="user_messages_association")
    message: Mapped["Message"] = relationship(
        back_populates="user_messages_association"
    )


class User(Base, Id, Timestamp):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    authored_messages: Mapped[List["Message"]] = relationship(back_populates="author")
    user_messages_association: Mapped[List["UserMessage"]] = relationship(
        back_populates="user"
    )

    def __init__(self, name: str, password: str):
        self.name = name
        self.password = password

    @property
    def password(self):
        raise ValueError("Password is write-only")

    @password.setter
    def password(self, value: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(value.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, value: str) -> bool:
        return bcrypt.checkpw(value.encode("utf-8"), self.password_hash.encode("utf-8"))

    @classmethod
    def auth(cls, session, username: str, password: str) -> Optional[User]:
        stmt = select(cls).where(cls.name == username)
        user = session.scalars(stmt).first()
        if user and user.check_password(password):
            return user
        elif not user:
            new_user = cls(name=username, password=password)
            session.add(new_user)
            session.flush()
            return new_user
        return None


class Message(Base, Id, Timestamp):
    __tablename__ = "messages"
    content: Mapped[str] = mapped_column(String(255))
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    author: Mapped["User"] = relationship(back_populates="authored_messages")
    user_messages_association: Mapped[List["UserMessage"]] = relationship(
        back_populates="message"
    )

    @classmethod
    def send(
        cls, session, content: str, author_id: int, receivers: list[str] = []
    ) -> Message:
        new_msg = cls(content=content, author_id=author_id)
        session.add(new_msg)
        session.flush()

        if len(receivers) < 1:
            user_ids = session.scalars(select(User.id)).all()
            values = [{"user_id": uid, "message_id": new_msg.id} for uid in user_ids]
        else:
            stmt = select(User.id).where(User.name.in_(receivers))
            receivers_ids = session.scalars(stmt).all()
            values = [
                {"user_id": rid, "message_id": new_msg.id} for rid in receivers_ids
            ]

        if values:
            session.execute(insert(UserMessage), values)
        return new_msg

    @classmethod
    def get_from_user(cls, session, user_id: int) -> list[Message]:
        stmt = select(cls).join(UserMessage).where(UserMessage.user_id == user_id)
        messages: list[Message] = session.scalars(stmt).all()
        return messages

    @property
    def fmt_message(self) -> str:
        author_name = self.author.name if self.author else "Usuario Eliminado"
        timestamp = self.created_at.strftime("%H:%M - %d/%m/%Y")
        return f"{author_name} ({timestamp}):\n{self.content}"
