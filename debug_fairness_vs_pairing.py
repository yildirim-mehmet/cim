#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_fairness_vs_pairing():
    print("=== DEBUGGING FAIRNESS VS PAIRING CONFLICT ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    personnel_ids = [p[0] for p in personnel]
    stats = scheduler.get_personnel_duty_stats(personnel_ids)
    
    total_count = sum(s['count'] for s in stats.values())
    total_value = sum(s['total_value'] for s in stats.values())
    avg_count = total_count / len(personnel_ids) if personnel_ids else 0
    avg_value = total_value / len(personnel_ids) if personnel_ids else 0
    
    print(f"Personnel duty statistics:")
    priority_scores = []
    for person_id in personnel_ids:
        person_stats = stats[person_id]
        priority_score = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
        priority_scores.append(priority_score)
        print(f"  Person {person_id}: count={person_stats['count']}, value={person_stats['total_value']:.1f}, priority={priority_score:.1f}")
    
    max_priority_diff = max(priority_scores) - min(priority_scores)
    print(f"\nMax priority difference: {max_priority_diff:.1f}")
    print(f"Current pairing bonus: 1000")
    print(f"Bonus dominance ratio: {1000 / max_priority_diff:.1f}x" if max_priority_diff > 0 else "N/A")
    
    test_thursday = date(2025, 6, 5)
    test_saturday = date(2025, 6, 14)
    
    print(f"\nTesting Thursday {test_thursday} -> Saturday {test_saturday} pairing:")
    
    for person_id in personnel_ids[:3]:
        schedule_with_thursday = [(test_thursday, person_id, 'Perşembe')]
        
        print(f"\nIf Person {person_id} gets Thursday:")
        
        saturday_bonus = scheduler.calculate_pairing_bonus(person_id, test_saturday, schedule_with_thursday, 2025, 6)
        saturday_priority = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
        saturday_total = saturday_priority + saturday_bonus
        
        print(f"  Person {person_id} Saturday: priority={saturday_priority:.1f}, bonus={saturday_bonus}, total={saturday_total:.1f}")
        
        for other_id in personnel_ids[:3]:
            if other_id != person_id:
                other_bonus = scheduler.calculate_pairing_bonus(other_id, test_saturday, schedule_with_thursday, 2025, 6)
                other_priority = scheduler.calculate_priority_score(other_id, stats, avg_count, avg_value)
                other_total = other_priority + other_bonus
                
                print(f"  Person {other_id} Saturday: priority={other_priority:.1f}, bonus={other_bonus}, total={other_total:.1f}")
                
                if other_total > saturday_total:
                    print(f"    ❌ Person {other_id} would be selected over Person {person_id} (diff: {other_total - saturday_total:.1f})")
                else:
                    print(f"    ✅ Person {person_id} would be selected (diff: {saturday_total - other_total:.1f})")

if __name__ == "__main__":
    debug_fairness_vs_pairing()
