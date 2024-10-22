from fastapi import FastAPI
from database import engine, Base
from routers import add_attendance, students, cleanup, admins
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from config import settings

# Initialize FastAPI
app = FastAPI(debug=True)

# Add the session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, session_cookie="session",  # Name of the session cookie           
)

# Create the database tables if they don't already exist
Base.metadata.create_all(bind=engine)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the routers
app.include_router(add_attendance.router, prefix="/input", tags=["Input"])
app.include_router(students.router, prefix="", tags=["Student"])
# app.include_router(cleanup.router)
app.include_router(admins.router, prefix="/admin", tags=["Admin"])



# Root endpoint
# @app.get("/")
# def root():
#     return {"message": "Attendance Management System is running!"}
