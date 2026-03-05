import time
import random
from sqlalchemy.orm import Session
from models import Faculty, Subject, ClassRoom, ClassGroup, TimetableEntry, GenerationLog, ConflictLog, AcademicSettings

class TimetableScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.faculty = db.query(Faculty).all()
        self.subjects = db.query(Subject).all()
        self.rooms = db.query(ClassRoom).all()
        self.classes = db.query(ClassGroup).all()
        self.settings = db.query(AcademicSettings).first()
        
        if not self.settings:
            # Default settings if none exist
            self.working_days = 5
            self.periods_per_day = 6
        else:
            self.working_days = self.settings.working_days
            self.periods_per_day = self.settings.periods_per_day

    def generate(self):
        start_time = time.time()
        
        # 1. Initialize grid: grid[day][period] = list of assigned entries
        # entry = {class_id, faculty_id, subject_code, room_id}
        grid = [[[] for _ in range(self.periods_per_day)] for _ in range(self.working_days)]
        
        # 2. Prepare subjects to schedule (flatten weekly hours)
        to_schedule = []
        for sub in self.subjects:
            # For labs, we might want to group them into blocks of 2 or 3
            if sub.type.lower() == 'lab':
                # Labs usually take 2 periods
                full_blocks = sub.weekly_hours // 2
                rem = sub.weekly_hours % 2
                for _ in range(full_blocks):
                    to_schedule.append({'subject': sub, 'duration': 2})
                if rem > 0:
                    to_schedule.append({'subject': sub, 'duration': rem})
            else:
                for _ in range(sub.weekly_hours):
                    to_schedule.append({'subject': sub, 'duration': 1})
        
        # Sorting priority: Labs first, then higher weekly hours
        to_schedule.sort(key=lambda x: (x['duration'] if x['subject'].type.lower() == 'lab' else 0, x['subject'].weekly_hours), reverse=True)
        
        assigned_entries = []
        conflicts = []
        
        # 3. Simple Greedy Allocation with basic logic
        # For each subject instance, find a valid slot
        for item in to_schedule:
            sub = item['subject']
            duration = item['duration']
            found = False
            
            # Find faculty for this subject expertise (in a real system, subjects should be linked to faculty)
            # For this prototype, let's assume subject expertise string contains the subject code or name
            potential_faculty = [f for f in self.faculty if sub.code in f.subject_expertise or sub.name in f.subject_expertise]
            
            if not potential_faculty:
                conflicts.append(f"No faculty found for subject {sub.code}")
                continue
                
            # Try to shuffle days and periods for better distribution
            days = list(range(self.working_days))
            periods = list(range(self.periods_per_day - duration + 1))
            random.shuffle(days)
            random.shuffle(periods)
            
            for day in days:
                for period in periods:
                    # Check if faculty is available at this time
                    # Check if classes and rooms are free
                    for fac in potential_faculty:
                        # Check availability matrix
                        # fac.availability is JSON: {"0": [1,1,0,1,1,1], "1": [...]} 1=available
                        day_str = str(day)
                        if fac.availability and day_str in fac.availability:
                            if not all(fac.availability[day_str][period + i] for i in range(duration)):
                                continue
                        
                        # Room check
                        valid_rooms = [r for r in self.rooms if r.type.lower() == sub.type.lower() and r.capacity >= (self.get_class_strength(sub.class_id))]
                        if not valid_rooms:
                            continue
                            
                        # Try each room
                        for room in valid_rooms:
                            if self.is_slot_free(grid, day, period, duration, fac.id, sub.class_id, room.id):
                                # Assign
                                for i in range(duration):
                                    entry = {
                                        'class_id': sub.class_id,
                                        'faculty_id': fac.id,
                                        'subject_code': sub.code,
                                        'room_id': room.id,
                                        'day': day,
                                        'period': period + i
                                    }
                                    grid[day][period + i].append(entry)
                                    assigned_entries.append(entry)
                                found = True
                                break
                        if found: break
                    if found: break
                if found: break
            
            if not found:
                conflicts.append(f"Could not schedule {sub.name} ({sub.code}) for class {sub.class_id}")

        execution_time = time.time() - start_time
        
        # Calculate soft score
        soft_score = self.calculate_soft_score(assigned_entries)
        
        # Save results
        status = "Valid" if not conflicts else "Invalid"
        log = GenerationLog(
            execution_time=execution_time,
            soft_score=soft_score,
            status=status,
            fail_reason=", ".join(conflicts) if conflicts else None
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        if status == "Valid":
            # Clear old timetable and save new one
            self.db.query(TimetableEntry).delete()
            for entry in assigned_entries:
                db_entry = TimetableEntry(**entry)
                self.db.add(db_entry)
            self.db.commit()
        else:
            for c in conflicts:
                self.db.add(ConflictLog(generation_id=log.id, conflict_details=c))
            self.db.commit()
            
        return {
            "status": status,
            "execution_time": execution_time,
            "soft_score": soft_score,
            "conflicts": conflicts
        }

    def get_class_strength(self, class_id):
        for c in self.classes:
            if c.id == class_id:
                return c.student_strength
        return 0

    def is_slot_free(self, grid, day, period, duration, faculty_id, class_id, room_id):
        for i in range(duration):
            for entry in grid[day][period + i]:
                if entry['faculty_id'] == faculty_id: return False
                if entry['class_id'] == class_id: return False
                if entry['room_id'] == room_id: return False
        return True

    def calculate_soft_score(self, entries):
        # penalize: 3 consecutive periods, uneven spread, etc.
        score = 1000
        
        # Organize entries by class and day
        by_class_day = {}
        for e in entries:
            key = (e['class_id'], e['day'])
            if key not in by_class_day: by_class_day[key] = []
            by_class_day[key].append(e)
            
        for key, day_entries in by_class_day.items():
            day_entries.sort(key=lambda x: x['period'])
            
            # Check consecutive
            consecutive = 1
            for i in range(1, len(day_entries)):
                if day_entries[i]['subject_code'] == day_entries[i-1]['subject_code'] and day_entries[i]['period'] == day_entries[i-1]['period'] + 1:
                    consecutive += 1
                else:
                    consecutive = 1
                
                if consecutive >= 3:
                    score -= 50 # Penalty for 3 consecutive same subject
            
            # Penalty for uneven spread (too many or too few classes in a day)
            if len(day_entries) > self.periods_per_day - 1:
                score -= 10
            if len(day_entries) < 2:
                score -= 20
                
        return max(0, score)

def generate_timetable(db: Session):
    scheduler = TimetableScheduler(db)
    return scheduler.generate()
