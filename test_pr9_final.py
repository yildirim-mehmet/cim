#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from scheduler import DutyScheduler
from database import Database
from datetime import date, timedelta
import calendar

def test_pr9_implementation():
    print("=== Testing PR #9 Final Implementation ===")
    
    try:
        db = Database()
        scheduler = DutyScheduler(db)
        
        print("\n1. Testing database connectivity...")
        personnel = scheduler.get_active_personnel()
        day_values = scheduler.get_day_values()
        print(f"Active personnel: {len(personnel)}")
        print(f"Day values: {len(day_values)}")
        
        if len(personnel) == 0:
            print("❌ No active personnel found - checking database...")
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Personel")
            total_personnel = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Personel WHERE Aktif = 1")
            active_personnel = cursor.fetchone()[0]
            print(f"Total personnel in DB: {total_personnel}")
            print(f"Active personnel in DB: {active_personnel}")
            conn.close()
            return False
        
        print("\n2. Testing enhanced schedule generation...")
        schedule = scheduler.generate_schedule(2025, 6)
        
        assigned_days = sum(1 for _, person_id, _ in schedule if person_id is not None)
        total_days = len(schedule)
        
        print(f"Generated schedule: {assigned_days}/{total_days} days assigned")
        
        if assigned_days == 0:
            print("❌ No assignments made")
            return False
        
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
        
        total_thursdays = len([d for d, p, _ in schedule if p and d.weekday() == 3])
        total_fridays = len([d for d, p, _ in schedule if p and d.weekday() == 4])
        
        thursday_saturday_rate = (thursday_saturday_pairs / max(total_thursdays, 1)) * 100
        friday_sunday_rate = (friday_sunday_pairs / max(total_fridays, 1)) * 100
        
        print(f"\n📊 PAIRING SUCCESS RATES:")
        print(f"Thursday-Saturday: {thursday_saturday_pairs}/{total_thursdays} = {thursday_saturday_rate:.1f}%")
        print(f"Friday-Sunday: {friday_sunday_pairs}/{total_fridays} = {friday_sunday_rate:.1f}%")
        
        print("\n4. Testing distribution balancing...")
        personnel_ids = [p[0] for p in personnel]
        monthly_stats = scheduler.get_monthly_duty_stats(personnel_ids, 2025, 6)
        
        distribution_conflicts = 0
        for person_id, day_types in monthly_stats.items():
            for day_type, count in day_types.items():
                if count > 1:
                    distribution_conflicts += 1
                    print(f"⚠️ Person {person_id} has {count} {day_type} duties")
        
        print(f"Distribution conflicts: {distribution_conflicts}")
        
        print("\n5. Testing manual change validation...")
        test_date = date(2025, 6, 15)
        warnings = scheduler.validate_manual_change(personnel_ids[0], test_date, 2025, 6)
        print(f"Manual change warnings: {len(warnings)}")
        
        success = (assigned_days > 0 and 
                  thursday_saturday_rate >= 50 and 
                  friday_sunday_rate >= 50)
        
        print(f"\n🎯 OVERALL SUCCESS: {'✅ PASS' if success else '❌ FAIL'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pr9_implementation()
    if success:
        print("\n🎉 PR #9 IMPLEMENTATION SUCCESSFUL!")
    else:
        print("\n❌ PR #9 IMPLEMENTATION NEEDS FIXES!")
