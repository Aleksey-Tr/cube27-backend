from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class ContractPremiseORM(Base):
    __tablename__ = "contract_premises"

    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), primary_key=True)
    premise_id: Mapped[int] = mapped_column(ForeignKey("premises.id"), primary_key=True)

