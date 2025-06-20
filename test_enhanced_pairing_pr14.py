#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def test_enhanced_pairing_pr14():
    print("=== TESTING ENHANCED PAIRING PR14 ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    print(f"\nGenerated schedule with {len(schedule)} days")
    
    thursdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 3]
    fridays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 4]
    saturdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 5]
    sundays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 6]
    mondays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 0]
    
    print(f"\nCRITICAL DAYS:")
    print(f"Thursdays: {thursdays}")
    print(f"Fridays: {fridays}")
    print(f"Saturdays: {saturdays}")
    print(f"Sundays: {sundays}")
    print(f"Mondays: {mondays}")
    
    thursday_saturday_pairs = 0
    for thursday_date, thursday_person in thursdays:
        for saturday_date, saturday_person in saturdays:
            if (saturday_person == thursday_person and 
                thursday_date.isocalendar()[1] != saturday_date.isocalendar()[1]):
                thursday_saturday_pairs += 1
                print(f"✅ Thursday-Saturday: Person {thursday_person} - {thursday_date} + {saturday_date}")
                break
    
    friday_sunday_pairs = 0
    for friday_date, friday_person in fridays:
        for sunday_date, sunday_person in sundays:
            if (sunday_person == friday_person and 
                friday_date.isocalendar()[1] != sunday_date.isocalendar()[1]):
                friday_sunday_pairs += 1
                print(f"✅ Friday-Sunday: Person {friday_person} - {friday_date} + {sunday_date}")
                break
    
    sunday_monday_pairs = 0
    for sunday_date, sunday_person in sundays:
        for monday_date, monday_person in mondays:
            if (monday_person == sunday_person and 
                sunday_date.isocalendar()[1] != monday_date.isocalendar()[1]):
                sunday_monday_pairs += 1
                print(f"✅ Sunday-Monday: Person {sunday_person} - {sunday_date} + {monday_date}")
                break
    
    critical_assignments = {}
    for date_person_pair in fridays + saturdays + sundays:
        person_id = date_person_pair[1]
        if person_id not in critical_assignments:
            critical_assignments[person_id] = 0
        critical_assignments[person_id] += 1
    
    print(f"\nCRITICAL DAY DISTRIBUTION:")
    for person_id, count in critical_assignments.items():
        print(f"Person {person_id}: {count} critical day assignments")
    
    thursday_saturday_rate = (thursday_saturday_pairs / max(len(thursdays), 1)) * 100
    friday_sunday_rate = (friday_sunday_pairs / max(len(fridays), 1)) * 100
    sunday_monday_rate = (sunday_monday_pairs / max(len(sundays), 1)) * 100
    
    print(f"\nSUCCESS RATES:")
    print(f"Thursday-Saturday pairings: {thursday_saturday_pairs}/{len(thursdays)} = {thursday_saturday_rate:.1f}%")
    print(f"Friday-Sunday pairings: {friday_sunday_pairs}/{len(fridays)} = {friday_sunday_rate:.1f}%")
    print(f"Sunday-Monday pairings: {sunday_monday_pairs}/{len(sundays)} = {sunday_monday_rate:.1f}%")
    
    max_critical_days = max(critical_assignments.values()) if critical_assignments else 0
    success = (thursday_saturday_rate >= 85 and friday_sunday_rate >= 85 and 
               sunday_monday_rate >= 85 and max_critical_days <= 2)
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Requirements {'met' if success else 'not met'}")
    print(f"Max critical days per person: {max_critical_days} (should be ≤ 2)")
    
    return success

if __name__ == "__main__":
    test_enhanced_pairing_pr14()
