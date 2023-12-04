from core.database import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BIGINT, ForeignKey, Text, String, ARRAY, Integer
from sqlalchemy.ext.mutable import MutableList


class SupportTicketMessageAssociation(Base):
    __tablename__ = 'support_tickets_messages'  # noqa

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    support_ticket_id: Mapped[int] = mapped_column(
        ForeignKey('support_tickets.id', ondelete='CASCADE')
    )
    ticket_message_id: Mapped[int] = mapped_column(
        ForeignKey('ticket_messages.id', ondelete='CASCADE')
    )


class User(Base):
    __tablename__ = 'users'  # noqa

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False, unique=True)


class TicketMessages(Base):
    __tablename__ = 'ticket_messages'  # noqa

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=True)
    sender_username: Mapped[str] = mapped_column(String(120), nullable=True)


class SupportTicket(Base):
    __tablename__ = 'support_tickets'  # noqa

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    admin_id: Mapped[int] = mapped_column(BIGINT, nullable=True)
    token: Mapped[str] = mapped_column(unique=True)
    closed: Mapped[bool] = mapped_column(default=False)
    close_requests: Mapped[int] = mapped_column(default=0)
    close_requests_ids = mapped_column(MutableList.as_mutable(ARRAY(item_type=String)), default=[])
    messages: Mapped[list[TicketMessages]] = relationship(
        secondary='support_tickets_messages',
        lazy='selectin'
    )
    user_username: Mapped[str] = mapped_column(String(100), nullable=True)
    admin_username: Mapped[str] = mapped_column(String(100), nullable=True)

    panel: Mapped[str] = mapped_column(String(100), nullable=True)
    link: Mapped[str] = mapped_column(nullable=True)
    login: Mapped[str] = mapped_column(nullable=True)
    password: Mapped[str] = mapped_column(nullable=True)
    steam_id: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f'Ticket for user: {self.user_id}'

    def __str__(self):
        return self.__repr__()


class AllowedUser(Base):
    __tablename__ = 'allowed_users'  # noqa

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
