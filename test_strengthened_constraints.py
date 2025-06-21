#!/usr/bin/env python3
"""
Test the strengthened Min/Max constraint enforcement
Verify that ABSOLUTE penalties prevent constraint violations
"""

from database import Database
from scheduler import DutyScheduler

def test_strengthened_constraints():
    """Test scheduler with strengthened constraint penalties"""
    print("🧪 TESTING STRENGTHENED MIN/MAX CONSTRAINT ENFORCEMENT")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_scenarios = [
        (3, 4, "Original user scenario - MUST be 3-4"),
        (3, 5, "User's example - MUST be 3-5"),
        (2, 6, "Wider range - MUST be 2-6"),
        (1, 3, "Lower range - MUST be 1-3"),
        (4, 7, "Higher range - MUST be 4-7")
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
                    print("✅ ABSOLUTE CONSTRAINTS RESPECTED")
                    results.append((description, True, min_actual, max_actual))
                else:
                    print("❌ ABSOLUTE CONSTRAINTS VIOLATED - ALGORITHM FAILURE")
                    if not min_constraint_ok:
                        print(f"   CRITICAL: Min violation: {min_actual} < {min_duties}")
                    if not max_constraint_ok:
                        print(f"   CRITICAL: Max violation: {max_actual} > {max_duties}")
                    results.append((description, False, min_actual, max_actual))
                
                print("Personnel duty distribution:")
                for person_id, count in sorted(person_counts.items()):
                    status = "✅" if min_duties <= count <= max_duties else "❌"
                    print(f"  Person {person_id}: {count} duties {status}")
            else:
                print("❌ NO DUTIES ASSIGNED")
                results.append((description, False, 0, 0))
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((description, False, 0, 0))
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS - ABSOLUTE CONSTRAINT ENFORCEMENT")
    print("=" * 60)
    
    success_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)
    
    for description, success, min_actual, max_actual in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}: Min={min_actual}, Max={max_actual}")
    
    print(f"\nOverall: {success_count}/{total_count} scenarios passed")
    
    if success_count == total_count:
        print("🎉 DYNAMIC MIN/MAX CONSTRAINTS WORKING PERFECTLY!")
        print("✅ Algorithm enforces ABSOLUTE Min/Max bounds")
        print("✅ No personnel can exceed maximum duties")
        print("✅ All personnel reach minimum duties")
        return True
    else:
        print("❌ CONSTRAINT VIOLATIONS DETECTED - ALGORITHM NEEDS MORE WORK")
        print("⚠️  Penalty values may need further strengthening")
        return False

if __name__ == "__main__":
    test_strengthened_constraints()
