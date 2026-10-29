from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orm.base import Base


class RoleORM(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["UserORM"]] = relationship(back_populates="role")
