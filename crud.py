from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from datetime import datetime, timedelta
import random
import string

from sqlalchemy.orm import Session
from sqlalchemy import text

def extract_registration_number(email: str) -> str:
    # Assuming the email format is "AG/16/001@domain.com"
    reg_number = email.split('@')[0]
    return reg_number


def get_class_tables_for_student(db: Session, reg_number: str):
    # Get class_id for the student from student_class_mapping
    class_ids = db.execute(text(f"""
    SELECT class_id FROM student_class_mapping WHERE reg_number = :reg_number
    """), {'reg_number': reg_number}).fetchall()

    # If no class_id found, return an empty list
    if not class_ids:
        return []

    # Get corresponding unique_class_names from meta_class_data
    class_tables = []
    for class_id in class_ids:
        result = db.execute(text(f"""
        SELECT unique_class_name FROM meta_class_data WHERE class_id = :class_id
        """), {'class_id': class_id[0]}).fetchone()
        
        if result:
            class_tables.append(result['unique_class_name'])

    return class_tables


def get_attendance_data(db: Session, reg_number: str, class_tables: list):
    attendance_data = []

    for class_table in class_tables:
        result = db.execute(text(f"""
        SELECT present_days AS pr, absent_days AS ab
        FROM {class_table}
        WHERE reg_number = :reg_number
        """), {'reg_number': reg_number}).fetchone()

        if result:
            attendance_data.append({
                "class_table": class_table,
                "pr": result['pr'],
                "ab": result['ab']
            })

    return attendance_data


def generate_unique_class_name(class_label: str):
    # Generate a random string to append to the class name
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    unique_class_name = f"{class_label.lower().replace(' ', '_')}_{random_str}"
    return unique_class_name

# Function to create or update the class table
def create_or_update_class(db: Session, class_label: str):
    # Generate a unique class name
    unique_class_name = generate_unique_class_name(class_label)

    # Store the class_label and unique_class_name in the meta_class_data table
    inspector = inspect(db.get_bind())
    
    if not inspector.has_table(unique_class_name):
        # Create a new table using the unique_class_name
        db.execute(text(f"""
        CREATE TABLE {unique_class_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reg_number VARCHAR(255) NOT NULL,
            present_days INT,
            absent_days INT
        )
        """))
    
    # Insert or update the metadata
    db.execute(text(f"""
    INSERT INTO meta_class_data (class_label, unique_class_name, last_updated)
    VALUES (:class_label, :unique_class_name, NOW())
    ON DUPLICATE KEY UPDATE last_updated = NOW()
    """), {'class_label': class_label, 'unique_class_name': unique_class_name})

    return unique_class_name


# Function to insert attendance data into the class table
def insert_attendance_data(db: Session, class_table_name: str, reg_number: str, present_days: int, absent_days: int):
    db.execute(text(f"""
    INSERT INTO {class_table_name} (reg_number, present_days, absent_days)
    VALUES (:reg_number, :present_days, :absent_days)
    """), {'reg_number': reg_number, 'present_days': present_days, 'absent_days': absent_days})

def update_student_class_mapping(db: Session, reg_number: str, unique_class_name: str):
    # Fetch the class_id based on the unique_class_name
    result = db.execute(text(f"""
    SELECT class_id FROM meta_class_data WHERE unique_class_name = :unique_class_name
    """), {'unique_class_name': unique_class_name}).fetchone()

    if result:
        class_id = result['class_id']

        # Check if the student-class mapping already exists
        mapping_result = db.execute(text(f"""
        SELECT * FROM student_class_mapping WHERE reg_number = :reg_number AND class_id = :class_id
        """), {'reg_number': reg_number, 'class_id': class_id}).fetchone()

        # If it doesn't exist, insert a new mapping
        if not mapping_result:
            db.execute(text(f"""
            INSERT INTO student_class_mapping (reg_number, class_id, added_date)
            VALUES (:reg_number, :class_id, NOW())
            """), {'reg_number': reg_number, 'class_id': class_id})

# Function to update the meta class data table
def update_meta_class_data(db: Session, class_id: str):
    db.execute(text(f"""
    INSERT INTO meta_class_data (class_id, last_updated)
    VALUES (:class_id, NOW())
    ON DUPLICATE KEY UPDATE last_updated = NOW()
    """), {'class_id': class_id})

# Function to clean up class tables older than 1 year
def cleanup_old_class_data(db: Session):
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    old_classes = db.execute(text(f"""
    SELECT class_id FROM meta_class_data WHERE last_updated < :one_year_ago
    """), {'one_year_ago': one_year_ago}).fetchall()

    for class_row in old_classes:
        class_id = class_row['class_id']
        db.execute(text(f"DROP TABLE IF EXISTS {class_id}"))
        db.execute(text(f"DELETE FROM meta_class_data WHERE class_id = :class_id"), {'class_id': class_id})

# Function to clean up student_class_mapping records older than 1 year
def cleanup_old_student_mappings(db: Session):
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    db.execute(text(f"""
    DELETE FROM student_class_mapping WHERE added_date < :one_year_ago
    """), {'one_year_ago': one_year_ago})



