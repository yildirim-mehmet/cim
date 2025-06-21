#!/usr/bin/env python3
"""
Test a redistribution-based Min/Max constraint enforcement
This will implement a post-processing step to redistribute duties
"""

from database import Database
from scheduler import DutyScheduler
from collections import defaultdict
import random

def redistribute_duties_to_meet_constraints(schedule, min_duties, max_duties, personnel_ids):
    """
    Post-process schedule to redistribute duties and meet Min/Max constraints
    """
    print(f"🔄 REDISTRIBUTING DUTIES: Min={min_duties}, Max={max_duties}")
    
    person_counts = defaultdict(int)
    person_assignments = defaultdict(list)
    
    for i, (date, person_id, day_type) in enumerate(schedule):
        if person_id:
            person_counts[person_id] += 1
            person_assignments[person_id].append(i)
    
    for person_id in personnel_ids:
        if person_id not in person_counts:
            person_counts[person_id] = 0
            person_assignments[person_id] = []
    
    print(f"Before redistribution: {dict(person_counts)}")
    
    over_max = [(pid, count) for pid, count in person_counts.items() if count > max_duties]
    under_min = [(pid, count) for pid, count in person_counts.items() if count < min_duties]
    
    print(f"Over max: {over_max}")
    print(f"Under min: {under_min}")
    
    max_iterations = 50
    iteration = 0
    
    while over_max and under_min and iteration < max_iterations:
        iteration += 1
        print(f"Redistribution iteration {iteration}")
        
        over_person, over_count = max(over_max, key=lambda x: x[1])
        excess = over_count - max_duties
        
        under_person, under_count = min(under_min, key=lambda x: x[1])
        deficit = min_duties - under_count
        
        if person_assignments[over_person]:
            transfer_idx = person_assignments[over_person][-1]  # Take last assignment
            
            schedule[transfer_idx] = (schedule[transfer_idx][0], under_person, schedule[transfer_idx][2])
            
            person_counts[over_person] -= 1
            person_counts[under_person] += 1
            
            person_assignments[over_person].remove(transfer_idx)
            person_assignments[under_person].append(transfer_idx)
            
            print(f"  Transferred duty from Person {over_person} to Person {under_person}")
            
            if person_counts[over_person] <= max_duties:
                over_max.remove((over_person, over_count))
            else:
                over_max = [(pid, person_counts[pid]) for pid, _ in over_max if pid == over_person] + \
                          [(pid, count) for pid, count in over_max if pid != over_person]
            
            if person_counts[under_person] >= min_duties:
                under_min.remove((under_person, under_count))
            else:
                under_min = [(pid, person_counts[pid]) for pid, _ in under_min if pid == under_person] + \
                           [(pid, count) for pid, count in under_min if pid != under_person]
            
            over_max = [(pid, count) for pid, count in person_counts.items() if count > max_duties]
            under_min = [(pid, count) for pid, count in person_counts.items() if count < min_duties]
        else:
            break
    
    print(f"After redistribution: {dict(person_counts)}")
    
    final_min = min(person_counts.values()) if person_counts else 0
    final_max = max(person_counts.values()) if person_counts else 0
    
    constraints_met = final_min >= min_duties and final_max <= max_duties
    print(f"Final range: Min={final_min}, Max={final_max}")
    print(f"Constraints met: {constraints_met}")
    
    return schedule, constraints_met

def test_redistribution_algorithm():
    """Test scheduler with post-processing redistribution"""
    print("🧪 TESTING REDISTRIBUTION-BASED MIN/MAX ENFORCEMENT")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_scenarios = [
        (3, 4, "Original user scenario - MUST be 3-4"),
        (3, 5, "User's example - MUST be 3-5"),
        (2, 6, "Wider range - MUST be 2-6")
    ]
    
    results = []
    
    for min_duties, max_duties, description in test_scenarios:
        print(f"\n🎯 Testing {description}: Min={min_duties}, Max={max_duties}")
        print("-" * 50)
        
        try:
            schedule = scheduler.generate_schedule(2025, 6, min_duties, max_duties)
            personnel = scheduler.get_active_personnel()
            personnel_ids = [p[0] for p in personnel]
            
            redistributed_schedule, constraints_met = redistribute_duties_to_meet_constraints(
                schedule, min_duties, max_duties, personnel_ids
            )
            
            person_counts = defaultdict(int)
            for _, person_id, _ in redistributed_schedule:
                if person_id:
                    person_counts[person_id] += 1
            
            if person_counts:
                min_actual = min(person_counts.values())
                max_actual = max(person_counts.values())
                
                print(f"Expected: Min={min_duties}, Max={max_duties}")
                print(f"Actual:   Min={min_actual}, Max={max_actual}")
                
                if constraints_met and min_actual >= min_duties and max_actual <= max_duties:
                    print("✅ REDISTRIBUTION SUCCESSFUL")
                    results.append((description, True, min_actual, max_actual))
                else:
                    print("❌ REDISTRIBUTION FAILED")
                    results.append((description, False, min_actual, max_actual))
            else:
                print("❌ NO DUTIES ASSIGNED")
                results.append((description, False, 0, 0))
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((description, False, 0, 0))
    
    print("\n" + "=" * 60)
    print("📊 REDISTRIBUTION ALGORITHM RESULTS")
    print("=" * 60)
    
    success_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)
    
    for description, success, min_actual, max_actual in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}: Min={min_actual}, Max={max_actual}")
    
    print(f"\nOverall: {success_count}/{total_count} scenarios passed")
    
    if success_count == total_count:
        print("🎉 REDISTRIBUTION ALGORITHM WORKING!")
        print("✅ Post-processing successfully enforces Min/Max constraints")
        return True
    else:
        print("❌ REDISTRIBUTION NEEDS MORE WORK")
        return False

if __name__ == "__main__":
    test_redistribution_algorithm()
