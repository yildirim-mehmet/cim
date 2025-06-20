#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
import calendar

def test_constraint_method():
    print("=== TESTING DAY-TYPE CONSTRAINT METHOD ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    mock_schedule = [
        (date(2025, 6, 2), 1, "Monday"),    # Person 1 - Monday #1
        (date(2025, 6, 9), 1, "Monday"),    # Person 1 - Monday #2
        (date(2025, 6, 3), 2, "Tuesday"),   # Person 2 - Tuesday #1
    ]
    
    test_date_monday = date(2025, 6, 16)  # Another Monday
    test_date_tuesday = date(2025, 6, 10)  # Another Tuesday
    test_date_wednesday = date(2025, 6, 4)  # Wednesday
    
    print("Testing constraint method directly:")
    
    conflict_monday = scheduler.has_day_type_limit_conflict(1, test_date_monday, mock_schedule)
    conflict_tuesday = scheduler.has_day_type_limit_conflict(2, test_date_tuesday, mock_schedule)
    conflict_wednesday = scheduler.has_day_type_limit_conflict(1, test_date_wednesday, mock_schedule)
    
    print(f"Person 1 Monday conflict (should be True): {conflict_monday}")
    print(f"Person 2 Tuesday conflict (should be False): {conflict_tuesday}")
    print(f"Person 1 Wednesday conflict (should be False): {conflict_wednesday}")
    
    return conflict_monday and not conflict_tuesday and not conflict_wednesday

def test_simple_schedule():
    print("\n=== TESTING SIMPLE SCHEDULE GENERATION ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    try:
        schedule = scheduler.generate_schedule(2025, 6)
        print(f"Schedule generated successfully with {len(schedule)} days")
        
        person_day_counts = {}
        for scheduled_date, person_id, _ in schedule:
            if person_id:
                day_name = calendar.day_name[scheduled_date.weekday()]
                if person_id not in person_day_counts:
                    person_day_counts[person_id] = {}
                person_day_counts[person_id][day_name] = person_day_counts[person_id].get(day_name, 0) + 1
        
        violations = []
        for person_id, day_counts in person_day_counts.items():
            for day_name, count in day_counts.items():
                if count > 2:
                    violations.append(f"Person {person_id}: {day_name} = {count}")
        
        if violations:
            print(f"❌ VIOLATIONS: {violations}")
            return False
        else:
            print("✅ All day-type constraints satisfied")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    method_test_passed = test_constraint_method()
    schedule_test_passed = test_simple_schedule()
    
    print(f"\n=== RESULTS ===")
    print(f"Constraint method test: {'✅ PASSED' if method_test_passed else '❌ FAILED'}")
    print(f"Schedule generation test: {'✅ PASSED' if schedule_test_passed else '❌ FAILED'}")
    
    if method_test_passed and schedule_test_passed:
        print("🎉 DAY-TYPE CONSTRAINT IMPLEMENTATION SUCCESSFUL!")
    else:
        print("💥 IMPLEMENTATION NEEDS REVIEW")
