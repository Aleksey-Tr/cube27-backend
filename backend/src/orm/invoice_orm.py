from datetime import date
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class InvoiceORM(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int | None] = mapped_column(
        ForeignKey("contracts.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="Unpaid", server_default="Unpaid", nullable=False
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)

    contract: Mapped["ContractORM | None"] = relationship(back_populates="invoices")
