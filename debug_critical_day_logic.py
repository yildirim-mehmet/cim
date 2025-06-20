#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_critical_day_logic():
    print("=== DEBUGGING CRITICAL DAY LOGIC ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    stats = scheduler.get_personnel_duty_stats(personnel_ids)
    monthly_stats = scheduler.get_monthly_duty_stats(personnel_ids, 2025, 6)
    
    print(f"\nInitial monthly stats: {monthly_stats}")
    
    test_date = date(2025, 6, 22)  # Sunday
    day_type = 'Pazar'
    
    print(f"\nTesting critical day distribution for {test_date} ({day_type}):")
    
    for person_id in personnel_ids[:5]:  # Test first 5 people
        has_conflict = scheduler.has_same_day_distribution_conflict(
            person_id, test_date, day_type, monthly_stats
        )
        
        person_monthly = monthly_stats.get(person_id, {})
        critical_days = ['Cuma', 'Cumartesi', 'Pazar']
        critical_count = sum(person_monthly.get(day, 0) for day in critical_days)
        
        print(f"Person {person_id}:")
        print(f"  Monthly stats: {person_monthly}")
        print(f"  Critical day count: {critical_count}")
        print(f"  Has conflict: {has_conflict}")
        print()

if __name__ == "__main__":
    debug_critical_day_logic()
