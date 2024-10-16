from pydantic import BaseModel
from typing import List, Optional

# Schema for a single attendance record (used when receiving data)
class AttendanceRecord(BaseModel):
    reg: str  # Registration number (Column A in your Google Sheet)
    pr: int  # Present days (Column C in your Google Sheet)
    ab: int  # Absent days (Column D in your Google Sheet)

# Schema for class attendance data (used when processing attendance)
class ClassAttendanceData(BaseModel):
    fileName: str  # The name of the Google Sheet file
    fileId: str  # The unique ID of the Google Sheet file
    ownerEmail: str  # The email of the sheet owner (used to determine department and prefix)
    data: List[AttendanceRecord]  # The list of attendance records (rows in the sheet)

    class Config:
        from_attributes = True  # This replaces orm_mode in Pydantic v2.x

# Schema for returning attendance data for a student
class StudentAttendance(BaseModel):
    class_table: str  # The name of the class table
    pr: int  # Number of present days
    ab: int  # Number of absent days

    class Config:
        from_attributes = True  # This replaces orm_mode in Pydantic v2.x

# Schema for returning all attendance data for a student
class StudentAttendanceResponse(BaseModel):
    reg_number: str  # The student's registration number
    attendance: List[StudentAttendance]  # List of attendance records for different classes

    class Config:
        from_attributes = True  # This replaces orm_mode in Pydantic v2.x

