#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_pairing_constraints():
    print("=== DEBUGGING PAIRING CONSTRAINTS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    thursday_date = date(2025, 6, 5)  # Thursday W23
    saturday_date = date(2025, 6, 14)  # Saturday W24 (different week)
    
    print(f"Testing Thursday {thursday_date} (Week {thursday_date.isocalendar()[1]})")
    print(f"Testing Saturday {saturday_date} (Week {saturday_date.isocalendar()[1]})")
    
    personnel = scheduler.get_active_personnel()
    print(f"Available personnel: {[p[0] for p in personnel]}")
    
    empty_schedule = []
    
    for person_id, name, status in personnel:
        print(f"\n--- Testing Person {person_id} ({name}) ---")
        
        thursday_conflict = scheduler.needs_thursday_saturday_pairing(person_id, thursday_date, empty_schedule, 2025, 6)
        thursday_bonus = scheduler.calculate_pairing_bonus(person_id, thursday_date, empty_schedule, 2025, 6)
        print(f"Thursday {thursday_date}: conflict={thursday_conflict}, bonus={thursday_bonus}")
        
        saturday_conflict = scheduler.needs_thursday_saturday_pairing(person_id, saturday_date, empty_schedule, 2025, 6)
        saturday_bonus = scheduler.calculate_pairing_bonus(person_id, saturday_date, empty_schedule, 2025, 6)
        print(f"Saturday {saturday_date}: conflict={saturday_conflict}, bonus={saturday_bonus}")
        
        schedule_with_thursday = [(thursday_date, person_id, 'Perşembe')]
        saturday_conflict_with_thursday = scheduler.needs_thursday_saturday_pairing(person_id, saturday_date, schedule_with_thursday, 2025, 6)
        saturday_bonus_with_thursday = scheduler.calculate_pairing_bonus(person_id, saturday_date, schedule_with_thursday, 2025, 6)
        print(f"Saturday with Thursday assigned: conflict={saturday_conflict_with_thursday}, bonus={saturday_bonus_with_thursday}")
        
        break  # Test only first person for now

if __name__ == "__main__":
    debug_pairing_constraints()
