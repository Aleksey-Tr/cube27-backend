from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class MeterReadingORM(Base):
    __tablename__ = "meter_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meter_id: Mapped[int] = mapped_column(ForeignKey("meters.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reading_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(
        ENUM(
            "Pending",
            "Approved",
            "Rejected",
            name="meter_reading_status",
            create_type=False,
        ),
        default="Pending",
        nullable=False,
    )

    meter: Mapped["MeterORM"] = relationship(back_populates="readings")
    user: Mapped["UserORM"] = relationship(back_populates="meter_readings")
