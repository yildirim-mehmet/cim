#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_critical_day_detailed():
    print("=== DEBUGGING CRITICAL DAY DETAILED ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    monthly_stats = scheduler.get_monthly_duty_stats(personnel_ids, 2025, 6)
    
    print(f"Initial monthly stats: {monthly_stats}")
    
    partial_schedule = [
        (date(2025, 6, 7), 2, 'Cumartesi'),  # Person 2 gets Saturday
        (date(2025, 6, 12), 2, 'Perşembe'),  # Person 2 gets Thursday
    ]
    
    print(f"\nPartial schedule: {partial_schedule}")
    
    updated_stats = scheduler.get_current_schedule_monthly_stats(partial_schedule, monthly_stats)
    print(f"Updated monthly stats: {updated_stats}")
    
    test_date = date(2025, 6, 22)  # Sunday
    day_type = 'Pazar'
    
    print(f"\nTesting Person 2 for {test_date} ({day_type}):")
    
    has_conflict = scheduler.has_same_day_distribution_conflict(
        2, test_date, day_type, updated_stats
    )
    
    person_monthly = updated_stats.get(2, {})
    critical_days = ['Cuma', 'Cumartesi', 'Pazar']
    
    print(f"Person 2 monthly stats: {person_monthly}")
    print(f"Critical days check:")
    for critical_day in critical_days:
        count = person_monthly.get(critical_day, 0)
        print(f"  {critical_day}: {count}")
    
    print(f"Has conflict: {has_conflict}")
    print(f"Should be True because Person 2 already has Cumartesi")

if __name__ == "__main__":
    debug_critical_day_detailed()
