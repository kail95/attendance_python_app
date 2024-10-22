from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

def get_assigned_classes(db: Session, reg_number: str):
    # Query to get class IDs where the student is assigned
    class_ids = db.execute(
        text("SELECT class_id FROM student_class_mapping WHERE reg_number = :reg_number"),
        {"reg_number": reg_number}
    ).fetchall()

    if not class_ids:
        raise HTTPException(status_code=404, detail="No classes found for the student")

    return [class_id[0] for class_id in class_ids]  # Extract class IDs


def get_class_table_names(db: Session, class_ids: list):
    # Query to get class table names using class IDs
    class_table_names = db.execute(
        text("SELECT class_table_name FROM meta_class_data WHERE class_id IN :class_ids"),
        {"class_ids": tuple(class_ids)}
    ).fetchall()

    if not class_table_names:
        raise HTTPException(status_code=404, detail="No class table names found")

    return [table[0] for table in class_table_names]  # Extract table names


def get_attendance_records(db: Session, class_table_names: list, reg_number: str):
    attendance_records = []

    for table_name in class_table_names:
        # Query each class table for the student's attendance records
        records = db.execute(
            text(f"SELECT * FROM {table_name} WHERE reg_number = :reg_number"),
            {"reg_number": reg_number}
        ).fetchall()
        
        attendance_records.extend(records)  # Add records to the list

    if not attendance_records:
        raise HTTPException(status_code=404, detail="No attendance records found")

    return attendance_records
