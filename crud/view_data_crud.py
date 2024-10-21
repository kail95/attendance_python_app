from sqlalchemy.orm import Session
from sqlalchemy import text
from models.models import MetaClassData

# Get classes by department
def get_classes_by_department(db: Session, dep_name: int):
    return db.query(MetaClassData).filter(MetaClassData.dep_name == dep_name).all()

# Get table data
def get_table_data(db: Session, table_name: str):
    return db.execute(text(f"SELECT * FROM {table_name}")).fetchall()