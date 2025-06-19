#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_pairing_failure():
    print("=== DEBUGGING PAIRING FAILURE ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    print("\n1. GENERATED SCHEDULE:")
    thursdays = []
    fridays = []
    saturdays = []
    sundays = []
    
    for scheduled_date, person_id, day_type in schedule:
        if person_id:
            weekday = scheduled_date.weekday()
            weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][weekday]
            print(f"{scheduled_date.strftime('%d.%m')} ({weekday_name}): Person {person_id} - {day_type}")
            
            if weekday == 3:
                thursdays.append((scheduled_date, person_id))
            elif weekday == 4:
                fridays.append((scheduled_date, person_id))
            elif weekday == 5:
                saturdays.append((scheduled_date, person_id))
            elif weekday == 6:
                sundays.append((scheduled_date, person_id))
    
    print(f"\n2. CRITICAL DAYS ANALYSIS:")
    print(f"Thursdays: {thursdays}")
    print(f"Fridays: {fridays}")
    print(f"Saturdays: {saturdays}")
    print(f"Sundays: {sundays}")
    
    print(f"\n3. PAIRING ANALYSIS:")
    for thursday_date, thursday_person in thursdays:
        found_saturday = False
        for saturday_date, saturday_person in saturdays:
            if saturday_person == thursday_person:
                thursday_week = scheduler.get_week_start(thursday_date)
                saturday_week = scheduler.get_week_start(saturday_date)
                if thursday_week != saturday_week:
                    print(f"✅ Person {thursday_person}: Thursday {thursday_date} paired with Saturday {saturday_date}")
                    found_saturday = True
                    break
        if not found_saturday:
            print(f"❌ Person {thursday_person}: Thursday {thursday_date} has NO Saturday pairing")
    
    for friday_date, friday_person in fridays:
        found_sunday = False
        for sunday_date, sunday_person in sundays:
            if sunday_person == friday_person:
                friday_week = scheduler.get_week_start(friday_date)
                sunday_week = scheduler.get_week_start(sunday_date)
                if friday_week != sunday_week:
                    print(f"✅ Person {friday_person}: Friday {friday_date} paired with Sunday {sunday_date}")
                    found_sunday = True
                    break
        if not found_sunday:
            print(f"❌ Person {friday_person}: Friday {friday_date} has NO Sunday pairing")
    
    print(f"\n4. CRITICAL DAY DISTRIBUTION:")
    critical_assignments = {}
    for date_person_pair in thursdays + fridays + saturdays + sundays:
        person_id = date_person_pair[1]
        if person_id not in critical_assignments:
            critical_assignments[person_id] = 0
        critical_assignments[person_id] += 1
    
    for person_id, count in critical_assignments.items():
        print(f"Person {person_id}: {count} critical day assignments")

if __name__ == "__main__":
    debug_pairing_failure()
