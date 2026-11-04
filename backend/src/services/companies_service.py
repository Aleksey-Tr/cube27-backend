from fastapi import HTTPException, status

from database import get_session
from orm.company_orm import CompanyORM
from orm.user_orm import UserORM
from repositories.companies_repo import CompaniesRepository
from roles import UserRole
from schemas.company_schemas import CompanyCreate, CompanyUpdate


class CompaniesService:
    """Сервис управления компаниями-арендаторами."""

    @classmethod
    async def get_all(cls, search: str | None = None) -> list[CompanyORM]:
        async with get_session() as session:
            repo = CompaniesRepository(session)
            return await repo.get_all(search=search)

    @classmethod
    async def get_by_id(
        cls, current_user: UserORM, company_id: int
    ) -> CompanyORM:
        user_role = current_user.role.lower() if current_user.role else ""

        # Доступ: owner, admin, lease_manager либо сама компания.
        allowed_roles = {
            UserRole.OWNER.value,
            UserRole.ADMIN.value,
            UserRole.LEASE_MANAGER.value,
        }
        if user_role not in allowed_roles and current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра карточки данной компании",
            )

        async with get_session() as session:
            repo = CompaniesRepository(session)
            company = await repo.get_by_id_with_details(company_id)
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Компания с ID {company_id} не найдена",
                )
            return company

    @classmethod
    async def create(cls, data: CompanyCreate) -> CompanyORM:
        async with get_session() as session:
            repo = CompaniesRepository(session)
            existing = await repo.get_by_inn(data.inn)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Компания с ИНН {data.inn} уже существует (ID: {existing.id})",
                )
            return await repo.create(
                name=data.name,
                inn=data.inn,
                address=data.address,
            )

    @classmethod
    async def update(
        cls, company_id: int, data: CompanyUpdate
    ) -> CompanyORM:
        async with get_session() as session:
            repo = CompaniesRepository(session)
            company = await repo.get_by_id(company_id)
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Компания с ID {company_id} не найдена",
                )

            # Если меняется ИНН — проверяем уникальность
            if data.inn and data.inn.strip() != company.inn:
                existing = await repo.get_by_inn(data.inn)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Компания с ИНН {data.inn} уже существует",
                    )

            return await repo.update(
                company=company,
                name=data.name,
                inn=data.inn,
                address=data.address,
            )

    @classmethod
    async def delete(cls, company_id: int) -> None:
        async with get_session() as session:
            repo = CompaniesRepository(session)
            company = await repo.get_by_id(company_id)
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Компания с ID {company_id} не найдена",
                )
            await repo.delete(company)
