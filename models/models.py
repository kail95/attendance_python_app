from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class StudentClassMapping(Base):
    __tablename__ = "student_class_mapping"

    id = Column(Integer, primary_key=True, index=True)
    reg_number = Column(String(255), nullable=False)
    class_id = Column(Integer, nullable=False)
    added_date = Column(TIMESTAMP, default=datetime.utcnow)

class MetaClassData(Base):
    __tablename__ = "meta_class_data"

    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_label = Column(String(255))  # Original provided name
    class_table_name = Column(String(255), unique=True)  # Generated unique class table name
    class_file_id = Column(String(255), unique=True)  # File ID of the Google Sheet
    dep_name = Column(Integer)  # Department name as an integer (e.g., 1 for 'attendance.ab@agri.pdn.ac.lk')
    last_updated = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    dep_name = Column(Integer, nullable=True)  # Department association
    is_super_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)