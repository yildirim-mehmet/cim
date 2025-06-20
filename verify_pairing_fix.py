#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def verify_pairing_fix():
    print("=== VERIFYING PAIRING FIX ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    thursdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 3]
    fridays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 4]
    saturdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 5]
    sundays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 6]
    
    print(f"\nCRITICAL DAYS:")
    print(f"Thursdays: {thursdays}")
    print(f"Fridays: {fridays}")
    print(f"Saturdays: {saturdays}")
    print(f"Sundays: {sundays}")
    
    thursday_saturday_pairs = 0
    friday_sunday_pairs = 0
    
    for thursday_date, thursday_person in thursdays:
        for saturday_date, saturday_person in saturdays:
            if (saturday_person == thursday_person and 
                scheduler.get_week_start(thursday_date) != scheduler.get_week_start(saturday_date)):
                thursday_saturday_pairs += 1
                print(f"✅ Pairing: Person {thursday_person} - Thursday {thursday_date} + Saturday {saturday_date}")
                break
    
    for friday_date, friday_person in fridays:
        for sunday_date, sunday_person in sundays:
            if (sunday_person == friday_person and 
                scheduler.get_week_start(friday_date) != scheduler.get_week_start(sunday_date)):
                friday_sunday_pairs += 1
                print(f"✅ Pairing: Person {friday_person} - Friday {friday_date} + Sunday {sunday_date}")
                break
    
    critical_assignments = {}
    for date_person_pair in thursdays + fridays + saturdays + sundays:
        person_id = date_person_pair[1]
        if person_id not in critical_assignments:
            critical_assignments[person_id] = 0
        critical_assignments[person_id] += 1
    
    print(f"\nCRITICAL DAY DISTRIBUTION:")
    for person_id, count in critical_assignments.items():
        print(f"Person {person_id}: {count} critical day assignments")
    
    thursday_saturday_rate = (thursday_saturday_pairs / max(len(thursdays), 1)) * 100
    friday_sunday_rate = (friday_sunday_pairs / max(len(fridays), 1)) * 100
    
    print(f"\nSUCCESS RATES:")
    print(f"Thursday-Saturday pairings: {thursday_saturday_pairs}/{len(thursdays)} = {thursday_saturday_rate:.1f}%")
    print(f"Friday-Sunday pairings: {friday_sunday_pairs}/{len(fridays)} = {friday_sunday_rate:.1f}%")
    
    max_critical = max(critical_assignments.values()) if critical_assignments else 0
    success = (thursday_saturday_rate >= 85 and friday_sunday_rate >= 85 and max_critical <= 2)
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Requirements {'met' if success else 'not met'}")
    
    return success

if __name__ == "__main__":
    verify_pairing_fix()
