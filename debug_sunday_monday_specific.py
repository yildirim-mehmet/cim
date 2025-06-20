#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_sunday_monday_specific():
    print("=== DEBUGGING SUNDAY-MONDAY SPECIFIC PAIRING ISSUES ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    sunday_dates = [date(2025, 6, 8), date(2025, 6, 22), date(2025, 6, 29)]  # Unpaired Sundays
    monday_dates = [date(2025, 6, 9), date(2025, 6, 23), date(2025, 6, 30)]  # Potential Monday pairs
    
    personnel = scheduler.get_active_personnel()
    
    for i, (sunday_date, monday_date) in enumerate(zip(sunday_dates, monday_dates)):
        print(f"\n=== TESTING SUNDAY-MONDAY PAIR {i+1}: {sunday_date} -> {monday_date} ===")
        
        partial_schedule = [(sunday_date, 9, 'Pazar')]  # Person 9 on Sunday
        
        print(f"Testing Monday {monday_date} assignment for Person 9 after Sunday {sunday_date}:")
        
        person_id = 9
        
        constraints = []
        if scheduler.is_ramazan_kurban_conflict(person_id, monday_date, partial_schedule):
            constraints.append("Ramazan/Kurban")
        if scheduler.needs_thursday_saturday_pairing(person_id, monday_date, partial_schedule, 2025, 6):
            constraints.append("Thursday-Saturday")
        if scheduler.needs_friday_sunday_pairing(person_id, monday_date, partial_schedule, 2025, 6):
            constraints.append("Friday-Sunday")
        if scheduler.needs_sunday_monday_pairing(person_id, monday_date, partial_schedule, 2025, 6):
            constraints.append("Sunday-Monday")
        if scheduler.has_consecutive_days_conflict(person_id, monday_date, partial_schedule):
            constraints.append("Consecutive")
        if scheduler.has_repeated_day_type_conflict(person_id, monday_date, partial_schedule, 2025, 6):
            constraints.append("Repeated-Day")
        if scheduler.check_first_week_pairing_requirements(person_id, monday_date, partial_schedule, 2025, 6):
            constraints.append("First-Week")
        if scheduler.has_critical_day_same_person_conflict(person_id, monday_date, partial_schedule, 2025, 6):
            constraints.append("Critical-Day")
        
        pairing_bonus = scheduler.calculate_pairing_bonus(person_id, monday_date, partial_schedule, 2025, 6)
        
        print(f"  Constraints blocking: {constraints}")
        print(f"  Pairing bonus: {pairing_bonus}")
        print(f"  ELIGIBLE: {len(constraints) == 0}")
        
        print(f"\n  Testing other personnel for Monday {monday_date}:")
        for person_id, name, status in personnel[:5]:
            if person_id == 9:
                continue
            
            other_constraints = []
            if scheduler.is_ramazan_kurban_conflict(person_id, monday_date, partial_schedule):
                other_constraints.append("Ramazan/Kurban")
            if scheduler.needs_thursday_saturday_pairing(person_id, monday_date, partial_schedule, 2025, 6):
                other_constraints.append("Thursday-Saturday")
            if scheduler.needs_friday_sunday_pairing(person_id, monday_date, partial_schedule, 2025, 6):
                other_constraints.append("Friday-Sunday")
            if scheduler.needs_sunday_monday_pairing(person_id, monday_date, partial_schedule, 2025, 6):
                other_constraints.append("Sunday-Monday")
            if scheduler.has_consecutive_days_conflict(person_id, monday_date, partial_schedule):
                other_constraints.append("Consecutive")
            if scheduler.has_repeated_day_type_conflict(person_id, monday_date, partial_schedule, 2025, 6):
                other_constraints.append("Repeated-Day")
            if scheduler.check_first_week_pairing_requirements(person_id, monday_date, partial_schedule, 2025, 6):
                other_constraints.append("First-Week")
            if scheduler.has_critical_day_same_person_conflict(person_id, monday_date, partial_schedule, 2025, 6):
                other_constraints.append("Critical-Day")
            
            other_bonus = scheduler.calculate_pairing_bonus(person_id, monday_date, partial_schedule, 2025, 6)
            
            print(f"    Person {person_id} ({name}): Constraints={other_constraints}, Bonus={other_bonus}, Eligible={len(other_constraints)==0}")

if __name__ == "__main__":
    debug_sunday_monday_specific()
