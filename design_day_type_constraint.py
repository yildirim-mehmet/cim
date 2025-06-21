#!/usr/bin/env python3
"""
Design and test day-type constraint implementation approach
"""
import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
from collections import defaultdict
import calendar

def design_constraint_integration():
    print("=== DESIGNING DAY-TYPE CONSTRAINT INTEGRATION ===\n")
    
    # Analyze current algorithm structure
    print("Current algorithm flow:")
    print("1. Get personnel, day values, holidays, exemptions")
    print("2. Calculate stats and averages")
    print("3. For each day in month:")
    print("   - Determine day type (holiday or weekday)")
    print("   - Check eligible personnel:")
    print("     a. Skip if last month duty person on day 1")
    print("     b. Skip if exemption tut=0")
    print("     c. Skip if Ramazan-Kurban conflict")
    print("     d. Skip if Thursday-Saturday conflict")
    print("     e. Skip if consecutive days conflict")
    print("   - Calculate priority scores")
    print("   - Select highest priority person")
    print("   - Update stats")
    
    print("\n=== PROPOSED DAY-TYPE CONSTRAINT INTEGRATION ===")
    print("Add new constraint check in eligible personnel loop:")
    print("   f. Skip if person already has 2+ assignments of this day type")
    
    print("\nImplementation approach:")
    print("1. Add person_day_type_count tracking dictionary")
    print("2. Initialize with defaultdict(lambda: defaultdict(int))")
    print("3. In eligible personnel loop, check current count")
    print("4. After assignment, update the tracking dictionary")
    
    # Test the tracking logic
    print("\n=== TESTING TRACKING LOGIC ===")
    
    # Simulate tracking during scheduling
    person_day_type_count = defaultdict(lambda: defaultdict(int))
    max_same_day_type = 2
    
    # Test assignments for June 2025
    test_assignments = [
        (date(2025, 6, 2), 1, "Monday"),    # Person 1 - Monday #1
        (date(2025, 6, 9), 1, "Monday"),    # Person 1 - Monday #2
        (date(2025, 6, 16), 1, "Monday"),   # Person 1 - Monday #3 (should block)
        (date(2025, 6, 23), 1, "Monday"),   # Person 1 - Monday #4 (should block)
        (date(2025, 6, 3), 2, "Tuesday"),   # Person 2 - Tuesday #1
        (date(2025, 6, 10), 2, "Tuesday"),  # Person 2 - Tuesday #2
        (date(2025, 6, 17), 2, "Tuesday"),  # Person 2 - Tuesday #3 (should block)
    ]
    
    print("Simulating constraint checking:")
    allowed_assignments = []
    blocked_assignments = []
    
    for scheduled_date, person_id, day_type in test_assignments:
        day_name = calendar.day_name[scheduled_date.weekday()]
        current_count = person_day_type_count[person_id][day_name]
        
        if current_count >= max_same_day_type:
            blocked_assignments.append((scheduled_date, person_id, day_name, current_count))
            print(f"  ❌ BLOCKED: Person {person_id} - {day_name} {scheduled_date.strftime('%d.%m')} (already has {current_count})")
        else:
            person_day_type_count[person_id][day_name] += 1
            new_count = person_day_type_count[person_id][day_name]
            allowed_assignments.append((scheduled_date, person_id, day_name, new_count))
            print(f"  ✅ ALLOWED: Person {person_id} - {day_name} {scheduled_date.strftime('%d.%m')} ({new_count}/{max_same_day_type})")
    
    print(f"\nResults:")
    print(f"  Allowed assignments: {len(allowed_assignments)}")
    print(f"  Blocked assignments: {len(blocked_assignments)}")
    
    print("\nFinal day-type counts per person:")
    for person_id, day_counts in person_day_type_count.items():
        print(f"  Person {person_id}:")
        for day_type, count in day_counts.items():
            print(f"    {day_type}: {count}")
    
    print("\n=== INTEGRATION POINTS ===")
    print("Files to modify:")
    print("1. scheduler.py - Add day-type constraint checking")
    print("2. Test files - Verify constraint works correctly")
    
    print("\nCode locations:")
    print("- Line ~172: Initialize person_day_type_count = defaultdict(lambda: defaultdict(int))")
    print("- Line ~185-204: Add day-type constraint check in eligible personnel loop")
    print("- Line ~213-214: Update person_day_type_count after assignment")

if __name__ == "__main__":
    design_constraint_integration()
