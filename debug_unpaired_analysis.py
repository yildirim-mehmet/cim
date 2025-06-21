#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_unpaired_analysis():
    print("=== DEBUGGING UNPAIRED ASSIGNMENTS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    thursdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 3]
    fridays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 4]
    saturdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 5]
    sundays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 6]
    
    print("UNPAIRED THURSDAY ANALYSIS:")
    for thursday_date, thursday_person in thursdays:
        thursday_week = thursday_date.isocalendar()[1]
        paired = False
        for saturday_date, saturday_person in saturdays:
            saturday_week = saturday_date.isocalendar()[1]
            if (saturday_person == thursday_person and thursday_week != saturday_week):
                paired = True
                break
        
        if not paired:
            print(f"\n❌ UNPAIRED Thursday: Person {thursday_person} - {thursday_date} (W{thursday_week})")
            
            available_saturdays = []
            for saturday_date, saturday_person in saturdays:
                saturday_week = saturday_date.isocalendar()[1]
                if saturday_week != thursday_week:
                    available_saturdays.append((saturday_date, saturday_person, saturday_week))
            
            print(f"  Available Saturdays in different weeks:")
            for sat_date, sat_person, sat_week in available_saturdays:
                print(f"    {sat_date} (W{sat_week}): Person {sat_person}")
            
            print(f"  Checking constraints for Person {thursday_person}:")
            
            personnel = scheduler.get_active_personnel()
            personnel_ids = [p[0] for p in personnel]
            stats = scheduler.get_personnel_duty_stats(personnel_ids)
            
            for sat_date, sat_person, sat_week in available_saturdays:
                consecutive = scheduler.has_consecutive_days_conflict(thursday_person, sat_date, schedule)
                ramazan_kurban = scheduler.is_ramazan_kurban_conflict(thursday_person, sat_date, schedule)
                
                print(f"    {sat_date}: consecutive={consecutive}, ramazan_kurban={ramazan_kurban}")
    
    print("\nUNPAIRED FRIDAY ANALYSIS:")
    for friday_date, friday_person in fridays:
        friday_week = friday_date.isocalendar()[1]
        paired = False
        for sunday_date, sunday_person in sundays:
            sunday_week = sunday_date.isocalendar()[1]
            if (sunday_person == friday_person and friday_week != sunday_week):
                paired = True
                break
        
        if not paired:
            print(f"\n❌ UNPAIRED Friday: Person {friday_person} - {friday_date} (W{friday_week})")
            
            available_sundays = []
            for sunday_date, sunday_person in sundays:
                sunday_week = sunday_date.isocalendar()[1]
                if sunday_week != friday_week:
                    available_sundays.append((sunday_date, sunday_person, sunday_week))
            
            print(f"  Available Sundays in different weeks:")
            for sun_date, sun_person, sun_week in available_sundays:
                print(f"    {sun_date} (W{sun_week}): Person {sun_person}")
            
            print(f"  Checking constraints for Person {friday_person}:")
            
            for sun_date, sun_person, sun_week in available_sundays:
                consecutive = scheduler.has_consecutive_days_conflict(friday_person, sun_date, schedule)
                ramazan_kurban = scheduler.is_ramazan_kurban_conflict(friday_person, sun_date, schedule)
                
                print(f"    {sun_date}: consecutive={consecutive}, ramazan_kurban={ramazan_kurban}")

if __name__ == "__main__":
    debug_unpaired_analysis()
