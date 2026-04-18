from database import SessionLocal
from models import Lead
import uuid


def seed():

    db = SessionLocal()

    try:
        existing = db.query(Lead).filter(Lead.email == "admin@mesanomega.com").first()

        if not existing:
            admin = Lead(
                id=str(uuid.uuid4()),
                nombre="MESAN Admin",
                email="admin@mesanomega.com",
                telefono="6861629643",
                score=100,
                clasificacion="BAJO",
                impacto_min=0,
                impacto_max=0,
                estatus="admin",
                fecha="2026-01-01"
            )
            db.add(admin)
            db.commit()
            print("Admin creado OK")
        else:
            print("Admin ya existe")

    except Exception as e:
        db.rollback()
        print(f"Error en seed: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
