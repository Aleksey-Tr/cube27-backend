from decimal import Decimal
from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class PremiseORM(Base):
    __tablename__ = "premises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    room_number: Mapped[str] = mapped_column(String(50), nullable=False)
    area: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="Free", server_default="Free", nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    contracts: Mapped[list["ContractORM"]] = relationship(
        secondary="contract_premises", back_populates="premises"
    )
    contract_associations: Mapped[list["ContractPremiseORM"]] = relationship(
        back_populates="premise"
    )
    meters: Mapped[list["MeterORM"]] = relationship(back_populates="premise")
