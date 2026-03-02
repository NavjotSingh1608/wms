"""
Seed roles and a test user. Run after alembic upgrade head.
Usage: python -m app.scripts.seed_db
"""
import json
import sys
from pathlib import Path

# Ensure app is on path when run as __main__
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password

# Permissions per spec (subset for demo)
WAREHOUSE_EXEC_PERMISSIONS = [
    "grn:create", "label:print", "material:update_rack", "material:issue",
    "retest:initiate", "grade:transfer_request", "fg:receive", "fg:dispatch",
    "stock:view", "reports:view",
]


def seed() -> None:
    engine = create_engine(settings.SYNC_DATABASE_URL)
    with Session(engine) as session:
        # Seed roles if missing
        (role_count,) = session.execute(text("SELECT COUNT(*) FROM roles")).one()
        if role_count == 0:
            roles = [
                ("WAREHOUSE_EXEC", WAREHOUSE_EXEC_PERMISSIONS),
                ("WAREHOUSE_HEAD", WAREHOUSE_EXEC_PERMISSIONS + ["grn:revise", "label:reprint", "audit:view"]),
                ("QC_EXEC", ["qc:add_ar_number", "qc:sampling", "qc:set_under_test", "stock:view", "reports:view"]),
                ("QC_HEAD", ["qc:add_ar_number", "qc:sampling", "qc:set_under_test", "qc:approve", "qc:reject", "qc:retest_date", "grade:change", "stock:view", "reports:view", "audit:view"]),
                ("PRODUCTION", ["fg:send_to_warehouse", "fg:shipper_label", "stock:view", "reports:view"]),
                ("QA_EXEC", ["fg:qa_approve", "stock:view", "reports:view"]),
                ("QA_HEAD", ["fg:qa_approve", "fg:revise_entry", "stock:view", "reports:view", "audit:view"]),
                ("PURCHASE", ["stock:view", "reports:view"]),
            ]
            for name, perms in roles:
                session.execute(
                    text("INSERT INTO roles (id, name, permissions) VALUES (gen_random_uuid(), :name, CAST(:perms AS jsonb))"),
                    {"name": name, "perms": json.dumps(perms)},
                )
            session.commit()
            print(f"Seeded {len(roles)} roles.")
        else:
            print(f"Roles already exist ({role_count}). Skipping roles.")

        # Seed test user if missing
        (user_count,) = session.execute(text("SELECT COUNT(*) FROM users WHERE email = 'warehouse@test.com'")).one()
        if user_count == 0:
            (role_id,) = session.execute(text("SELECT id FROM roles WHERE name = 'WAREHOUSE_EXEC' LIMIT 1")).one()
            pw_hash = hash_password("Test@1234")
            session.execute(
                text(
                    """INSERT INTO users (id, name, email, password_hash, role_id, department)
                       VALUES (gen_random_uuid(), 'Test Warehouse', 'warehouse@test.com', :pw, :role_id, 'Warehouse')"""
                ),
                {"pw": pw_hash, "role_id": str(role_id)},
            )
            session.commit()
            print("Created user: warehouse@test.com / Test@1234")
        else:
            print("Test user already exists.")

        # Seed materials if missing
        (mat_count,) = session.execute(text("SELECT COUNT(*) FROM materials")).one()
        if mat_count == 0:
            materials = [
                ("PARA-IP-001", "Paracetamol IP", "IP", "kg"),
                ("PARA-BP-001", "Paracetamol BP", "BP", "kg"),
                ("AMOX-IP-001", "Amoxicillin IP", "IP", "kg"),
                ("VIT-C-001", "Vitamin C", "USP", "kg"),
            ]
            for item_code, item_name, grade, uom in materials:
                session.execute(
                    text(
                        """INSERT INTO materials (id, item_code, item_name, grade, unit_of_measure)
                           VALUES (gen_random_uuid(), :item_code, :item_name, :grade, :uom)"""
                    ),
                    {"item_code": item_code, "item_name": item_name, "grade": grade, "uom": uom},
                )
            session.commit()
            print(f"Seeded {len(materials)} materials.")
        else:
            print(f"Materials already exist ({mat_count}). Skipping materials.")

    print("Seed complete.")


if __name__ == "__main__":
    seed()
