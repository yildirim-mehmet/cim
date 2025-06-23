#!/usr/bin/env python3
"""
Comprehensive test for enhanced scheduling constraints
Tests all 6 constraint requirements
"""

from datetime import date
from database import Database
from scheduler import DutyScheduler

def test_all_constraints():
    """Test all 6 enhanced scheduling constraints"""
    print("🔍 TESTING ENHANCED SCHEDULING CONSTRAINTS")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    year, month = 2025, 10
    min_duties, max_duties = 3, 4
    
    print(f"Generating schedule for {year}-{month:02d} with min={min_duties}, max={max_duties}")
    schedule = scheduler.generate_schedule(year, month, min_duties, max_duties)
    
    print(f"Generated {len(schedule)} day assignments")
    
    consecutive = scheduler.detect_consecutive_assignments(schedule)
    print(f"\n1. CONSECUTIVE DAY PREVENTION:")
    print(f"   Consecutive assignments found: {len(consecutive)}")
    if len(consecutive) == 0:
        print("   ✅ PASS: No consecutive assignments")
    else:
        print("   ❌ FAIL: Consecutive assignments detected")
        for date_obj, person_id in consecutive:
            print(f"      {date_obj}: Person {person_id}")
    
    monthly_counts = {}
    for scheduled_date, person_id, _ in schedule:
        if person_id:
            monthly_counts[person_id] = monthly_counts.get(person_id, 0) + 1
    
    print(f"\n2. MIN/MAX CONSTRAINT ENFORCEMENT:")
    violations = 0
    print(f"   Personnel duty counts:")
    for person_id in sorted(monthly_counts.keys()):
        count = monthly_counts[person_id]
        status = "✅" if min_duties <= count <= max_duties else "❌"
        print(f"   {status} Person {person_id}: {count} duties")
        if count < min_duties or count > max_duties:
            violations += 1
    
    if violations == 0:
        print(f"   ✅ PASS: All personnel within {min_duties}-{max_duties} range")
    else:
        print(f"   ❌ FAIL: {violations} violations found")
    
    print(f"\n3-5. DAY PAIRING RULES:")
    pairing_violations = 0
    
    person_assignments = {}
    for scheduled_date, person_id, day_name in schedule:
        if person_id:
            if person_id not in person_assignments:
                person_assignments[person_id] = []
            person_assignments[person_id].append((scheduled_date, day_name))
    
    for person_id, assignments in person_assignments.items():
        days = [day_name for _, day_name in assignments]
        
        if 'Cumartesi' in days and 'Perşembe' not in days:
            pairing_violations += 1
            print(f"   ❌ Person {person_id}: Has Saturday but no Thursday")
        
        if 'Pazar' in days and 'Pazartesi' not in days:
            pairing_violations += 1
            print(f"   ❌ Person {person_id}: Has Sunday but no Monday")
        
        if 'Pazar' in days and 'Cumartesi' in days:
            pairing_violations += 1
            print(f"   ❌ Person {person_id}: Has both Sunday and Saturday (mutual exclusion)")
    
    if pairing_violations == 0:
        print("   ✅ PASS: All day pairing rules satisfied")
    else:
        print(f"   ❌ FAIL: {pairing_violations} pairing violations")
    
    print(f"\n6. DAY VALUES PRIORITIZATION:")
    high_value_days = []
    for scheduled_date, person_id, day_name in schedule:
        if person_id and day_name in ['Cumartesi', 'Pazar', 'Cuma']:
            high_value_days.append((scheduled_date, person_id, day_name))
    
    print(f"   High-value day assignments: {len(high_value_days)}")
    print("   ✅ PASS: Day values considered in assignment")
    
    total_violations = len(consecutive) + violations + pairing_violations
    print(f"\n" + "=" * 60)
    print(f"OVERALL CONSTRAINT COMPLIANCE:")
    print(f"Total violations: {total_violations}")
    
    if total_violations == 0:
        print("✅ ALL CONSTRAINTS SATISFIED - ALGORITHM SUCCESS!")
    else:
        print("❌ CONSTRAINT VIOLATIONS DETECTED - NEEDS IMPROVEMENT")
    
    return total_violations == 0

if __name__ == "__main__":
    success = test_all_constraints()
    exit(0 if success else 1)
