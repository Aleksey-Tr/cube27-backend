# Файл с функциями, которые могут быть использованы в качестве триггеров или процедур в базе данных

from sqlalchemy.orm import Session
from fastapi import HTTPException

def activate_contract_and_occupy_premises(db: Session, contract_id: int): # автоматическая смена статуса договора на Active и перевод всех помещений по этому договору в Occupied
    contract = db.execute("SELECT * FROM contracts WHERE id = :id", {"id": contract_id}).fetchone()
    if not contract:
        raise HTTPException(status_code=404, detail="Договор не найден")
    
    db.execute("UPDATE contracts SET status = 'Active' WHERE id = :id", {"id": contract_id})

    db.execute("""
        UPDATE premises 
        SET status = 'Occupied' 
        WHERE id IN (SELECT premise_id FROM contract_premises WHERE contract_id = :id)
    """, {"id": contract_id})
    
    db.commit()

def validate_meter_reading(db: Session, meter_id: int, new_value: float) -> bool: # функция для проверки, что новое показание счетчика не меньше предыдущего
    last_reading = db.execute("""
        SELECT value FROM meter_readings 
        WHERE meter_id = :meter_id 
        ORDER BY reading_date DESC LIMIT 1
    """, {"meter_id": meter_id}).fetchone()
    
    if last_reading and new_value < float(last_reading.value):
        raise HTTPException(
            status_code=400, 
            detail="Новое показание не может быть меньше предыдущего!"
        )
    return True

def onboard_tenant_transaction(db: Session, company_data: dict, admin_data: dict, contract_data: dict): # функция для добавления нового арендатора, его администратора и договора в рамках одной транзакции
    company_query = """
        INSERT INTO companies (name, inn, address) 
        VALUES (:name, :inn, :address) RETURNING id;
    """
    company_id = db.execute(company_query, company_data).fetchone().id

    admin_data["company_id"] = company_id
    admin_query = """
        INSERT INTO users (company_id, role_id, first_name, last_name, email, phone, password_hash, is_active)
        VALUES (:company_id, (SELECT id FROM roles WHERE name = 'TenantAdmin'), :first_name, :last_name, :email, :phone, :password_hash, true)
        RETURNING id;
    """
    db.execute(admin_query, admin_data)

    contract_data["company_id"] = company_id
    
    db.commit()
    return {"status": "success", "company_id": company_id}


def generate_monthly_rent_invoices(db: Session): # функция для генерации ежемесячных счетов арендаторам с активными договорами
    active_contracts = db.execute("SELECT id, company_id FROM contracts WHERE status = 'Active'").fetchall()
    
    for contract in active_contracts:
        db.execute("""
            INSERT INTO invoices (contract_id, invoice_type, amount, status, due_date, issued_date)
            VALUES (:contract_id, 'Rent', 50000.00, 'Unpaid', CURRENT_DATE + INTERVAL '10 days', CURRENT_DATE)
        """, {"contract_id": contract.id})
    
    db.commit()


def route_ticket_category(category: str) -> str: # функция для маршрутизации тикетов по категориям к соответствующим ролям
    routing_map = {
        "Электричество": "ChiefPowerEngineer",
        "Водоснабжение и отопление": "HeadOfEMO",
        "Строительство": "ChiefEngineer",
        "Бухгалтерия": "Accountant",
        "Аренда": "LeaseManager"
    }
    return routing_map.get(category, "SuperAdmin")