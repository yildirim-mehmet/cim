#!/usr/bin/env python3
"""
Test multiple months for Sunday→Friday pairing stability
"""

from database import Database
from scheduler import DutyScheduler

def test_multi_month_stability():
    """Test Sunday→Friday pairing across multiple months"""
    print("🔍 TESTING MULTI-MONTH SUNDAY→FRIDAY PAIRING STABILITY")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    for month in [10, 11, 12]:
        print(f'\nTesting {2025}-{month:02d}')
        schedule = scheduler.generate_schedule(2025, month, 3, 4)
        
        sunday_people = set()
        friday_people = set()
        for date_obj, person_id, day_name in schedule:
            if person_id and day_name == 'Pazar':
                sunday_people.add(person_id)
            elif person_id and day_name == 'Cuma':
                friday_people.add(person_id)
        
        pairing_violations = 0
        for person_id in sunday_people:
            if person_id not in friday_people:
                pairing_violations += 1
                print(f'  ❌ Person {person_id}: Has Sunday but no Friday')
        
        print(f'Sunday assignments: {len(sunday_people)}')
        print(f'Friday assignments: {len(friday_people)}')
        print(f'Sunday→Friday pairing violations: {pairing_violations}')
        
        if pairing_violations == 0:
            print('✅ PASS: Sunday→Friday pairing working correctly')
        else:
            print('❌ FAIL: Sunday→Friday pairing violations detected')
        
        print('---')
    
    print("\n✅ MULTI-MONTH STABILITY TEST COMPLETE")

if __name__ == "__main__":
    test_multi_month_stability()
