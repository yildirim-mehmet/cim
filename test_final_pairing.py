#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def test_final_pairing():
    print("=== FINAL PAIRING TEST ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    thursdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 3]
    fridays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 4]
    saturdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 5]
    sundays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 6]
    
    print(f"\nCRITICAL DAYS SUMMARY:")
    print(f"Thursdays ({len(thursdays)}): {[f'{d.day}.{d.month}→P{p}' for d, p in thursdays]}")
    print(f"Fridays ({len(fridays)}): {[f'{d.day}.{d.month}→P{p}' for d, p in fridays]}")
    print(f"Saturdays ({len(saturdays)}): {[f'{d.day}.{d.month}→P{p}' for d, p in saturdays]}")
    print(f"Sundays ({len(sundays)}): {[f'{d.day}.{d.month}→P{p}' for d, p in sundays]}")
    
    print(f"\nMANDATORY PAIRING VERIFICATION:")
    
    thursday_saturday_pairs = 0
    for thursday_date, thursday_person in thursdays:
        found_pair = False
        for saturday_date, saturday_person in saturdays:
            if (saturday_person == thursday_person and 
                scheduler.get_week_start(thursday_date) != scheduler.get_week_start(saturday_date)):
                print(f"✅ P{thursday_person}: Thu {thursday_date.day}.{thursday_date.month} ↔ Sat {saturday_date.day}.{saturday_date.month}")
                thursday_saturday_pairs += 1
                found_pair = True
                break
        if not found_pair:
            print(f"❌ P{thursday_person}: Thu {thursday_date.day}.{thursday_date.month} - NO Saturday pair")
    
    friday_sunday_pairs = 0
    for friday_date, friday_person in fridays:
        found_pair = False
        for sunday_date, sunday_person in sundays:
            if (sunday_person == friday_person and 
                scheduler.get_week_start(friday_date) != scheduler.get_week_start(sunday_date)):
                print(f"✅ P{friday_person}: Fri {friday_date.day}.{friday_date.month} ↔ Sun {sunday_date.day}.{sunday_date.month}")
                friday_sunday_pairs += 1
                found_pair = True
                break
        if not found_pair:
            print(f"❌ P{friday_person}: Fri {friday_date.day}.{friday_date.month} - NO Sunday pair")
    
    critical_assignments = {}
    for date_person_pair in thursdays + fridays + saturdays + sundays:
        person_id = date_person_pair[1]
        if person_id not in critical_assignments:
            critical_assignments[person_id] = 0
        critical_assignments[person_id] += 1
    
    print(f"\nCRITICAL DAY DISTRIBUTION:")
    for person_id in sorted(critical_assignments.keys()):
        count = critical_assignments[person_id]
        status = "✅" if count <= 2 else "❌"
        print(f"{status} Person {person_id}: {count} critical days")
    
    thursday_saturday_rate = (thursday_saturday_pairs / max(len(thursdays), 1)) * 100
    friday_sunday_rate = (friday_sunday_pairs / max(len(fridays), 1)) * 100
    max_critical = max(critical_assignments.values()) if critical_assignments else 0
    
    print(f"\nFINAL RESULTS:")
    print(f"Thursday-Saturday pairings: {thursday_saturday_pairs}/{len(thursdays)} = {thursday_saturday_rate:.1f}%")
    print(f"Friday-Sunday pairings: {friday_sunday_pairs}/{len(fridays)} = {friday_sunday_rate:.1f}%")
    print(f"Max critical days per person: {max_critical}")
    
    success = (thursday_saturday_rate >= 85 and friday_sunday_rate >= 85 and max_critical <= 2)
    
    print(f"\n{'🎉 SUCCESS' if success else '💥 FAILED'}: Requirements {'MET' if success else 'NOT MET'}")
    
    return success

if __name__ == "__main__":
    test_final_pairing()
