#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
import calendar

def test_day_type_constraint():
    print("=== TESTING DAY-TYPE CONSTRAINT ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    test_cases = [
        (2025, 6),  # June: 30 days
        (2025, 7),  # July: 31 days  
        (2025, 2),  # February: 28 days
    ]
    
    for year, month in test_cases:
        print(f"\nTesting {calendar.month_name[month]} {year}")
        
        days_in_month = calendar.monthrange(year, month)[1]
        day_type_distribution = {}
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            day_name = calendar.day_name[current_date.weekday()]
            day_type_distribution[day_name] = day_type_distribution.get(day_name, 0) + 1
        
        print("Day type distribution:")
        for day_name, count in sorted(day_type_distribution.items()):
            print(f"  {day_name}: {count} occurrences")
        
        schedule = scheduler.generate_schedule(year, month)
        
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
            
        print("Personnel day-type assignments:")
        for person_id, day_counts in sorted(person_day_counts.items()):
            person_name = scheduler.get_person_name(person_id)
            print(f"  {person_name} (ID {person_id}):")
            for day_name, count in sorted(day_counts.items()):
                print(f"    {day_name}: {count}")
    
    return True

def test_edge_cases():
    print("\n=== TESTING EDGE CASES ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    print("\nTesting constraint method directly:")
    
    mock_schedule = [
        (date(2025, 6, 2), 1, "Monday"),    # Person 1 - Monday #1
        (date(2025, 6, 9), 1, "Monday"),    # Person 1 - Monday #2
        (date(2025, 6, 3), 2, "Tuesday"),   # Person 2 - Tuesday #1
    ]
    
    test_date_monday = date(2025, 6, 16)  # Another Monday
    test_date_tuesday = date(2025, 6, 10)  # Another Tuesday
    
    conflict_monday = scheduler.has_day_type_limit_conflict(1, test_date_monday, mock_schedule)
    conflict_tuesday = scheduler.has_day_type_limit_conflict(2, test_date_tuesday, mock_schedule)
    
    print(f"Person 1 Monday conflict (should be True): {conflict_monday}")
    print(f"Person 2 Tuesday conflict (should be False): {conflict_tuesday}")
    
    return conflict_monday and not conflict_tuesday

if __name__ == "__main__":
    constraint_test_passed = test_day_type_constraint()
    edge_case_test_passed = test_edge_cases()
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Day-type constraint test: {'✅ PASSED' if constraint_test_passed else '❌ FAILED'}")
    print(f"Edge case test: {'✅ PASSED' if edge_case_test_passed else '❌ FAILED'}")
    
    if constraint_test_passed and edge_case_test_passed:
        print("🎉 ALL TESTS PASSED - Day-type constraint implementation successful!")
    else:
        print("💥 SOME TESTS FAILED - Implementation needs review")
