#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from scheduler import DutyScheduler
from database import Database
from datetime import date, timedelta
import calendar

def test_schedule_fix():
    print("=== Testing Schedule Generation Fix ===")
    
    try:
        db = Database()
        scheduler = DutyScheduler(db)
        
        print("\n1. Testing basic schedule generation...")
        schedule = scheduler.generate_schedule(2025, 6)
        
        assigned_days = sum(1 for _, person_id, _ in schedule if person_id is not None)
        total_days = len(schedule)
        
        print(f"Generated schedule: {assigned_days}/{total_days} days assigned")
        
        if assigned_days == 0:
            print("❌ No assignments made - investigating...")
            
            personnel = scheduler.get_active_personnel()
            print(f"Active personnel: {len(personnel)}")
            
            day_values = scheduler.get_day_values()
            print(f"Day values: {len(day_values)} entries")
            
            stats = scheduler.get_personnel_duty_stats([p[0] for p in personnel])
            print(f"Personnel stats: {len(stats)} entries")
            
            return False
        
        print("\n2. Analyzing assignments by weekday...")
        weekday_assignments = {}
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                weekday = scheduled_date.weekday()
                weekday_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday]
                if weekday_name not in weekday_assignments:
                    weekday_assignments[weekday_name] = []
                weekday_assignments[weekday_name].append((scheduled_date, person_id, day_type))
        
        for weekday, assignments in weekday_assignments.items():
            print(f"{weekday}: {len(assignments)} assignments")
            for scheduled_date, person_id, day_type in assignments[:3]:
                print(f"  {scheduled_date}: Person {person_id} ({day_type})")
        
        print("\n3. Testing mandatory pairing detection...")
        thursday_saturday_pairs = 0
        friday_sunday_pairs = 0
        
        person_thursdays = {}
        person_fridays = {}
        person_saturdays = {}
        person_sundays = {}
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                weekday = scheduled_date.weekday()
                if weekday == 3:
                    if person_id not in person_thursdays:
                        person_thursdays[person_id] = []
                    person_thursdays[person_id].append(scheduled_date)
                elif weekday == 4:
                    if person_id not in person_fridays:
                        person_fridays[person_id] = []
                    person_fridays[person_id].append(scheduled_date)
                elif weekday == 5:
                    if person_id not in person_saturdays:
                        person_saturdays[person_id] = []
                    person_saturdays[person_id].append(scheduled_date)
                elif weekday == 6:
                    if person_id not in person_sundays:
                        person_sundays[person_id] = []
                    person_sundays[person_id].append(scheduled_date)
        
        for person_id in person_thursdays:
            if person_id in person_saturdays:
                for thursday_date in person_thursdays[person_id]:
                    for saturday_date in person_saturdays[person_id]:
                        thursday_week = scheduler.get_week_start(thursday_date)
                        saturday_week = scheduler.get_week_start(saturday_date)
                        if thursday_week != saturday_week:
                            thursday_saturday_pairs += 1
                            print(f"✅ Thursday-Saturday pair: Person {person_id} - {thursday_date} & {saturday_date}")
                            break
        
        for person_id in person_fridays:
            if person_id in person_sundays:
                for friday_date in person_fridays[person_id]:
                    for sunday_date in person_sundays[person_id]:
                        friday_week = scheduler.get_week_start(friday_date)
                        sunday_week = scheduler.get_week_start(sunday_date)
                        if friday_week != sunday_week:
                            friday_sunday_pairs += 1
                            print(f"✅ Friday-Sunday pair: Person {person_id} - {friday_date} & {sunday_date}")
                            break
        
        print(f"\nPairing Results:")
        print(f"Thursday-Saturday pairs: {thursday_saturday_pairs}")
        print(f"Friday-Sunday pairs: {friday_sunday_pairs}")
        
        return assigned_days > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_schedule_fix()
    if success:
        print("\n🎉 SCHEDULE GENERATION WORKING!")
    else:
        print("\n❌ SCHEDULE GENERATION NEEDS FIXING!")
