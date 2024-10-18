from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta

# Clean up old class tables (older than 1 year)
def cleanup_old_class_data(db: Session):
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    old_classes = db.execute(text("""
        SELECT class_table_name FROM meta_class_data WHERE last_updated < :one_year_ago
    """), {'one_year_ago': one_year_ago}).fetchall()
    for class_row in old_classes:
        class_table_name = class_row['class_table_name']
        db.execute(text(f"DROP TABLE IF EXISTS {class_table_name}"))
        db.execute(text("""
            DELETE FROM meta_class_data WHERE class_table_name = :class_table_name
        """), {'class_table_name': class_table_name})


# Clean up old student-class mappings (older than 1 year)
def cleanup_old_student_mappings(db: Session):
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    db.execute(text("""
        DELETE FROM student_class_mapping WHERE added_date < :one_year_ago
    """), {'one_year_ago': one_year_ago})
