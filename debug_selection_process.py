#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_selection_process():
    print("=== DEBUGGING SELECTION PROCESS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    stats = scheduler.get_personnel_duty_stats(personnel_ids)
    monthly_stats = scheduler.get_monthly_duty_stats(personnel_ids, 2025, 6)
    
    total_count = sum(s['count'] for s in stats.values())
    total_value = sum(s['total_value'] for s in stats.values())
    avg_count = total_count / len(personnel_ids) if personnel_ids else 0
    avg_value = total_value / len(personnel_ids) if personnel_ids else 0
    
    print(f"Personnel: {personnel_ids}")
    print(f"Average count: {avg_count}, Average value: {avg_value}")
    
    partial_schedule = [
        (date(2025, 6, 7), 2, 'Cumartesi'),   # Person 2 gets Saturday
        (date(2025, 6, 12), 2, 'Perşembe'),  # Person 2 gets Thursday
        (date(2025, 6, 19), 2, 'Perşembe'),  # Person 2 gets another Thursday
    ]
    
    print(f"\nPartial schedule: {partial_schedule}")
    
    test_date = date(2025, 6, 22)  # Sunday
    day_type = 'Pazar'
    
    print(f"\nTesting assignment for {test_date} ({day_type}):")
    
    for person_id in personnel_ids[:5]:  # Test first 5 people
        print(f"\n--- Person {person_id} ---")
        
        current_monthly_stats = scheduler.get_current_schedule_monthly_stats(partial_schedule, monthly_stats)
        
        has_conflict = scheduler.has_same_day_distribution_conflict(
            person_id, test_date, day_type, current_monthly_stats
        )
        print(f"Critical day conflict: {has_conflict}")
        
        if has_conflict:
            print(f"SKIPPED due to critical day conflict")
            continue
        
        priority_score = scheduler.calculate_priority_score(
            person_id, stats, avg_count, avg_value, test_date, 
            partial_schedule, day_type, current_monthly_stats, personnel_ids
        )
        
        pairing_bonus = scheduler.calculate_pairing_bonus(person_id, test_date, partial_schedule)
        
        print(f"Base priority score: {priority_score}")
        print(f"Pairing bonus: {pairing_bonus}")
        print(f"Total score: {priority_score + pairing_bonus}")
        
        if pairing_bonus > 0:
            print(f"MANDATORY PAIRING CANDIDATE with bonus!")

if __name__ == "__main__":
    debug_selection_process()
