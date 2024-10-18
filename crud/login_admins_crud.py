from sqlalchemy.orm import Session
from models.models import Admin

def get_admin_by_email(db: Session, email: str):
    return db.query(Admin).filter(Admin.email == email).first()

def create_admin(db: Session, admin):
    new_admin = Admin(
        email=admin.email,
        dep_name=admin.dep_name,
        is_super_admin=admin.is_super_admin
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin
