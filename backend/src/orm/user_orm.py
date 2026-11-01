from sqlalchemy import Boolean, ForeignKey, Integer, String, false
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    role: Mapped[str] = mapped_column(
        ENUM(
            "owner",
            "admin",
            "lease_manager",
            "chief_power_engineer",
            "chief_emo",
            "chief_engineer",
            "chief_accountant",
            "company",
            name="user_role",
            create_type=False,
        ),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    company: Mapped["CompanyORM | None"] = relationship(back_populates="users")
    meter_readings: Mapped[list["MeterReadingORM"]] = relationship(back_populates="user")
    tickets: Mapped[list["TicketORM"]] = relationship(back_populates="author")
