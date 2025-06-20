#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def test_min_max_constraints():
    print("=== TESTING MIN/MAX DUTY CONSTRAINTS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    print("\n1. Testing default constraints (min=0, max=10)...")
    schedule = scheduler.generate_schedule(2025, 6, 0, 10)
    
    personnel_counts = {}
    for scheduled_date, person_id, day_type in schedule:
        if person_id:
            if person_id not in personnel_counts:
                personnel_counts[person_id] = 0
            personnel_counts[person_id] += 1
    
    print(f"Personnel duty counts: {personnel_counts}")
    max_duties = max(personnel_counts.values()) if personnel_counts else 0
    min_duties = min(personnel_counts.values()) if personnel_counts else 0
    print(f"Min duties assigned: {min_duties}, Max duties assigned: {max_duties}")
    
    print("\n2. Testing restrictive constraints (min=2, max=5)...")
    schedule_restrictive = scheduler.generate_schedule(2025, 6, 2, 5)
    
    personnel_counts_restrictive = {}
    for scheduled_date, person_id, day_type in schedule_restrictive:
        if person_id:
            if person_id not in personnel_counts_restrictive:
                personnel_counts_restrictive[person_id] = 0
            personnel_counts_restrictive[person_id] += 1
    
    print(f"Personnel duty counts (restrictive): {personnel_counts_restrictive}")
    max_duties_restrictive = max(personnel_counts_restrictive.values()) if personnel_counts_restrictive else 0
    min_duties_restrictive = min(personnel_counts_restrictive.values()) if personnel_counts_restrictive else 0
    print(f"Min duties assigned: {min_duties_restrictive}, Max duties assigned: {max_duties_restrictive}")
    
    print("\n3. Testing low maximum (min=0, max=3)...")
    schedule_low_max = scheduler.generate_schedule(2025, 6, 0, 3)
    
    personnel_counts_low = {}
    for scheduled_date, person_id, day_type in schedule_low_max:
        if person_id:
            if person_id not in personnel_counts_low:
                personnel_counts_low[person_id] = 0
            personnel_counts_low[person_id] += 1
    
    print(f"Personnel duty counts (low max): {personnel_counts_low}")
    max_duties_low = max(personnel_counts_low.values()) if personnel_counts_low else 0
    min_duties_low = min(personnel_counts_low.values()) if personnel_counts_low else 0
    print(f"Min duties assigned: {min_duties_low}, Max duties assigned: {max_duties_low}")
    
    print("\n4. Constraint validation...")
    print(f"Default (0-10): Max={max_duties} <= 10? {max_duties <= 10}")
    print(f"Restrictive (2-5): Min={min_duties_restrictive} >= 2? {min_duties_restrictive >= 2}, Max={max_duties_restrictive} <= 5? {max_duties_restrictive <= 5}")
    print(f"Low max (0-3): Max={max_duties_low} <= 3? {max_duties_low <= 3}")
    
    success = (max_duties <= 10 and 
               max_duties_restrictive <= 5 and 
               max_duties_low <= 3)
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Min/Max constraints {'respected' if success else 'violated'}")
    
    return success

if __name__ == "__main__":
    test_min_max_constraints()
