#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_priority_scores():
    print("=== DEBUGGING PRIORITY SCORES VS PAIRING BONUSES ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    stats = scheduler.get_personnel_duty_stats(personnel_ids)
    
    total_count = sum(s['count'] for s in stats.values())
    total_value = sum(s['total_value'] for s in stats.values())
    avg_count = total_count / len(personnel_ids) if personnel_ids else 0
    avg_value = total_value / len(personnel_ids) if personnel_ids else 0
    
    print(f"Personnel stats:")
    for person_id in personnel_ids:
        person_stats = stats[person_id]
        priority_score = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
        print(f"  Person {person_id}: count={person_stats['count']}, value={person_stats['total_value']:.1f}, priority={priority_score:.1f}")
    
    print(f"\nAverage count: {avg_count:.1f}, Average value: {avg_value:.1f}")
    
    test_date = date(2025, 6, 14)  # Saturday
    partial_schedule = [(date(2025, 6, 5), 6, 'Perşembe')]  # Person 6 on Thursday
    
    print(f"\nTesting Saturday {test_date} assignment after Thursday assignment:")
    
    for person_id in personnel_ids[:5]:
        priority_score = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
        pairing_bonus = scheduler.calculate_pairing_bonus(person_id, test_date, partial_schedule, 2025, 6)
        total_score = priority_score + pairing_bonus
        
        print(f"  Person {person_id}: priority={priority_score:.1f}, bonus={pairing_bonus}, total={total_score:.1f}")
    
    priority_scores = [scheduler.calculate_priority_score(pid, stats, avg_count, avg_value) for pid in personnel_ids]
    max_priority_diff = max(priority_scores) - min(priority_scores)
    print(f"\nMax priority score difference: {max_priority_diff:.1f}")
    print(f"Current max pairing bonus: 3000")
    print(f"Bonus dominance ratio: {3000 / max_priority_diff:.1f}x" if max_priority_diff > 0 else "N/A")

if __name__ == "__main__":
    debug_priority_scores()
