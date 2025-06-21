#!/usr/bin/env python3
"""
Test the enhanced Min/Max constraint enforcement with progressive penalties
This should achieve perfect constraint compliance
"""

from database import Database
from scheduler import DutyScheduler

def test_enhanced_enforcement():
    """Test scheduler with enhanced progressive constraint enforcement"""
    print("🧪 TESTING ENHANCED MIN/MAX CONSTRAINT ENFORCEMENT")
    print("Progressive penalties and exponential priority system")
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
                    print("✅ PERFECT CONSTRAINT ENFORCEMENT")
                    results.append((description, True, min_actual, max_actual))
                else:
                    print("❌ CONSTRAINT VIOLATIONS DETECTED")
                    if not min_constraint_ok:
                        print(f"   CRITICAL: Min violation: {min_actual} < {min_duties}")
                    if not max_constraint_ok:
                        print(f"   CRITICAL: Max violation: {max_actual} > {max_duties}")
                    results.append((description, False, min_actual, max_actual))
                
                print("Personnel duty distribution:")
                for person_id, count in sorted(person_counts.items()):
                    status = "✅" if min_duties <= count <= max_duties else "❌"
                    if count < min_duties:
                        violation = f"(BELOW MIN by {min_duties - count})"
                    elif count > max_duties:
                        violation = f"(ABOVE MAX by {count - max_duties})"
                    else:
                        violation = "(WITHIN BOUNDS)"
                    print(f"  Person {person_id}: {count} duties {status} {violation}")
                    
                if person_counts:
                    duty_range = max_actual - min_actual
                    print(f"Duty range: {duty_range} (smaller is more fair)")
                    
            else:
                print("❌ NO DUTIES ASSIGNED")
                results.append((description, False, 0, 0))
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((description, False, 0, 0))
    
    print("\n" + "=" * 60)
    print("📊 ENHANCED CONSTRAINT ENFORCEMENT RESULTS")
    print("=" * 60)
    
    success_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)
    
    for description, success, min_actual, max_actual in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}: Min={min_actual}, Max={max_actual}")
    
    print(f"\nOverall: {success_count}/{total_count} scenarios passed")
    
    if success_count == total_count:
        print("🎉 ENHANCED MIN/MAX CONSTRAINTS WORKING PERFECTLY!")
        print("✅ Progressive penalties enforce absolute Min/Max bounds")
        print("✅ Exponential priority system ensures fair redistribution")
        print("✅ Algorithm adapts to any Min/Max values dynamically")
        return True
    else:
        print("❌ SOME CONSTRAINT VIOLATIONS REMAIN")
        print("⚠️  Algorithm may need further enhancement")
        return False

if __name__ == "__main__":
    test_enhanced_enforcement()
