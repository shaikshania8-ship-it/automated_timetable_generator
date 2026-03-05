from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    subject_expertise = Column(String) # For display
    availability = Column(JSON) # Matrix or list of available slots

class Subject(Base):
    __tablename__ = "subjects"
    code = Column(String, primary_key=True, index=True)
    name = Column(String)
    weekly_hours = Column(Integer)
    type = Column(String) # Lab/Theory
    class_id = Column(String, ForeignKey("classes.id"))

class ClassRoom(Base):
    __tablename__ = "rooms"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    capacity = Column(Integer)
    type = Column(String) # Lab/Theory/General

class ClassGroup(Base):
    __tablename__ = "classes"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    student_strength = Column(Integer)

class TimetableEntry(Base):
    __tablename__ = "timetable_entries"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    class_id = Column(String, ForeignKey("classes.id"))
    faculty_id = Column(String, ForeignKey("faculty.id"))
    subject_code = Column(String, ForeignKey("subjects.code"))
    room_id = Column(String, ForeignKey("rooms.id"))
    day = Column(Integer) # 0-5 (Mon-Sat)
    period = Column(Integer) 

class GenerationLog(Base):
    __tablename__ = "generation_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    execution_time = Column(Float)
    soft_score = Column(Float)
    status = Column(String) # Valid/Invalid
    fail_reason = Column(String, nullable=True)

class ConflictLog(Base):
    __tablename__ = "conflict_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    generation_id = Column(Integer, ForeignKey("generation_logs.id"))
    conflict_details = Column(String)

class AcademicSettings(Base):
    __tablename__ = "academic_settings"
    id = Column(Integer, primary_key=True, default=1)
    working_days = Column(Integer, default=5)
    periods_per_day = Column(Integer, default=6)
