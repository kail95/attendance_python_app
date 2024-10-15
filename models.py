from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class StudentClassMapping(Base):
    __tablename__ = "student_class_mapping"

    id = Column(Integer, primary_key=True, index=True)
    reg_number = Column(String(255), nullable=False)
    class_id = Column(String(255), nullable=False)
    added_date = Column(TIMESTAMP, default=datetime.utcnow)

class MetaClassData(Base):
    __tablename__ = "meta_class_data"

    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_label = Column(String(255))  # Original provided name
    unique_class_name = Column(String(255), unique=True)  # Generated unique name
    last_updated = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)