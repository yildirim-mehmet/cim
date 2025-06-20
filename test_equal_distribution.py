#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
import calendar

def test_equal_distribution():
    print("=== TESTING EQUAL DISTRIBUTION ACROSS MULTIPLE SCENARIOS ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    test_cases = [
        (2025, 2, 0, 10),  # February: 28 days
        (2025, 6, 0, 10),  # June: 30 days  
        (2025, 7, 0, 10),  # July: 31 days
        (2025, 2, 2, 6),   # February with constraints
        (2025, 6, 1, 5),   # June with tight constraints
    ]
    
    all_passed = True
    
    for year, month, min_nob, max_nob in test_cases:
        print(f"\nTesting {calendar.month_name[month]} {year} (min={min_nob}, max={max_nob})")
        schedule = scheduler.generate_schedule(year, month, min_nob, max_nob)
        
        person_counts = {}
        for _, person_id, _ in schedule:
            if person_id:
                person_counts[person_id] = person_counts.get(person_id, 0) + 1
        
        if person_counts:
            min_duties = min(person_counts.values())
            max_duties = max(person_counts.values())
            difference = max_duties - min_duties
            
            print(f"  Min duties: {min_duties}, Max duties: {max_duties}, Difference: {difference}")
            
            if difference > 1:
                print(f"  ❌ UNEQUAL DISTRIBUTION: Difference = {difference}")
                for person_id, count in sorted(person_counts.items(), key=lambda x: x[1]):
                    name = scheduler.get_person_name(person_id)
                    print(f"    {name}: {count} duties")
                all_passed = False
            else:
                print(f"  ✅ Fair distribution (max difference = {difference})")
        else:
            print("  ⚠️ No duties assigned")
    
    print(f"\n=== FINAL RESULT ===")
    if all_passed:
        print("🎉 ALL TESTS PASSED - Equal distribution working!")
    else:
        print("💥 SOME TESTS FAILED - Distribution needs improvement")
    
    return all_passed

def test_edge_cases():
    print("\n=== TESTING EDGE CASES ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    print("\nTesting February 2025 (reported issue scenario):")
    schedule = scheduler.generate_schedule(2025, 2, 0, 10)
    
    person_counts = {}
    for _, person_id, _ in schedule:
        if person_id:
            person_counts[person_id] = person_counts.get(person_id, 0) + 1
    
    if person_counts:
        min_duties = min(person_counts.values())
        max_duties = max(person_counts.values())
        difference = max_duties - min_duties
        
        print(f"February 2025 results:")
        print(f"  Min duties: {min_duties}, Max duties: {max_duties}, Difference: {difference}")
        
        print("\nDetailed breakdown:")
        for person_id, count in sorted(person_counts.items(), key=lambda x: x[1]):
            name = scheduler.get_person_name(person_id)
            print(f"  {name}: {count} duties")
        
        if difference <= 1:
            print("✅ February 2025 issue RESOLVED!")
            return True
        else:
            print("❌ February 2025 issue PERSISTS!")
            return False
    
    return False

if __name__ == "__main__":
    distribution_test = test_equal_distribution()
    edge_case_test = test_edge_cases()
    
    print(f"\n=== OVERALL RESULTS ===")
    print(f"Distribution test: {'✅ PASSED' if distribution_test else '❌ FAILED'}")
    print(f"Edge case test: {'✅ PASSED' if edge_case_test else '❌ FAILED'}")
    
    if distribution_test and edge_case_test:
        print("🎉 ALL TESTS PASSED - Equal distribution system working!")
    else:
        print("💥 SOME TESTS FAILED - Implementation needs review")
