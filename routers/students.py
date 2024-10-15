from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text

router = APIRouter()

@router.get("/attendance/{reg_number}")
def get_attendance_for_student(reg_number: str, db: Session = Depends(get_db)):
    classes = db.execute(text(f"""
    SELECT class_id FROM student_class_mapping WHERE reg_number = :reg_number
    """), {'reg_number': reg_number}).fetchall()

    attendance_data = []

    for class_row in classes:
        class_id = class_row['class_id']
        result = db.execute(text(f"""
        SELECT * FROM {class_id} WHERE reg_number = :reg_number
        """), {'reg_number': reg_number}).fetchone()

        if result:
            attendance_data.append({
                "class_id": class_id,
                "present_days": result['present_days'],
                "absent_days": result['absent_days']
            })

    if not attendance_data:
        raise HTTPException(status_code=404, detail="No attendance data found for this student.")

    return {"reg_number": reg_number, "attendance": attendance_data}

