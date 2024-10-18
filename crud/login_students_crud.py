from sqlalchemy.orm import Session
from sqlalchemy import text


# Extract registration number from email
def extract_registration_number(email: str) -> str:
    reg_number = email.split('@')[0]
    return reg_number


# Fetch class tables for the student
def get_class_tables_for_student(db: Session, reg_number: str):
    class_ids = db.execute(text("""
        SELECT class_id FROM student_class_mapping WHERE reg_number = :reg_number
    """), {'reg_number': reg_number}).fetchall()
    if not class_ids:
        return []
    class_tables = []
    for class_id in class_ids:
        result = db.execute(text("""
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


