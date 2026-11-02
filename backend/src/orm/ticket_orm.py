from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class TicketORM(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM(
            "Open",
            "InProgress",
            "PendingTenant",
            "Closed",
            "Cancelled",
            name="ticket_status",
            create_type=False,
        ),
        default="Open",
        server_default="Open",
        nullable=False,
    )
    bitrix_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    author: Mapped["UserORM | None"] = relationship(back_populates="tickets")
