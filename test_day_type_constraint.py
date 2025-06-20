#!/usr/bin/env python3
"""
Test day-type constraint implementation
"""
import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
from collections import defaultdict
import calendar

def test_day_type_tracking():
    print("=== TESTING DAY-TYPE CONSTRAINT LOGIC ===\n")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    # Test month: June 2025 (30 days)
    year, month = 2025, 6
    
    print(f"Testing {calendar.month_name[month]} {year}")
    
    # Count day types in the month
    day_type_counts = defaultdict(int)
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        current_date = date(year, month, day)
        weekday = current_date.weekday()  # Monday=0, Sunday=6
        day_name = calendar.day_name[weekday]
        day_type_counts[day_name] += 1
    
    print("Day type distribution:")
    for day_name, count in day_type_counts.items():
        print(f"  {day_name}: {count} occurrences")
    
    print(f"\nMax occurrences: {max(day_type_counts.values())}")
    print(f"Min occurrences: {min(day_type_counts.values())}")
    
    # Test constraint logic
    max_same_day_type = 2
    print(f"\nConstraint: Max {max_same_day_type} assignments per person per day type")
    
    # Simulate tracking during scheduling
    person_day_type_count = defaultdict(lambda: defaultdict(int))
    
    # Example assignments
    test_assignments = [
        (date(2025, 6, 2), 1, "Monday"),    # Person 1 - Monday
        (date(2025, 6, 9), 1, "Monday"),    # Person 1 - Monday (2nd)
        (date(2025, 6, 16), 1, "Monday"),   # Person 1 - Monday (3rd - should be blocked)
        (date(2025, 6, 3), 2, "Tuesday"),   # Person 2 - Tuesday
        (date(2025, 6, 10), 2, "Tuesday"),  # Person 2 - Tuesday (2nd)
    ]
    
    print("\nSimulating assignments:")
    for scheduled_date, person_id, day_type in test_assignments:
        current_count = person_day_type_count[person_id][day_type]
        
        if current_count >= max_same_day_type:
            print(f"  ❌ BLOCKED: Person {person_id} already has {current_count} {day_type} assignments")
        else:
            person_day_type_count[person_id][day_type] += 1
            new_count = person_day_type_count[person_id][day_type]
            print(f"  ✅ ALLOWED: Person {person_id} - {day_type} ({new_count}/{max_same_day_type})")
    
    print("\nFinal day-type counts per person:")
    for person_id, day_counts in person_day_type_count.items():
        print(f"  Person {person_id}:")
        for day_type, count in day_counts.items():
            print(f"    {day_type}: {count}")

if __name__ == "__main__":
    test_day_type_tracking()
