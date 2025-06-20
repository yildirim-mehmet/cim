#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_user_proven_detailed():
    print("=== DEBUGGING USER'S PROVEN ALGORITHM - DETAILED ANALYSIS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    print(f"Generated schedule with {len(schedule)} days")
    
    thursdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 3]
    saturdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 5]
    
    print(f"\nThursdays: {thursdays}")
    print(f"Saturdays: {saturdays}")
    
    print(f"\nTesting pairing bonus calculation:")
    
    test_thursday = date(2025, 6, 5)  # First Thursday
    empty_schedule = []
    
    for person_id in [1, 2, 3]:
        bonus = scheduler.calculate_pairing_bonus(person_id, test_thursday, empty_schedule, 2025, 6)
        print(f"Person {person_id} Thursday bonus (empty schedule): {bonus}")
        
        schedule_with_thursday = [(test_thursday, person_id, 'Perşembe')]
        test_saturday = date(2025, 6, 14)  # Different week Saturday
        
        saturday_bonus = scheduler.calculate_pairing_bonus(person_id, test_saturday, schedule_with_thursday, 2025, 6)
        print(f"Person {person_id} Saturday bonus (after Thursday): {saturday_bonus}")
        
        pairing_conflict = scheduler.needs_thursday_saturday_pairing(person_id, test_saturday, schedule_with_thursday, 2025, 6)
        print(f"Person {person_id} Saturday pairing conflict: {pairing_conflict}")
        
        print()

if __name__ == "__main__":
    debug_user_proven_detailed()
