from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from crud.cleanup_data_crud import cleanup_old_class_data, cleanup_old_student_mappings

router = APIRouter()

# Cleanup endpoint to remove old class tables
@router.post("/cleanup_old_classes/")
def cleanup_old_classes(db: Session = Depends(get_db)):
    cleanup_old_class_data(db)
    return {"message": "Old class tables deleted successfully."}

# Cleanup endpoint to remove old student_class_mapping records
@router.post("/cleanup_old_student_mappings/")
def cleanup_old_student_mappings_route(db: Session = Depends(get_db)):
    cleanup_old_student_mappings(db)
    return {"message": "Old student-class mappings deleted successfully."}
