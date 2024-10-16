from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from datetime import datetime, timedelta
import random
import string
import re

# Mapping for department based on email and prefixes
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

# Extract registration number from email
def extract_registration_number(email: str) -> str:
    # Assuming the email format is "AG/16/001@domain.com"
    reg_number = email.split('@')[0]
    return reg_number

# Fetch class tables for the student
def get_class_tables_for_student(db: Session, reg_number: str):
    # Get class_id for the student from student_class_mapping
    class_ids = db.execute(text(f"""
    SELECT class_id FROM student_class_mapping WHERE reg_number = :reg_number
    """), {'reg_number': reg_number}).fetchall()

    if not class_ids:
        return []

    # Get class_table names from meta_class_data based on class_id
    class_tables = []
    for class_id in class_ids:
        result = db.execute(text(f"""
        SELECT class_table_name FROM meta_class_data WHERE class_id = :class_id
        """), {'class_id': class_id[0]}).fetchone()
        
        if result:
            class_tables.append(result['class_table_name'])

    return class_tables

# Fetch attendance data for a student
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

def generate_unique_class_name(class_label: str, email: str):
    # Extract prefix from email
    dep_data = EMAIL_TO_DEP_MAP.get(email, (99, 'test_'))  # Default to 99 and 'test_' for unrecognized email
    prefix = dep_data[1]

    # Clean up class_label to ensure it's a valid identifier (remove spaces, special characters, etc.)
    cleaned_class_label = re.sub(r'[^a-zA-Z0-9_]', '_', class_label.lower()).strip('_')

    # Generate a random string to append to the class name
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Generate unique class name with prefix and cleaned class label
    unique_class_name = f"{prefix}{cleaned_class_label}_{random_str}"

    # Check if the table name length exceeds MySQL's maximum length of 64 characters
    if len(unique_class_name) > 64:
        raise ValueError("Generated class table name exceeds MySQL's 64 character limit")

    return unique_class_name, dep_data[0]


# Function to create or update the class table using fileId and dep_name
def create_or_update_class(db: Session, class_label: str, file_id: str, email: str):
    # Check if the class for this fileId already exists in meta_class_data
    result = db.execute(text(f"""
    SELECT class_table_name FROM meta_class_data WHERE class_file_id = :file_id
    """), {'file_id': file_id}).fetchone()

    if result:
        # If it exists, return the existing table name
        class_table_name = result[0]
    else:
        # Generate a new unique class table name using email and class label
        class_table_name, dep_name = generate_unique_class_name(class_label, email)

        # Create the new table if it doesn't exist
        inspector = inspect(db.get_bind())
        if not inspector.has_table(class_table_name):
            # Create the table using the unique class_table_name
            db.execute(text(f"""
            CREATE TABLE {class_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reg_number VARCHAR(255) NOT NULL,
                present_days INT,
                absent_days INT
            )
            """))

        # Insert the metadata for the new class
        db.execute(text(f"""
        INSERT INTO meta_class_data (class_label, class_table_name, class_file_id, dep_name, last_updated)
        VALUES (:class_label, :class_table_name, :file_id, :dep_name, NOW())
        """), {'class_label': class_label, 'class_table_name': class_table_name, 'file_id': file_id, 'dep_name': dep_name})

    return class_table_name


# Insert attendance data
def insert_attendance_data(db: Session, class_table_name: str, reg_number: str, present_days: int, absent_days: int):
    # Ensure the table name is properly formatted
    if isinstance(class_table_name, str) and class_table_name.isidentifier():
        db.execute(text(f"""
        INSERT INTO {class_table_name} (reg_number, present_days, absent_days)
        VALUES (:reg_number, :present_days, :absent_days)
        """), {'reg_number': reg_number, 'present_days': present_days, 'absent_days': absent_days})
    else:
        raise ValueError("Invalid table name")


def truncate_attendance_data(db: Session, class_table_name: str):
    # Log the table name to debug
    print(f"Truncating data from table: {class_table_name}")

    # Validate the table name
    if isinstance(class_table_name, str) and class_table_name.isidentifier():
        db.execute(text(f"TRUNCATE TABLE {class_table_name}"))
    else:
        raise ValueError(f"Invalid table name: {class_table_name}")


# Update student-class mapping table
def update_student_class_mapping(db: Session, reg_number: str, class_table_name: str):
    # Fetch the class_id from meta_class_data
    result = db.execute(text(f"""
    SELECT class_id FROM meta_class_data WHERE class_table_name = :class_table_name
    """), {'class_table_name': class_table_name}).fetchone()

    if result:
        class_id = result[0]

        # Check if the student-class mapping already exists
        mapping_result = db.execute(text(f"""
        SELECT * FROM student_class_mapping WHERE reg_number = :reg_number AND class_id = :class_id
        """), {'reg_number': reg_number, 'class_id': class_id}).fetchone()

        if not mapping_result:
            # Insert the mapping if it doesn't exist
            db.execute(text(f"""
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

# Clean up old class tables (older than 1 year)
def cleanup_old_class_data(db: Session):
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    old_classes = db.execute(text(f"""
    SELECT class_table_name FROM meta_class_data WHERE last_updated < :one_year_ago
    """), {'one_year_ago': one_year_ago}).fetchall()

    for class_row in old_classes:
        class_table_name = class_row['class_table_name']
        db.execute(text(f"DROP TABLE IF EXISTS {class_table_name}"))
        db.execute(text(f"DELETE FROM meta_class_data WHERE class_table_name = :class_table_name"), {'class_table_name': class_table_name})

# Clean up old student-class mappings (older than 1 year)
def cleanup_old_student_mappings(db: Session):
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    db.execute(text(f"""
    DELETE FROM student_class_mapping WHERE added_date < :one_year_ago
    """), {'one_year_ago': one_year_ago})
