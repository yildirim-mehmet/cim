#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
import calendar

def test_integrated_constraints():
    print("=== TESTING INTEGRATED MIN/MAX + DAY-TYPE CONSTRAINTS ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    print("\nTesting with min_nob=2, max_nob=6")
    schedule = scheduler.generate_schedule(2025, 6, min_nob=2, max_nob=6)
    
    print(f"Schedule generated successfully with {len(schedule)} days")
    
    person_assignments = {}
    person_day_types = {}
    
    for scheduled_date, person_id, day_type in schedule:
        if person_id:
            if person_id not in person_assignments:
                person_assignments[person_id] = 0
                person_day_types[person_id] = {}
            
            person_assignments[person_id] += 1
            
            day_name = calendar.day_name[scheduled_date.weekday()]
            person_day_types[person_id][day_name] = person_day_types[person_id].get(day_name, 0) + 1
    
    print("\nPersonnel assignment counts:")
    for person_id, count in person_assignments.items():
        person_name = scheduler.get_person_name(person_id)
        print(f"  {person_name} (ID {person_id}): {count} assignments")
    
    print("\nDay-type constraint verification:")
    violations = []
    for person_id, day_counts in person_day_types.items():
        person_name = scheduler.get_person_name(person_id)
        print(f"  {person_name}:")
        for day_name, count in sorted(day_counts.items()):
            print(f"    {day_name}: {count}")
            if count > 2:
                violations.append(f"{person_name}: {day_name} = {count}")
    
    if violations:
        print(f"\n❌ DAY-TYPE VIOLATIONS: {violations}")
        return False
    else:
        print("\n✅ All day-type constraints satisfied (max 2 per day type)")
    
    return True

def test_constraint_methods():
    print("\n=== TESTING CONSTRAINT METHODS DIRECTLY ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    mock_schedule = [
        (date(2025, 6, 2), 1, "Monday"),    # Person 1 - Monday #1
        (date(2025, 6, 9), 1, "Monday"),    # Person 1 - Monday #2
        (date(2025, 6, 3), 2, "Tuesday"),   # Person 2 - Tuesday #1
    ]
    
    count_monday = scheduler.get_day_type_count(1, date(2025, 6, 16), mock_schedule)  # Another Monday
    count_tuesday = scheduler.get_day_type_count(2, date(2025, 6, 10), mock_schedule)  # Another Tuesday
    
    print(f"Person 1 Monday count: {count_monday} (should be 2)")
    print(f"Person 2 Tuesday count: {count_tuesday} (should be 1)")
    
    conflict_monday = scheduler.has_day_type_limit_conflict(1, date(2025, 6, 16), mock_schedule)
    conflict_tuesday = scheduler.has_day_type_limit_conflict(2, date(2025, 6, 10), mock_schedule)
    
    print(f"Person 1 Monday conflict: {conflict_monday} (should be True)")
    print(f"Person 2 Tuesday conflict: {conflict_tuesday} (should be False)")
    
    return count_monday == 2 and count_tuesday == 1 and conflict_monday and not conflict_tuesday

if __name__ == "__main__":
    constraint_test_passed = test_integrated_constraints()
    method_test_passed = test_constraint_methods()
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Integrated constraint test: {'✅ PASSED' if constraint_test_passed else '❌ FAILED'}")
    print(f"Constraint method test: {'✅ PASSED' if method_test_passed else '❌ FAILED'}")
    
    if constraint_test_passed and method_test_passed:
        print("🎉 ALL TESTS PASSED - Integrated constraint system working!")
    else:
        print("💥 SOME TESTS FAILED - Implementation needs review")
