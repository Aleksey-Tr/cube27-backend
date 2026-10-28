from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class ContractORM(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    contract_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM(
            "Draft",
            "Active",
            "Expired",
            "Terminated",
            name="contract_status",
            create_type=False,
        ),
        default="Active",
        server_default="Active",
        nullable=False,
    )

    company: Mapped["CompanyORM | None"] = relationship(back_populates="contracts")
    premises: Mapped[list["PremiseORM"]] = relationship(secondary="contract_premises", back_populates="contracts")
    invoices: Mapped[list["InvoiceORM"]] = relationship(back_populates="contract")
