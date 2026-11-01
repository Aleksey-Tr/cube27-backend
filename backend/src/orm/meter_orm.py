from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class MeterORM(Base):
    __tablename__ = "meters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    premise_id: Mapped[int] = mapped_column(ForeignKey("premises.id"), nullable=False)
    meter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    premise: Mapped["PremiseORM"] = relationship(back_populates="meters")
    readings: Mapped[list["MeterReadingORM"]] = relationship(back_populates="meter")
