#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_new_constraints():
    print("=== DEBUGGING NEW CONSTRAINTS BLOCKING ASSIGNMENTS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_cases = [
        (date(2025, 6, 12), "Thursday"),  # Missing Thursday
        (date(2025, 6, 26), "Thursday"),  # Missing Thursday
        (date(2025, 6, 7), "Saturday"),   # Missing Saturday
        (date(2025, 6, 28), "Saturday"),  # Missing Saturday
    ]
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    
    schedule = []  # Start with empty schedule
    
    for test_date, day_name in test_cases:
        print(f"\n=== TESTING {day_name.upper()} {test_date} ===")
        
        for person_id in personnel_ids[:3]:  # Test first 3 people
            print(f"\nPerson {person_id}:")
            
            first_week_blocked = scheduler.check_first_week_pairing_rules(person_id, test_date, schedule, 2025, 6)
            print(f"  First week rules blocked: {first_week_blocked}")
            
            percentage_blocked = scheduler.check_same_day_type_percentage_restriction(person_id, test_date, day_name, schedule, 2025, 6)
            print(f"  Percentage restriction blocked: {percentage_blocked}")
            
            day_values = scheduler.get_day_values()
            day_value = None
            for value_id, value_info in day_values.items():
                if value_info['name'] == day_name:
                    day_value = value_info['value']
                    break
            
            if day_value:
                critical_blocked = scheduler.check_critical_day_same_value_conflict(person_id, test_date, day_name, day_value, schedule, 2025, 6)
                print(f"  Critical day same value blocked: {critical_blocked}")
            
            consecutive_blocked = scheduler.has_consecutive_days_conflict(person_id, test_date, schedule)
            print(f"  Consecutive days blocked: {consecutive_blocked}")
            
            total_blocked = first_week_blocked or percentage_blocked or (critical_blocked if day_value else False) or consecutive_blocked
            print(f"  TOTAL BLOCKED: {total_blocked}")

if __name__ == "__main__":
    debug_new_constraints()
