#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_constraint_blocking():
    print("=== DEBUGGING CONSTRAINT BLOCKING ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_date = date(2025, 6, 5)  # Thursday
    personnel = scheduler.get_active_personnel()
    
    print(f"Testing assignment for {test_date} (Thursday)")
    print(f"Available personnel: {[p[0] for p in personnel]}")
    
    for person_id, name, status in personnel:
        print(f"\nTesting Person {person_id} ({name}):")
        
        empty_schedule = []
        
        ramazan_conflict = scheduler.is_ramazan_kurban_conflict(person_id, test_date, empty_schedule)
        print(f"  Ramazan/Kurban conflict: {ramazan_conflict}")
        
        thursday_saturday_conflict = scheduler.needs_thursday_saturday_pairing(person_id, test_date, empty_schedule, 2025, 6)
        print(f"  Thursday-Saturday pairing conflict: {thursday_saturday_conflict}")
        
        friday_sunday_conflict = scheduler.needs_friday_sunday_pairing(person_id, test_date, empty_schedule, 2025, 6)
        print(f"  Friday-Sunday pairing conflict: {friday_sunday_conflict}")
        
        consecutive_conflict = scheduler.has_consecutive_days_conflict(person_id, test_date, empty_schedule)
        print(f"  Consecutive days conflict: {consecutive_conflict}")
        
        pairing_bonus = scheduler.calculate_pairing_bonus(person_id, test_date, empty_schedule, 2025, 6)
        print(f"  Pairing bonus: {pairing_bonus}")
        
        eligible = not (ramazan_conflict or thursday_saturday_conflict or friday_sunday_conflict or consecutive_conflict)
        print(f"  ELIGIBLE: {eligible}")

if __name__ == "__main__":
    debug_constraint_blocking()
