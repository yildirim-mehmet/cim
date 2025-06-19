#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_priority_scoring():
    print("=== DEBUGGING PRIORITY SCORING ===")
    
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
    
    test_date = date(2025, 6, 14)
    existing_schedule = [(date(2025, 6, 5), 1, 'Perşembe')]
    
    print(f"\nTesting Saturday {test_date} assignment with existing Thursday for person 1:")
    
    for person_id in personnel_ids[:3]:
        priority_score = scheduler.calculate_priority_score(
            person_id, stats, avg_count, avg_value, test_date, 
            existing_schedule, 'Cumartesi', monthly_stats, personnel_ids
        )
        
        person_stats = stats[person_id]
        count_diff = avg_count - person_stats['count']
        value_diff = avg_value - person_stats['total_value']
        base_score = count_diff * 2 + value_diff
        
        pairing_bonus = scheduler.calculate_pairing_bonus(person_id, test_date, existing_schedule)
        distribution_penalty = -50 if scheduler.has_same_day_distribution_conflict(person_id, test_date, 'Cumartesi', monthly_stats) else 0
        cycle_bonus = 100 if scheduler.should_prioritize_for_holiday_cycle(person_id, test_date, 'Cumartesi', personnel_ids, existing_schedule) else 0
        
        print(f"Person {person_id}:")
        print(f"  Base score: {base_score:.2f} (count_diff: {count_diff:.2f}, value_diff: {value_diff:.2f})")
        print(f"  Pairing bonus: {pairing_bonus}")
        print(f"  Distribution penalty: {distribution_penalty}")
        print(f"  Cycle bonus: {cycle_bonus}")
        print(f"  TOTAL: {priority_score:.2f}")
        print()

if __name__ == "__main__":
    debug_priority_scoring()
