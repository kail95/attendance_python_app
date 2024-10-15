from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import ClassAttendanceData
from crud import create_or_update_class, insert_attendance_data, update_student_class_mapping, update_meta_class_data

router = APIRouter()

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from crud import extract_registration_number, get_class_tables_for_student, get_attendance_data
from database import get_db

router = APIRouter()

from fastapi import Request

def get_current_user_email(request: Request):
    # For now, just return a hardcoded email for testing
    return "AG/16/001@domain.com"

@router.get("/get_attendance/")
def get_attendance(db: Session = Depends(get_db), email: str = Depends(get_current_user_email)):
    # Extract registration number from the email
    reg_number = extract_registration_number(email)

    # Get class tables for the student
    class_tables = get_class_tables_for_student(db, reg_number)

    if not class_tables:
        return {"message": "No classes found for this student."}

    # Get attendance data for each class
    attendance_data = get_attendance_data(db, reg_number, class_tables)

    return {
        "reg_number": reg_number,
        "attendance": attendance_data
    }


@router.post("/process_attendance/")
def process_attendance(data: ClassAttendanceData, db: Session = Depends(get_db)):
    # Create or update the class using the label
    unique_class_name = create_or_update_class(db, data.fileName)

    for record in data.data:
        reg_number = record.reg
        present_days = record.pr
        absent_days = record.ab

        # Insert attendance data into the unique class table
        insert_attendance_data(db, unique_class_name, reg_number, present_days, absent_days)

        # Update student_class_mapping with the correct class_id
        update_student_class_mapping(db, reg_number, unique_class_name)

    # Update the meta_class_data table with the last update time
    update_meta_class_data(db, unique_class_name)

    return {"message": "Attendance data processed successfully."}
