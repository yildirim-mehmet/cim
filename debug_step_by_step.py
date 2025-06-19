#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
import calendar

def debug_step_by_step():
    print("=== STEP-BY-STEP DEBUGGING ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    stats = scheduler.get_personnel_duty_stats(personnel_ids)
    monthly_stats = scheduler.get_monthly_duty_stats(personnel_ids, 2025, 6)
    
    print(f"Personnel: {personnel_ids}")
    print(f"Initial monthly stats: {monthly_stats}")
    
    schedule = []
    
    test_dates = [
        (date(2025, 6, 7), 'Cumartesi'),   # Saturday - Person 2 gets this
        (date(2025, 6, 12), 'Perşembe'),  # Thursday - Person 2 gets this  
        (date(2025, 6, 19), 'Perşembe'),  # Thursday - Person 2 gets this again
        (date(2025, 6, 22), 'Pazar'),     # Sunday - Person 2 gets this too
    ]
    
    for test_date, day_type in test_dates:
        print(f"\n=== TESTING {test_date} ({day_type}) ===")
        
        current_monthly_stats = scheduler.get_current_schedule_monthly_stats(schedule, monthly_stats)
        print(f"Current monthly stats: {current_monthly_stats}")
        
        eligible_personnel = []
        for person_id in personnel_ids:
            print(f"\n--- Person {person_id} ---")
            
            has_conflict = scheduler.has_same_day_distribution_conflict(
                person_id, test_date, day_type, current_monthly_stats
            )
            print(f"Critical day conflict: {has_conflict}")
            
            if has_conflict:
                print(f"SKIPPED due to critical day conflict")
                continue
            
            priority_score = 100  # Dummy score
            eligible_personnel.append((person_id, priority_score))
            print(f"ELIGIBLE with score: {priority_score}")
        
        print(f"\nEligible personnel: {eligible_personnel}")
        
        if eligible_personnel:
            selected_person_id = 2  # This is what's happening in reality
            print(f"SELECTED: Person {selected_person_id}")
            schedule.append((test_date, selected_person_id, day_type))
        else:
            print("NO ONE ELIGIBLE - This should happen for Person 2 after first critical day!")
            schedule.append((test_date, None, day_type))
    
    print(f"\nFINAL SIMULATED SCHEDULE: {schedule}")

if __name__ == "__main__":
    debug_step_by_step()
