#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_proven_algorithm():
    print("=== DEBUGGING USER'S PROVEN ALGORITHM IMPLEMENTATION ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    print(f"Active personnel: {len(personnel)} people")
    for p in personnel:
        print(f"  Person {p[0]}: {p[1]} ({p[2]})")
    
    day_values = scheduler.get_day_values()
    print(f"\nDay values: {len(day_values)} entries")
    for id, info in day_values.items():
        print(f"  {id}: {info['name']} = {info['value']}")
    
    test_date_thursday = date(2025, 6, 5)  # Thursday
    test_date_saturday = date(2025, 6, 14)  # Saturday (different week)
    
    print(f"\nTesting pairing logic:")
    print(f"Thursday: {test_date_thursday} (week {test_date_thursday.isocalendar()[1]})")
    print(f"Saturday: {test_date_saturday} (week {test_date_saturday.isocalendar()[1]})")
    
    empty_schedule = []
    
    for person_id, name, status in personnel[:3]:
        thursday_conflict = scheduler.needs_thursday_saturday_pairing(person_id, test_date_thursday, empty_schedule, 2025, 6)
        thursday_bonus = scheduler.calculate_pairing_bonus(person_id, test_date_thursday, empty_schedule, 2025, 6)
        
        print(f"\nPerson {person_id} ({name}) on Thursday:")
        print(f"  Conflict: {thursday_conflict}")
        print(f"  Bonus: {thursday_bonus}")
        
        schedule_with_thursday = [(test_date_thursday, person_id, 'Perşembe')]
        saturday_conflict = scheduler.needs_thursday_saturday_pairing(person_id, test_date_saturday, schedule_with_thursday, 2025, 6)
        saturday_bonus = scheduler.calculate_pairing_bonus(person_id, test_date_saturday, schedule_with_thursday, 2025, 6)
        
        print(f"  Saturday after Thursday:")
        print(f"    Conflict: {saturday_conflict}")
        print(f"    Bonus: {saturday_bonus}")

if __name__ == "__main__":
    debug_proven_algorithm()
