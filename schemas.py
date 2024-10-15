from pydantic import BaseModel
from typing import List

class AttendanceRecord(BaseModel):
    reg: str
    pr: int
    ab: int

class ClassAttendanceData(BaseModel):
    fileName: str
    ownerName: str
    ownerEmail: str
    data: List[AttendanceRecord]
