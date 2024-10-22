from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.attendance_schemas import ClassAttendanceData
from crud.insert_data_crud import (
    create_or_update_class,
    insert_attendance_data,
    update_student_class_mapping,
    update_meta_class_data,
    truncate_attendance_data
)

router = APIRouter()

@router.post("/process_attendance/")
def process_attendance(data: ClassAttendanceData, db: Session = Depends(get_db)):
    try:
        # Generate or fetch the class table name
        class_table_name = create_or_update_class(db, data.fileName, data.fileId, data.ownerEmail)
        
        # Log the table name to debug
        print(f"Processing attendance for table: {class_table_name}")

        # Truncate the existing class table if it already exists
        truncate_attendance_data(db, class_table_name)

        # Insert attendance records
        for record in data.data:
            reg_number = record.reg
            student_name = record.name  # Extract student name
            present_days = record.pr
            absent_days = record.ab

            insert_attendance_data(db, class_table_name, reg_number, student_name, present_days, absent_days)
            update_student_class_mapping(db, reg_number, class_table_name)

        # Update meta_class_data
        update_meta_class_data(db, data.fileId)

        return {"message": "Attendance data processed successfully."}
    
    except Exception as e:
        # Catch other unexpected exceptions and return a 500 error with detailed logs
        raise HTTPException(status_code=500, detail=f"An error occurred while processing attendance: {str(e)}")
