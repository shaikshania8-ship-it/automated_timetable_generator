from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models, database, scheduler
from pydantic import BaseModel
import datetime

app = FastAPI(title="Automated Timetable Generator")

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
models.Base.metadata.create_all(bind=database.engine)

# Pydantic models for request validation
class FacultyCreate(BaseModel):
    id: str
    name: str
    subject_expertise: str
    availability: dict

class SubjectCreate(BaseModel):
    code: str
    name: str
    weekly_hours: int
    type: str
    class_id: str

class ClassCreate(BaseModel):
    id: str
    name: str
    student_strength: int

class RoomCreate(BaseModel):
    id: str
    name: str
    capacity: int
    type: str

class SettingsCreate(BaseModel):
    working_days: int
    periods_per_day: int

@app.post("/add-faculty")
def add_faculty(faculty: FacultyCreate, db: Session = Depends(database.get_db)):
    db_fac = db.query(models.Faculty).filter(models.Faculty.id == faculty.id).first()
    if db_fac:
        raise HTTPException(status_code=400, detail="Faculty ID already exists")
    new_fac = models.Faculty(**faculty.dict())
    db.add(new_fac)
    db.commit()
    return {"message": "Faculty added successfully"}

@app.get("/faculty")
def get_all_faculty(db: Session = Depends(database.get_db)):
    return db.query(models.Faculty).all()

@app.post("/add-subject")
def add_subject(subject: SubjectCreate, db: Session = Depends(database.get_db)):
    db_sub = db.query(models.Subject).filter(models.Subject.code == subject.code).first()
    if db_sub:
        raise HTTPException(status_code=400, detail="Subject code already exists")
    new_sub = models.Subject(**subject.dict())
    db.add(new_sub)
    db.commit()
    return {"message": "Subject added successfully"}

@app.get("/subjects")
def get_all_subjects(db: Session = Depends(database.get_db)):
    return db.query(models.Subject).all()

@app.post("/add-class")
def add_class(cls: ClassCreate, db: Session = Depends(database.get_db)):
    db_cls = db.query(models.ClassGroup).filter(models.ClassGroup.id == cls.id).first()
    if db_cls:
        raise HTTPException(status_code=400, detail="Class ID already exists")
    new_cls = models.ClassGroup(**cls.dict())
    db.add(new_cls)
    db.commit()
    return {"message": "Class added successfully"}

@app.get("/classes")
def get_all_classes(db: Session = Depends(database.get_db)):
    return db.query(models.ClassGroup).all()

@app.post("/add-room")
def add_room(room: RoomCreate, db: Session = Depends(database.get_db)):
    db_room = db.query(models.ClassRoom).filter(models.ClassRoom.id == room.id).first()
    if db_room:
        raise HTTPException(status_code=400, detail="Room ID already exists")
    new_room = models.ClassRoom(**room.dict())
    db.add(new_room)
    db.commit()
    return {"message": "Room added successfully"}

@app.get("/rooms")
def get_all_rooms(db: Session = Depends(database.get_db)):
    return db.query(models.ClassRoom).all()

@app.post("/settings")
def update_settings(settings: SettingsCreate, db: Session = Depends(database.get_db)):
    db_settings = db.query(models.AcademicSettings).first()
    if db_settings:
        db_settings.working_days = settings.working_days
        db_settings.periods_per_day = settings.periods_per_day
    else:
        db_settings = models.AcademicSettings(**settings.dict())
        db.add(db_settings)
    db.commit()
    return {"message": "Settings updated"}

@app.get("/settings")
def get_settings(db: Session = Depends(database.get_db)):
    s = db.query(models.AcademicSettings).first()
    if not s:
        return {"working_days": 5, "periods_per_day": 6}
    return s

@app.post("/generate")
def generate(db: Session = Depends(database.get_db)):
    result = scheduler.generate_timetable(db)
    return result

@app.get("/timetable/class/{id}")
def get_class_timetable(id: str, db: Session = Depends(database.get_db)):
    entries = db.query(models.TimetableEntry).filter(models.TimetableEntry.class_id == id).all()
    return entries

@app.get("/timetable/faculty/{id}")
def get_faculty_timetable(id: str, db: Session = Depends(database.get_db)):
    entries = db.query(models.TimetableEntry).filter(models.TimetableEntry.faculty_id == id).all()
    return entries

@app.get("/timetable/room/{id}")
def get_room_timetable(id: str, db: Session = Depends(database.get_db)):
    entries = db.query(models.TimetableEntry).filter(models.TimetableEntry.room_id == id).all()
    return entries

@app.get("/logs")
def get_logs(db: Session = Depends(database.get_db)):
    logs = db.query(models.GenerationLog).order_by(models.GenerationLog.timestamp.desc()).all()
    return logs

@app.get("/logs/{id}/conflicts")
def get_conflicts(id: int, db: Session = Depends(database.get_db)):
    return db.query(models.ConflictLog).filter(models.ConflictLog.generation_id == id).all()