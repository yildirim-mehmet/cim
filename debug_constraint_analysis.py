#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_constraint_analysis():
    print("=== DEBUGGING CONSTRAINT ANALYSIS - WHY PAIRINGS FAIL ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    thursday_date = date(2025, 6, 5)  # Week 23
    saturday_date = date(2025, 6, 14)  # Week 24 (different week)
    
    personnel = scheduler.get_active_personnel()
    print(f"Testing pairing for Thursday {thursday_date} and Saturday {saturday_date}")
    
    partial_schedule = [(thursday_date, 1, 'Perşembe')]  # Person 1 on Thursday
    
    print(f"\nTesting Saturday assignment for Person 1 after Thursday assignment:")
    
    person_id = 1
    
    ramazan_conflict = scheduler.is_ramazan_kurban_conflict(person_id, saturday_date, partial_schedule)
    print(f"  Ramazan/Kurban conflict: {ramazan_conflict}")
    
    thursday_saturday_conflict = scheduler.needs_thursday_saturday_pairing(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  Thursday-Saturday pairing conflict: {thursday_saturday_conflict}")
    
    friday_sunday_conflict = scheduler.needs_friday_sunday_pairing(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  Friday-Sunday pairing conflict: {friday_sunday_conflict}")
    
    sunday_monday_conflict = scheduler.needs_sunday_monday_pairing(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  Sunday-Monday pairing conflict: {sunday_monday_conflict}")
    
    consecutive_conflict = scheduler.has_consecutive_days_conflict(person_id, saturday_date, partial_schedule)
    print(f"  Consecutive days conflict: {consecutive_conflict}")
    
    repeated_day_conflict = scheduler.has_repeated_day_type_conflict(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  Repeated day type conflict: {repeated_day_conflict}")
    
    first_week_conflict = scheduler.check_first_week_pairing_requirements(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  First week pairing conflict: {first_week_conflict}")
    
    critical_day_conflict = scheduler.has_critical_day_same_person_conflict(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  Critical day same person conflict: {critical_day_conflict}")
    
    pairing_bonus = scheduler.calculate_pairing_bonus(person_id, saturday_date, partial_schedule, 2025, 6)
    print(f"  Pairing bonus: {pairing_bonus}")
    
    total_blocked = (ramazan_conflict or thursday_saturday_conflict or friday_sunday_conflict or 
                    sunday_monday_conflict or consecutive_conflict or repeated_day_conflict or 
                    first_week_conflict or critical_day_conflict)
    
    print(f"\n  TOTAL BLOCKED: {total_blocked}")
    print(f"  ELIGIBLE FOR PAIRING: {not total_blocked}")
    
    print(f"\nTesting other personnel for Saturday {saturday_date}:")
    for person_id, name, status in personnel[:3]:  # Test first 3 people
        if person_id == 1:
            continue  # Already tested
        
        conflicts = []
        if scheduler.is_ramazan_kurban_conflict(person_id, saturday_date, partial_schedule):
            conflicts.append("Ramazan/Kurban")
        if scheduler.needs_thursday_saturday_pairing(person_id, saturday_date, partial_schedule, 2025, 6):
            conflicts.append("Thursday-Saturday")
        if scheduler.needs_friday_sunday_pairing(person_id, saturday_date, partial_schedule, 2025, 6):
            conflicts.append("Friday-Sunday")
        if scheduler.needs_sunday_monday_pairing(person_id, saturday_date, partial_schedule, 2025, 6):
            conflicts.append("Sunday-Monday")
        if scheduler.has_consecutive_days_conflict(person_id, saturday_date, partial_schedule):
            conflicts.append("Consecutive")
        if scheduler.has_repeated_day_type_conflict(person_id, saturday_date, partial_schedule, 2025, 6):
            conflicts.append("Repeated-Day")
        if scheduler.check_first_week_pairing_requirements(person_id, saturday_date, partial_schedule, 2025, 6):
            conflicts.append("First-Week")
        if scheduler.has_critical_day_same_person_conflict(person_id, saturday_date, partial_schedule, 2025, 6):
            conflicts.append("Critical-Day")
        
        bonus = scheduler.calculate_pairing_bonus(person_id, saturday_date, partial_schedule, 2025, 6)
        
        print(f"  Person {person_id} ({name}): Conflicts={conflicts}, Bonus={bonus}, Eligible={len(conflicts)==0}")

if __name__ == "__main__":
    debug_constraint_analysis()
