#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
from collections import defaultdict

def debug_duplicate_assignments():
    print("=== DEBUGGING DUPLICATE ASSIGNMENTS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    print(f"Total schedule entries: {len(schedule)}")
    
    date_assignments = defaultdict(list)
    for date_obj, person_id, day_type in schedule:
        date_assignments[date_obj].append((person_id, day_type))
    
    print(f"\nDuplicate date assignments:")
    duplicates_found = False
    for date_obj, assignments in date_assignments.items():
        if len(assignments) > 1:
            duplicates_found = True
            print(f"  {date_obj}: {assignments}")
    
    if not duplicates_found:
        print("  No duplicate dates found")
    
    none_assignments = [(d, t) for d, p, t in schedule if p is None]
    print(f"\nNone assignments: {len(none_assignments)}")
    for date_obj, day_type in none_assignments:
        print(f"  {date_obj} ({day_type}): No person assigned")
    
    person_assignments = defaultdict(list)
    for date_obj, person_id, day_type in schedule:
        if person_id:
            person_assignments[person_id].append((date_obj, day_type))
    
    print(f"\nAssignment distribution:")
    for person_id, assignments in person_assignments.items():
        print(f"  Person {person_id}: {len(assignments)} assignments")
        critical_days = [day_type for _, day_type in assignments if day_type in ['Perşembe', 'Cuma', 'Cumartesi', 'Pazar']]
        print(f"    Critical days: {len(critical_days)} - {critical_days}")
    
    print(f"\nConsecutive assignment violations:")
    violations_found = False
    for person_id, assignments in person_assignments.items():
        dates = sorted([date_obj for date_obj, _ in assignments])
        for i in range(len(dates) - 1):
            if (dates[i+1] - dates[i]).days == 1:
                violations_found = True
                print(f"  Person {person_id}: {dates[i]} -> {dates[i+1]} (consecutive)")
    
    if not violations_found:
        print("  No consecutive assignment violations found")

if __name__ == "__main__":
    debug_duplicate_assignments()
