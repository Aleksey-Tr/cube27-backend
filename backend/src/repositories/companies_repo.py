from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from orm.company_orm import CompanyORM
from orm.contract_orm import ContractORM
from orm.user_orm import UserORM


class CompaniesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, search: str | None = None) -> list[CompanyORM]:
        stmt = select(CompanyORM).order_by(CompanyORM.id.desc())
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    CompanyORM.name.ilike(pattern),
                    CompanyORM.inn.ilike(pattern),
                )
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, company_id: int) -> CompanyORM | None:
        return await self.session.get(CompanyORM, company_id)

    async def get_by_id_with_details(self, company_id: int) -> CompanyORM | None:
        stmt = (
            select(CompanyORM)
            .options(
                selectinload(CompanyORM.users).selectinload(UserORM.role),
                selectinload(CompanyORM.contracts).selectinload(ContractORM.premises),
            )
            .where(CompanyORM.id == company_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_inn(self, inn: str) -> CompanyORM | None:
        stmt = select(CompanyORM).where(CompanyORM.inn == inn.strip())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(
        self, name: str, inn: str, address: str | None = None
    ) -> CompanyORM:
        company = CompanyORM(
            name=name.strip(),
            inn=inn.strip(),
            address=address.strip() if address else None,
        )
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def get_or_create(
        self, name: str, inn: str, address: str | None = None
    ) -> CompanyORM:
        existing = await self.get_by_inn(inn)
        if existing:
            return existing
        return await self.create(name=name, inn=inn, address=address)

    async def update(
        self,
        company: CompanyORM,
        name: str | None = None,
        inn: str | None = None,
        address: str | None = None,
    ) -> CompanyORM:
        if name is not None:
            company.name = name.strip()
        if inn is not None:
            company.inn = inn.strip()
        if address is not None:
            company.address = address.strip() if address else None

        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def delete(self, company: CompanyORM) -> None:
        await self.session.delete(company)
        await self.session.commit()
