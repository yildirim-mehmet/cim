#!/usr/bin/env python3
"""
Test the duty change warning system implementation
"""

from database import Database
from scheduler import DutyScheduler
from datetime import date

def test_duty_change_warning_system():
    """Test duty change warning system for non-Mazeret entries"""
    print("🔍 TESTING DUTY CHANGE WARNING SYSTEM")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_date = date(2025, 10, 15)
    test_person_id = 1
    new_person_id = 2
    
    is_mazeret, tut_value = scheduler.is_mazeret_entry(new_person_id, test_date, 2025, 10)
    print(f"Is Mazeret entry: {is_mazeret}, tut value: {tut_value}")
    
    if not is_mazeret:
        print(f"✅ Non-Mazeret entry detected - warning system would trigger")
    
    print(f"\nTesting constraint checking methods:")
    
    schedule = scheduler.generate_schedule(2025, 10, 3, 4)
    day_name = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'][test_date.weekday()]
    
    violations = scheduler.check_duty_change_constraints(new_person_id, test_date, day_name, schedule, 2025, 10)
    print(f"Constraint violations detected: {len(violations)}")
    
    for i, violation in enumerate(violations, 1):
        print(f"  {i}. {violation}")
    
    print(f"\n✅ Duty change warning system test complete")

if __name__ == "__main__":
    test_duty_change_warning_system()
