#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from scheduler import DutyScheduler
from database import Database
from datetime import date, timedelta
import calendar

def debug_pairing_system():
    print("=== Debugging Mandatory Pairing System ===")
    
    try:
        db = Database()
        scheduler = DutyScheduler(db)
        
        print("\n1. Generating schedule for June 2025...")
        schedule = scheduler.generate_schedule(2025, 6)
        
        print(f"Generated {len(schedule)} days")
        
        print("\n2. Analyzing weekday distribution...")
        weekday_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                weekday = scheduled_date.weekday()
                weekday_counts[weekday] += 1
                if weekday in [3, 4, 5, 6]:
                    print(f"{weekday_names[weekday]} {scheduled_date}: Person {person_id} ({day_type})")
        
        print(f"\nWeekday distribution:")
        for i, count in weekday_counts.items():
            print(f"{weekday_names[i]}: {count}")
        
        print("\n3. Testing pairing bonus calculation...")
        mock_schedule = [
            (date(2025, 6, 5), 1, 'Perşembe'),
            (date(2025, 6, 14), 1, 'Cumartesi'),
        ]
        
        bonus = scheduler.calculate_pairing_bonus(1, date(2025, 6, 14), mock_schedule)
        print(f"Pairing bonus for person 1 on Saturday 14th: {bonus}")
        
        needs_pairing = scheduler.needs_thursday_saturday_pairing(1, date(2025, 6, 14), mock_schedule)
        print(f"Needs Thursday-Saturday pairing: {needs_pairing}")
        
        print("\n4. Testing priority score calculation...")
        personnel = scheduler.get_active_personnel()
        personnel_ids = [p[0] for p in personnel]
        stats = scheduler.get_personnel_duty_stats(personnel_ids)
        monthly_stats = scheduler.get_monthly_duty_stats(personnel_ids, 2025, 6)
        
        total_count = sum(s['count'] for s in stats.values())
        total_value = sum(s['total_value'] for s in stats.values())
        avg_count = total_count / len(personnel_ids) if personnel_ids else 0
        avg_value = total_value / len(personnel_ids) if personnel_ids else 0
        
        test_date = date(2025, 6, 14)
        for person_id in personnel_ids[:3]:
            try:
                priority = scheduler.calculate_priority_score(
                    person_id, stats, avg_count, avg_value, test_date,
                    mock_schedule, 'Cumartesi', monthly_stats, personnel_ids
                )
                print(f"Person {person_id} priority score for Saturday: {priority}")
            except Exception as e:
                print(f"Error calculating priority for person {person_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_pairing_system()
