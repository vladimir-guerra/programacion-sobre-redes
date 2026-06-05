from __future__ import annotations
import bcrypt
from datetime import datetime
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declarative_mixin,
    relationship,
    object_session,
)
from sqlalchemy import func, ForeignKey, select, event
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


class User(Base, Id, Timestamp):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column()

    @property
    def password(self):
        raise ValueError("Password is write-only")

    @password.setter
    def password(self, value: str):
        hash_value = value.encode("utf-8")
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(hash_value, salt).decode("utf-8")

    def check_password(self, value: str) -> bool:
        hash_value = value.encode("utf-8")
        hash_pw = self.password_hash.encode("utf-8")
        return bcrypt.checkpw(hash_value, hash_pw)

    @classmethod
    def auth(cls, session, username: str, password: str):
        stmt = select(cls).where(cls.name == username)
        user = session.scalars(stmt).first()
        if user and user.check_password(password):
            return user
        elif not user:
            new_user = cls(username, "pw")
            new_user.password = password
            session.add(new_user)
            return new_user
        return None

    members: Mapped[list["Member"]] = relationship("Member", back_populates="user")


class Forum(Base, Id, Timestamp):
    __tablename__ = "forums"
    name: Mapped[str] = mapped_column(unique=True)
    is_dm: Mapped[bool] = mapped_column(default=False)

    members: Mapped[list["Member"]] = relationship("Member", back_populates="forum")


class Member(Base, Id, Timestamp):
    __tablename__ = "members"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    forum_id: Mapped[int] = mapped_column(ForeignKey("forums.id", ondelete="CASCADE"))
    role: Mapped[int] = mapped_column(default=2)

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="member")
    forum: Mapped["Forum"] = relationship("Forum", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="members")


class Message(Base, Id, Timestamp):
    __tablename__ = "messages"
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL")
    )
    content: Mapped[str] = mapped_column()

    member: Mapped["Member"] = relationship("Member", back_populates="messages")


@event.listens_for(User, "before_insert")
def add_to_default(mapper, connection, target: User):
    session = object_session(target)
    if not session:
        return
    stmt = select(Forum).where(Forum.name == "DEFAULT")
    default_forum = session.scalars(stmt).first()
    if not default_forum:
        default_forum = Forum("DEFAULT")
        session.add(default_forum)
    new_member = Member(user=target, forum=default_forum)
    target.members.append(new_member)
