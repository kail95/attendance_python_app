from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text

from utils.jwt import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db), 
                            current_user: dict = Depends(get_current_user)
):
    # Ensure the user is a student
    if current_user['user_type'] != "student":
        raise HTTPException(status_code=403, detail="Access denied")

    # current_user = {
    #     "user_type": "student",
    #     "email": "student@example.com",  # Fake email
    #     "reg_number": "AG/16/011"  # Fake registration number
    # }
    reg_number = current_user['reg_number'].lower()  # Lowercase the registration number for case-insensitive matching

    # Step 1: Get the class IDs and class labels from the student_class_mapping and meta_class_data tables
    class_data = db.execute(
        text("""
            SELECT sc.class_id, mc.class_table_name, mc.class_label
            FROM student_class_mapping sc
            JOIN meta_class_data mc ON sc.class_id = mc.class_id
            WHERE LOWER(sc.reg_number) = :reg_number
        """),
        {"reg_number": reg_number}
    ).fetchall()

    if not class_data:
        return HTMLResponse(content="<h1>No classes found for the student</h1>", status_code=200)

    # Step 2: Loop through class_data to get the attendance records from each class table
    all_records = []
    
    for class_info in class_data:
        class_table_name = class_info.class_table_name
        class_label = class_info.class_label  # This is the class name
        
        # Query attendance records from each class table for the current student
        records = db.execute(
            text(f"SELECT *, :class_label AS class_name FROM {class_table_name} WHERE LOWER(reg_number) = :reg_number"),
            {"reg_number": reg_number, "class_label": class_label}
        ).fetchall()

        all_records.extend(records)  # Add the records from each table with class name included

    if not all_records:
        return HTMLResponse(content="<h1>No attendance records found for the student</h1>", status_code=200)

    # Step 4: Render the results in the student dashboard, passing current_user data
    return templates.TemplateResponse("student/student_dashboard.html", {
        "request": request,
        "current_user": current_user,  # Pass current user data to the template
        "records": all_records  # Pass all attendance records to the template
    })