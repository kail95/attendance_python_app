from pydantic import BaseModel
from typing import List, Optional

# Schema for a single attendance record (used when receiving data)
class AttendanceRecord(BaseModel):
    reg: str
    pr: int
    ab: int
    name: str  # Adding student name

    class Config:
        from_attributes = True


# Schema for class attendance data (used when processing attendance)
class ClassAttendanceData(BaseModel):
    fileName: str  # The name of the Google Sheet file
    fileId: str  # The unique ID of the Google Sheet file
    ownerEmail: str  # The email of the sheet owner (used to determine department and prefix)
    data: List[AttendanceRecord]  # The list of attendance records (rows in the sheet)

    class Config:
        from_attributes = True  # This replaces orm_mode in Pydantic v2.x



