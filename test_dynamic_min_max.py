#!/usr/bin/env python3
"""
Test dynamic Min/Max constraint enforcement
Verify that the scheduler respects any Min/Max values entered by user
"""

from database import Database
from scheduler import DutyScheduler

def test_dynamic_constraints():
    """Test scheduler with different Min/Max combinations"""
    print("🧪 TESTING DYNAMIC MIN/MAX CONSTRAINT ENFORCEMENT")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_scenarios = [
        (3, 4, "Original user scenario"),
        (3, 5, "User's example scenario"),
        (2, 6, "Wider range scenario"),
        (1, 3, "Lower range scenario"),
        (4, 7, "Higher range scenario")
    ]
    
    results = []
    
    for min_duties, max_duties, description in test_scenarios:
        print(f"\n🎯 Testing {description}: Min={min_duties}, Max={max_duties}")
        print("-" * 50)
        
        try:
            schedule = scheduler.generate_schedule(2025, 6, min_duties, max_duties)
            
            person_counts = {}
            for _, person_id, _ in schedule:
                if person_id:
                    person_counts[person_id] = person_counts.get(person_id, 0) + 1
            
            if person_counts:
                min_actual = min(person_counts.values())
                max_actual = max(person_counts.values())
                
                print(f"Expected: Min={min_duties}, Max={max_duties}")
                print(f"Actual:   Min={min_actual}, Max={max_actual}")
                
                min_constraint_ok = min_actual >= min_duties
                max_constraint_ok = max_actual <= max_duties
                
                if min_constraint_ok and max_constraint_ok:
                    print("✅ CONSTRAINTS RESPECTED")
                    results.append((description, True, min_actual, max_actual))
                else:
                    print("❌ CONSTRAINTS VIOLATED")
                    if not min_constraint_ok:
                        print(f"   Min violation: {min_actual} < {min_duties}")
                    if not max_constraint_ok:
                        print(f"   Max violation: {max_actual} > {max_duties}")
                    results.append((description, False, min_actual, max_actual))
                
                print(f"Personnel duty counts: {dict(sorted(person_counts.items()))}")
            else:
                print("❌ NO DUTIES ASSIGNED")
                results.append((description, False, 0, 0))
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((description, False, 0, 0))
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    success_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)
    
    for description, success, min_actual, max_actual in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}: Min={min_actual}, Max={max_actual}")
    
    print(f"\nOverall: {success_count}/{total_count} scenarios passed")
    
    if success_count == total_count:
        print("🎉 DYNAMIC MIN/MAX CONSTRAINTS WORKING PERFECTLY!")
        return True
    else:
        print("⚠️  SOME CONSTRAINT VIOLATIONS DETECTED")
        return False

if __name__ == "__main__":
    test_dynamic_constraints()
