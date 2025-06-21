#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_selection_priority():
    print("=== DEBUGGING SELECTION PRIORITY IN WEEKLY BLOCK STRATEGY ===")
    
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
    for person_id in personnel_ids:
        person_stats = stats[person_id]
        priority_score = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
        print(f"  Person {person_id}: count={person_stats['count']}, value={person_stats['total_value']:.1f}, priority={priority_score:.1f}")
    
    thursday_people = {1: [date(2025, 6, 5)]}
    friday_people = {}
    sunday_people = {}
    saturday_people = {}
    monday_people = {}
    
    test_saturday = date(2025, 6, 14)  # Different week Saturday
    
    print(f"\nTesting Saturday assignment {test_saturday} (week 24):")
    print(f"Person 1 has Thursday 2025-06-05 (week 23)")
    
    for person_id in personnel_ids[:5]:  # Test first 5 people
        base_priority = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
        
        pairing_bonus = scheduler.calculate_weekly_block_pairing_bonus(
            person_id, test_saturday, 'Cumartesi', 24,
            thursday_people, friday_people, sunday_people, saturday_people, monday_people
        )
        
        total_score = base_priority + pairing_bonus
        
        print(f"  Person {person_id}: base={base_priority:.1f}, bonus={pairing_bonus}, total={total_score:.1f}")
        
        if person_id == 1:
            print(f"    ✅ Person 1 should win with {total_score:.1f} points (3000 bonus)")
    
    print(f"\nTesting Person 1 eligibility for Saturday {test_saturday}:")
    
    schedule = [(date(2025, 6, 5), 1, 'Perşembe')]  # Person 1 has Thursday
    week_assignments = {}  # Empty for different week
    exemption_dict = {}
    last_month_duty_person = None
    
    eligible = scheduler.is_person_eligible_for_weekly_block(
        1, test_saturday, 'Cumartesi', 24, schedule, week_assignments,
        exemption_dict, last_month_duty_person, thursday_people, friday_people,
        sunday_people, saturday_people, monday_people
    )
    
    print(f"  Person 1 eligible for Saturday: {eligible}")
    
    consecutive = scheduler.has_consecutive_days_conflict(1, test_saturday, schedule)
    print(f"  Consecutive days conflict: {consecutive}")
    
    ramazan_kurban = scheduler.is_ramazan_kurban_conflict(1, test_saturday, schedule)
    print(f"  Ramazan-Kurban conflict: {ramazan_kurban}")

if __name__ == "__main__":
    debug_selection_priority()
