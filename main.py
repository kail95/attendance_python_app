from fastapi import FastAPI
from database import engine, Base
from routers import attendance, students, cleanup

# Initialize FastAPI
app = FastAPI()

# Create the database tables if they don't already exist
Base.metadata.create_all(bind=engine)

# Include the routers
app.include_router(attendance.router)
app.include_router(students.router)
app.include_router(cleanup.router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Attendance Management System is running!"}
