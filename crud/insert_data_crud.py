from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import random
import string
import re

EMAIL_TO_DEP_MAP = {
    'attendance.ab@agri.pdn.ac.lk': (1, 'biol_'),
    'attendance.ae@agri.pdn.ac.lk': (2, 'engi_'),
    'attendance.as@agri.pdn.ac.lk': (3, 'anim_'),
    'attendance.eb@agri.pdn.ac.lk': (4, 'econ_'),
    'attendance.ex@agri.pdn.ac.lk': (5, 'exte_'),
    'attendance.cs@agri.pdn.ac.lk': (6, 'crop_'),
    'attendance.ss@agri.pdn.ac.lk': (7, 'soil_'),
    'attendance.fst@agri.pdn.ac.lk': (8, 'food_'),
    'isuruk@agri.pdn.ac.lk': (99, 'test_')  # For testing
}


# Function to generate a unique class table name based on email and random string
def generate_unique_class_name(class_label: str, email: str):
    dep_data = EMAIL_TO_DEP_MAP.get(email, (99, 'test_'))
    prefix = dep_data[1]
    cleaned_class_label = re.sub(r'[^a-zA-Z0-9_]', '_', class_label.lower()).strip('_')
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    unique_class_name = f"{prefix}{cleaned_class_label}_{random_str}"
    if len(unique_class_name) > 64:
        raise ValueError("Generated class table name exceeds MySQL's 64 character limit")
    return unique_class_name, dep_data[0]


# Function to create or update the class table and metadata
def create_or_update_class(db: Session, class_label: str, file_id: str, email: str):
    result = db.execute(text("""
        SELECT class_table_name FROM meta_class_data WHERE class_file_id = :file_id
    """), {'file_id': file_id}).fetchone()
    if result:
        class_table_name = result[0]
    else:
        class_table_name, dep_name = generate_unique_class_name(class_label, email)
        inspector = inspect(db.get_bind())
        if not inspector.has_table(class_table_name):
            db.execute(text(f"""
                CREATE TABLE {class_table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    reg_number VARCHAR(255) NOT NULL,
                    student_name VARCHAR(255),
                    present_days INT,
                    absent_days INT
                )
            """))
        db.execute(text("""
            INSERT INTO meta_class_data (class_label, class_table_name, class_file_id, dep_name, last_updated)
            VALUES (:class_label, :class_table_name, :file_id, :dep_name, NOW())
        """), {'class_label': class_label, 'class_table_name': class_table_name, 'file_id': file_id, 'dep_name': dep_name})
    return class_table_name


# Function to insert attendance data into the class table
def insert_attendance_data(db: Session, class_table_name: str, reg_number: str, student_name: str, present_days: int, absent_days: int):
    if isinstance(class_table_name, str) and class_table_name.isidentifier():
        db.execute(text(f"""
            INSERT INTO {class_table_name} (reg_number, student_name, present_days, absent_days)
            VALUES (:reg_number, :student_name, :present_days, :absent_days)
        """), {'reg_number': reg_number, 'student_name': student_name, 'present_days': present_days, 'absent_days': absent_days})
    else:
        raise ValueError("Invalid table name")


# Function to truncate class table (before inserting new data)
def truncate_attendance_data(db: Session, class_table_name: str):
    if isinstance(class_table_name, str) and class_table_name.isidentifier():
        db.execute(text(f"TRUNCATE TABLE {class_table_name}"))
    else:
        raise ValueError(f"Invalid table name: {class_table_name}")


# Function to update student-class mapping table
def update_student_class_mapping(db: Session, reg_number: str, class_table_name: str):
    result = db.execute(text("""
        SELECT class_id FROM meta_class_data WHERE class_table_name = :class_table_name
    """), {'class_table_name': class_table_name}).fetchone()
    if result:
        class_id = result[0]
        mapping_result = db.execute(text("""
            SELECT * FROM student_class_mapping WHERE reg_number = :reg_number AND class_id = :class_id
        """), {'reg_number': reg_number, 'class_id': class_id}).fetchone()
        if not mapping_result:
            db.execute(text("""
                INSERT INTO student_class_mapping (reg_number, class_id, added_date)
                VALUES (:reg_number, :class_id, NOW())
            """), {'reg_number': reg_number, 'class_id': class_id})


# Update last_updated in meta_class_data
def update_meta_class_data(db: Session, class_file_id: str):
    db.execute(text(f"""
    UPDATE meta_class_data
    SET last_updated = NOW()
    WHERE class_file_id = :class_file_id
    """), {'class_file_id': class_file_id})