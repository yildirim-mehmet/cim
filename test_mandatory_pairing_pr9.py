#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from scheduler import DutyScheduler
from database import Database
from datetime import date, timedelta
import calendar

def test_mandatory_pairing_system():
    print("=== Testing Mandatory Pairing System (PR #9) ===")
    
    try:
        db = Database()
        scheduler = DutyScheduler(db)
        
        print("\n1. Testing method existence...")
        required_methods = [
            'get_monthly_duty_stats',
            'needs_thursday_saturday_pairing', 
            'needs_friday_sunday_pairing',
            'calculate_pairing_bonus',
            'has_same_day_distribution_conflict',
            'get_holiday_cycle_position',
            'validate_manual_change'
        ]
        
        for method in required_methods:
            assert hasattr(scheduler, method), f"Method {method} missing"
            print(f"✅ {method} method exists")
        
        print("\n2. Testing week calculation...")
        test_date = date(2025, 6, 15)  # Sunday
        week_start = scheduler.get_week_start(test_date)
        expected_week_start = date(2025, 6, 9)  # Monday
        assert week_start == expected_week_start, f"Week calculation failed: {week_start} != {expected_week_start}"
        print(f"✅ Week calculation: {test_date} -> week starts {week_start}")
        
        print("\n3. Testing mandatory pairing detection...")
        
        mock_schedule = [
            (date(2025, 6, 5), 1, 'Perşembe'),  # Thursday, week 1
            (date(2025, 6, 14), 1, 'Cumartesi'), # Saturday, week 2
        ]
        
        saturday_date = date(2025, 6, 14)
        needs_pairing = scheduler.needs_thursday_saturday_pairing(1, saturday_date, mock_schedule)
        print(f"✅ Thursday-Saturday pairing detection: {needs_pairing}")
        
        print("\n4. Testing pairing bonus...")
        bonus = scheduler.calculate_pairing_bonus(1, saturday_date, mock_schedule)
        print(f"✅ Pairing bonus: {bonus} points")
        
        print("\n5. Testing distribution balancing...")
        monthly_stats = {1: {'Perşembe': 1, 'Cumartesi': 0}}
        has_conflict = scheduler.has_same_day_distribution_conflict(1, date(2025, 6, 12), 'Perşembe', monthly_stats)
        print(f"✅ Distribution conflict detection: {has_conflict}")
        
        print("\n6. Testing holiday cycle...")
        personnel_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        cycle_pos = scheduler.get_holiday_cycle_position(1, personnel_ids)
        print(f"✅ Holiday cycle position for person 1: {cycle_pos}")
        
        print("\n7. Testing manual change validation...")
        warnings = scheduler.validate_manual_change(1, date(2025, 6, 15), 2025, 6)
        print(f"✅ Manual change validation: {len(warnings)} warnings")
        
        print("\n8. Testing enhanced schedule generation...")
        try:
            schedule = scheduler.generate_schedule(2025, 6)
            print(f"✅ Enhanced schedule generated: {len(schedule)} days")
        except Exception as e:
            print(f"❌ Schedule generation failed: {e}")
            return False
        
        thursday_saturday_pairs = 0
        friday_sunday_pairs = 0
        total_thursdays = 0
        total_fridays = 0
        
        person_thursdays = {}
        person_fridays = {}
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                weekday = scheduled_date.weekday()
                if weekday == 3:  # Thursday
                    total_thursdays += 1
                    if person_id not in person_thursdays:
                        person_thursdays[person_id] = []
                    person_thursdays[person_id].append(scheduled_date)
                elif weekday == 4:  # Friday
                    total_fridays += 1
                    if person_id not in person_fridays:
                        person_fridays[person_id] = []
                    person_fridays[person_id].append(scheduled_date)
                elif weekday == 5:  # Saturday
                    if person_id in person_thursdays:
                        for thursday_date in person_thursdays[person_id]:
                            thursday_week = scheduler.get_week_start(thursday_date)
                            saturday_week = scheduler.get_week_start(scheduled_date)
                            if thursday_week != saturday_week:
                                thursday_saturday_pairs += 1
                                break
                elif weekday == 6:  # Sunday
                    if person_id in person_fridays:
                        for friday_date in person_fridays[person_id]:
                            friday_week = scheduler.get_week_start(friday_date)
                            sunday_week = scheduler.get_week_start(scheduled_date)
                            if friday_week != sunday_week:
                                friday_sunday_pairs += 1
                                break
        
        thursday_saturday_rate = (thursday_saturday_pairs / max(total_thursdays, 1)) * 100
        friday_sunday_rate = (friday_sunday_pairs / max(total_fridays, 1)) * 100
        
        thursday_saturday_pairs = 0
        friday_sunday_pairs = 0
        total_thursdays = 0
        total_fridays = 0
        total_saturdays = 0
        total_sundays = 0
        
        person_thursdays = {}
        person_fridays = {}
        person_saturdays = {}
        person_sundays = {}
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                weekday = scheduled_date.weekday()
                if weekday == 3:
                    total_thursdays += 1
                    if person_id not in person_thursdays:
                        person_thursdays[person_id] = []
                    person_thursdays[person_id].append(scheduled_date)
                elif weekday == 4:
                    total_fridays += 1
                    if person_id not in person_fridays:
                        person_fridays[person_id] = []
                    person_fridays[person_id].append(scheduled_date)
                elif weekday == 5:
                    total_saturdays += 1
                    if person_id not in person_saturdays:
                        person_saturdays[person_id] = []
                    person_saturdays[person_id].append(scheduled_date)
                elif weekday == 6:
                    total_sundays += 1
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
                            break
        
        for person_id in person_fridays:
            if person_id in person_sundays:
                for friday_date in person_fridays[person_id]:
                    for sunday_date in person_sundays[person_id]:
                        friday_week = scheduler.get_week_start(friday_date)
                        sunday_week = scheduler.get_week_start(sunday_date)
                        if friday_week != sunday_week:
                            friday_sunday_pairs += 1
                            break
        
        print(f"\n📊 SCHEDULE ANALYSIS:")
        print(f"Total Thursdays: {total_thursdays}, Saturdays: {total_saturdays}")
        print(f"Total Fridays: {total_fridays}, Sundays: {total_sundays}")
        print(f"Thursday-Saturday pairs: {thursday_saturday_pairs}")
        print(f"Friday-Sunday pairs: {friday_sunday_pairs}")
        
        thursday_people_with_saturday = len([p for p in person_thursdays if p in person_saturdays])
        friday_people_with_sunday = len([p for p in person_fridays if p in person_sundays])
        
        thursday_saturday_rate = (thursday_saturday_pairs / max(thursday_people_with_saturday, 1)) * 100 if thursday_people_with_saturday > 0 else 0
        friday_sunday_rate = (friday_sunday_pairs / max(friday_people_with_sunday, 1)) * 100 if friday_people_with_sunday > 0 else 0
        
        print(f"\n📊 PAIRING SUCCESS RATES:")
        print(f"Thursday-Saturday: {thursday_saturday_pairs}/{thursday_people_with_saturday} = {thursday_saturday_rate:.1f}%")
        print(f"Friday-Sunday: {friday_sunday_pairs}/{friday_people_with_sunday} = {friday_sunday_rate:.1f}%")
        
        success = thursday_saturday_rate >= 85 and friday_sunday_rate >= 85
        
        print(f"\n🎯 TARGET: 85-90% pairing success rate")
        print(f"✅ RESULT: {'SUCCESS' if success else 'NEEDS IMPROVEMENT'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mandatory_pairing_system()
    if success:
        print("\n🎉 MANDATORY PAIRING SYSTEM IMPLEMENTATION SUCCESSFUL!")
    else:
        print("\n❌ MANDATORY PAIRING SYSTEM NEEDS REFINEMENT!")
