#!/usr/bin/env python3
"""
Test that Mazeret rules are preserved and not overridden by new constraints
"""

from database import Database
from scheduler import DutyScheduler
from datetime import date

def test_mazeret_preservation():
    """Test that Mazeret tut=0/1 rules are preserved"""
    print("🔍 TESTING MAZERET RULE PRESERVATION")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    exemptions = scheduler.get_exemptions(2025, 6)
    print(f"Current exemptions in database for June 2025: {len(exemptions)}")
    
    for exemption in exemptions:
        person_id = exemption[0]  # person_id is first element
        exemption_date = exemption[1]  # date is second element  
        tut_value = exemption[2]  # tut is third element
        
        print(f"Person {person_id} on {exemption_date}: tut={tut_value}")
        
        if tut_value == 0:
            print(f"  ✓ Should be EXCLUDED from duty on {exemption_date}")
        elif tut_value == 1:
            print(f"  ✓ Should be FORCED to duty on {exemption_date}")
    
    schedule = scheduler.generate_schedule(2025, 6, 3, 4)  # June 2025 has exemptions
    
    print(f"\nGenerated schedule for June 2025: {len(schedule)} assignments")
    
    exemption_violations = 0
    
    for exemption in exemptions:
        person_id = exemption[0]  # person_id is first element
        exemption_date = exemption[1]  # date is second element  
        tut_value = exemption[2]  # tut is third element
        
        assigned_person = None
        for scheduled_date, scheduled_person, day_name in schedule:
            if scheduled_date == exemption_date:
                assigned_person = scheduled_person
                break
        
        if tut_value == 0:  # Should be excluded
            if assigned_person == person_id:
                exemption_violations += 1
                print(f"  ❌ VIOLATION: Person {person_id} assigned on {exemption_date} despite tut=0")
            else:
                print(f"  ✅ CORRECT: Person {person_id} excluded from {exemption_date} (tut=0)")
        
        elif tut_value == 1:  # Should be forced
            if assigned_person == person_id:
                print(f"  ✅ CORRECT: Person {person_id} forced to duty on {exemption_date} (tut=1)")
            else:
                exemption_violations += 1
                print(f"  ❌ VIOLATION: Person {person_id} NOT assigned on {exemption_date} despite tut=1")
    
    print(f"\nMAZERET RULE COMPLIANCE:")
    print(f"Total exemption violations: {exemption_violations}")
    
    if exemption_violations == 0:
        print("✅ PASS: All Mazeret rules preserved and respected")
    else:
        print("❌ FAIL: Mazeret rule violations detected")
    
    return exemption_violations == 0

if __name__ == "__main__":
    success = test_mazeret_preservation()
    print(f'\nMazeret preservation test: {"PASS" if success else "FAIL"}')
