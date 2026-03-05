from pydantic import BaseModel

class FacultyCreate(BaseModel):
    faculty_id: str
    name: str
    expertise: str

class SubjectCreate(BaseModel):
    name: str
    hours_per_week: int

class RoomCreate(BaseModel):
    room_name: str
    room_type: str

class ClassCreate(BaseModel):
    class_name: str