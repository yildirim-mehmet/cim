#!/usr/bin/env python3
"""
Detailed debug of pairing system failures
"""

from datetime import date
from database import Database
from scheduler import DutyScheduler

def debug_pairing_detailed():
    """Debug why pairing system is failing"""
    print("🔍 DETAILED PAIRING SYSTEM DEBUG")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    year, month = 2025, 10
    schedule = scheduler.generate_schedule(year, month, 3, 4)
    
    person_assignments = {}
    for scheduled_date, person_id, day_name in schedule:
        if person_id:
            if person_id not in person_assignments:
                person_assignments[person_id] = []
            person_assignments[person_id].append((scheduled_date, day_name))
    
    print("\n📋 DETAILED PERSON ASSIGNMENTS:")
    for person_id, assignments in person_assignments.items():
        print(f"\nPerson {person_id}:")
        days = [day_name for _, day_name in assignments]
        
        for date_obj, day_name in assignments:
            print(f"  {date_obj} ({day_name})")
        
        has_saturday = 'Cumartesi' in days
        has_thursday = 'Perşembe' in days
        has_sunday = 'Pazar' in days
        has_monday = 'Pazartesi' in days
        
        print(f"  Pairing Status:")
        if has_saturday:
            print(f"    Saturday: ✓ | Thursday: {'✓' if has_thursday else '❌'}")
            if not has_thursday:
                print(f"    ❌ VIOLATION: Saturday without Thursday")
        
        if has_thursday:
            print(f"    Thursday: ✓ | Saturday: {'✓' if has_saturday else '❌'}")
            if not has_saturday:
                print(f"    ❌ VIOLATION: Thursday without Saturday")
        
        if has_sunday:
            print(f"    Sunday: ✓ | Monday: {'✓' if has_monday else '❌'}")
            if not has_monday:
                print(f"    ❌ VIOLATION: Sunday without Monday")
        
        if has_monday:
            print(f"    Monday: ✓ | Sunday: {'✓' if has_sunday else '❌'}")
            if not has_sunday:
                print(f"    ❌ VIOLATION: Monday without Sunday")
    
    print("\n🧪 TESTING CONSTRAINT METHODS:")
    
    saturday_violator = None
    for person_id, assignments in person_assignments.items():
        days = [day_name for _, day_name in assignments]
        if 'Cumartesi' in days and 'Perşembe' not in days:
            saturday_violator = person_id
            break
    
    if saturday_violator:
        print(f"\nTesting Person {saturday_violator} (has Saturday, no Thursday):")
        
        thursday_dates = []
        for scheduled_date, person_id, day_name in schedule:
            if day_name == 'Perşembe':
                thursday_dates.append(scheduled_date)
        
        if thursday_dates:
            test_thursday = thursday_dates[0]
            print(f"Testing Thursday assignment to {test_thursday}:")
            
            pairing_conflict = scheduler.needs_enhanced_day_pairing(
                saturday_violator, test_thursday, 'Perşembe', schedule, year, month)
            print(f"  Pairing conflict: {pairing_conflict}")
            
            pairing_bonus = scheduler.calculate_pairing_completion_bonus(
                saturday_violator, 'Perşembe', schedule, year, month)
            print(f"  Pairing bonus: {pairing_bonus}")
            
            already_assigned = any(
                scheduled_date == test_thursday and person_id == saturday_violator
                for scheduled_date, person_id, _ in schedule
            )
            print(f"  Already assigned to this date: {already_assigned}")

if __name__ == "__main__":
    debug_pairing_detailed()
