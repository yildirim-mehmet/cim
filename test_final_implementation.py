#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def test_final_implementation():
    print("=== TESTING FINAL IMPLEMENTATION - BALANCED MANDATORY PAIRINGS ===")
    
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
    
    print(f"\nDETAILED PAIRING ANALYSIS:")
    
    thursday_saturday_pairs = 0
    for thursday_date, thursday_person in thursdays:
        thursday_week = thursday_date.isocalendar()[1]
        paired = False
        for saturday_date, saturday_person in saturdays:
            saturday_week = saturday_date.isocalendar()[1]
            if (saturday_person == thursday_person and thursday_week != saturday_week):
                thursday_saturday_pairs += 1
                print(f"✅ Thursday-Saturday: Person {thursday_person} - {thursday_date} (W{thursday_week}) + {saturday_date} (W{saturday_week})")
                paired = True
                break
        if not paired:
            print(f"❌ Thursday UNPAIRED: Person {thursday_person} - {thursday_date} (W{thursday_week})")
    
    friday_sunday_pairs = 0
    for friday_date, friday_person in fridays:
        friday_week = friday_date.isocalendar()[1]
        paired = False
        for sunday_date, sunday_person in sundays:
            sunday_week = sunday_date.isocalendar()[1]
            if (sunday_person == friday_person and friday_week != sunday_week):
                friday_sunday_pairs += 1
                print(f"✅ Friday-Sunday: Person {friday_person} - {friday_date} (W{friday_week}) + {sunday_date} (W{sunday_week})")
                paired = True
                break
        if not paired:
            print(f"❌ Friday UNPAIRED: Person {friday_person} - {friday_date} (W{friday_week})")
    
    sunday_monday_pairs = 0
    for sunday_date, sunday_person in sundays:
        sunday_week = sunday_date.isocalendar()[1]
        paired = False
        for monday_date, monday_person in mondays:
            monday_week = monday_date.isocalendar()[1]
            if (monday_person == sunday_person and sunday_week != monday_week):
                sunday_monday_pairs += 1
                print(f"✅ Sunday-Monday: Person {sunday_person} - {sunday_date} (W{sunday_week}) + {monday_date} (W{monday_week})")
                paired = True
                break
        if not paired:
            print(f"❌ Sunday UNPAIRED: Person {sunday_person} - {sunday_date} (W{sunday_week})")
    
    critical_assignments = {}
    for date_person_pair in fridays + saturdays + sundays:
        person_id = date_person_pair[1]
        if person_id not in critical_assignments:
            critical_assignments[person_id] = 0
        critical_assignments[person_id] += 1
    
    print(f"\nCRITICAL DAY DISTRIBUTION:")
    for person_id, count in critical_assignments.items():
        print(f"Person {person_id}: {count} critical day assignments")
    
    all_assignments = {}
    for date_obj, person_id, day_type in schedule:
        if person_id:
            if person_id not in all_assignments:
                all_assignments[person_id] = 0
            all_assignments[person_id] += 1
    
    print(f"\nTOTAL DUTY DISTRIBUTION:")
    for person_id, count in all_assignments.items():
        print(f"Person {person_id}: {count} total duties")
    
    thursday_saturday_rate = (thursday_saturday_pairs / max(len(thursdays), 1)) * 100
    friday_sunday_rate = (friday_sunday_pairs / max(len(fridays), 1)) * 100
    sunday_monday_rate = (sunday_monday_pairs / max(len(sundays), 1)) * 100
    
    print(f"\nSUCCESS RATES:")
    print(f"Thursday-Saturday pairings: {thursday_saturday_pairs}/{len(thursdays)} = {thursday_saturday_rate:.1f}%")
    print(f"Friday-Sunday pairings: {friday_sunday_pairs}/{len(fridays)} = {friday_sunday_rate:.1f}%")
    print(f"Sunday-Monday pairings: {sunday_monday_pairs}/{len(sundays)} = {sunday_monday_rate:.1f}%")
    
    max_critical_days = max(critical_assignments.values()) if critical_assignments else 0
    max_total_duties = max(all_assignments.values()) if all_assignments else 0
    min_total_duties = min(all_assignments.values()) if all_assignments else 0
    
    success = (thursday_saturday_rate >= 85 and friday_sunday_rate >= 85 and 
               sunday_monday_rate >= 85 and max_critical_days <= 3 and 
               (max_total_duties - min_total_duties) <= 2)
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Requirements {'met' if success else 'not met'}")
    print(f"Max critical days per person: {max_critical_days} (should be ≤ 3)")
    print(f"Duty distribution fairness: {min_total_duties}-{max_total_duties} (difference should be ≤ 2)")
    
    return success

if __name__ == "__main__":
    test_final_implementation()
