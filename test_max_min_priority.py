#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
import calendar
from datetime import date
import random

def test_max_min_priority_scenarios():
    """Test Max-Min priority across multiple scenarios"""
    print("🧪 TESTING MAX-MIN PRIORITY SYSTEM")
    print("=== TESTING NORMAL SCENARIOS ===")
    
    db = Database()
    db.populate_sample_data()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Nobet')
    conn.commit()
    conn.close()
    
    scheduler = DutyScheduler(db)
    
    test_cases = [
        (2025, 1),   # January: 31 days
        (2025, 2),   # February: 28 days (reported issue)
        (2025, 6),   # June: 30 days (has holidays)
        (2025, 7),   # July: 31 days
    ]
    
    all_fair = True
    
    for year, month in test_cases:
        print(f'\nTesting {calendar.month_name[month]} {year}:')
        schedule = scheduler.generate_schedule(year, month)
        
        person_counts = {}
        for _, person_id, _ in schedule:
            if person_id:
                person_counts[person_id] = person_counts.get(person_id, 0) + 1
        
        if person_counts:
            min_duties = min(person_counts.values())
            max_duties = max(person_counts.values())
            difference = max_duties - min_duties
            
            print(f'  Min duties: {min_duties}, Max duties: {max_duties}, Difference: {difference}')
            
            if difference > 1:
                print(f'  ❌ MAX-MIN PRIORITY FAILED: Difference = {difference}')
                for person_id, count in sorted(person_counts.items(), key=lambda x: x[1]):
                    name = scheduler.get_person_name(person_id)
                    print(f'    {name}: {count} duties')
                all_fair = False
            else:
                print(f'  ✅ Max-Min priority working (difference = {difference})')
        else:
            print('  ⚠️ No duties assigned')
    
    return all_fair

def test_extreme_imbalance_with_max_min():
    """Test Max-Min priority under extreme existing duty imbalance"""
    print("\n=== TESTING EXTREME IMBALANCE WITH MAX-MIN PRIORITY ===")
    
    db = Database()
    db.populate_sample_data()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Nobet')
    
    for i in range(30):  # 30 existing duties
        person_id = random.choice([1, 2, 3])  # Only first 3 personnel get duties
        duty_date = date(2024, 12, random.randint(1, 28))
        cursor.execute('INSERT INTO Nobet (personelId, gunDegerId, ad, deger, tarih, kayit, degisiklik) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (person_id, 1, 'Test', 1.0, duty_date, '2024-12-01 00:00:00', 0))
    
    conn.commit()
    conn.close()
    
    scheduler = DutyScheduler(db)
    
    print('\nTesting February 2025 with extreme existing duty imbalance:')
    schedule = scheduler.generate_schedule(2025, 2)
    
    person_counts = {}
    for _, person_id, _ in schedule:
        if person_id:
            person_counts[person_id] = person_counts.get(person_id, 0) + 1
    
    if person_counts:
        min_duties = min(person_counts.values())
        max_duties = max(person_counts.values())
        difference = max_duties - min_duties
        
        print(f'  Min duties: {min_duties}, Max duties: {max_duties}, Difference: {difference}')
        
        print('\nDetailed breakdown:')
        for person_id, count in sorted(person_counts.items(), key=lambda x: x[1]):
            name = scheduler.get_person_name(person_id)
            print(f'  {name}: {count} duties')
        
        if difference > 1:
            print(f'❌ MAX-MIN PRIORITY STILL FAILS: Difference = {difference}')
            return False
        else:
            print(f'✅ Max-Min priority handles extreme imbalance (difference = {difference})')
            return True
    
    return False

def test_constraint_preservation():
    """Test that Max-Min priority preserves mazeret and consecutive day constraints"""
    print("\n=== TESTING CONSTRAINT PRESERVATION WITH MAX-MIN PRIORITY ===")
    
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    violations = []
    
    for i in range(len(schedule) - 1):
        date1, person1, _ = schedule[i]
        date2, person2, _ = schedule[i + 1]
        
        if person1 and person2 and person1 == person2:
            if (date2 - date1).days == 1:
                violations.append(f"Consecutive days: {person1} on {date1} and {date2}")
    
    ramazan_personnel = set()
    kurban_personnel = set()
    
    for scheduled_date, person_id, day_type in schedule:
        if person_id:
            if 'Ramazan' in day_type:
                ramazan_personnel.add(person_id)
            elif 'Kurban' in day_type:
                kurban_personnel.add(person_id)
    
    ramazan_kurban_conflicts = ramazan_personnel.intersection(kurban_personnel)
    if ramazan_kurban_conflicts:
        violations.append(f"Ramazan/Kurban conflicts: {ramazan_kurban_conflicts}")
    
    if violations:
        print("❌ CONSTRAINT VIOLATIONS DETECTED:")
        for violation in violations:
            print(f"  - {violation}")
        return False
    else:
        print("✅ All constraints preserved with Max-Min priority")
        return True

if __name__ == "__main__":
    print("🎯 TESTING MAX-MIN PRIORITY SYSTEM")
    
    normal_test = test_max_min_priority_scenarios()
    extreme_test = test_extreme_imbalance_with_max_min()
    constraint_test = test_constraint_preservation()
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Normal scenarios: {'✅ PASSED' if normal_test else '❌ FAILED'}")
    print(f"Extreme imbalance: {'✅ PASSED' if extreme_test else '❌ FAILED'}")
    print(f"Constraint preservation: {'✅ PASSED' if constraint_test else '❌ FAILED'}")
    
    if normal_test and extreme_test and constraint_test:
        print("🎉 ALL TESTS PASSED - Max-Min priority system working!")
    else:
        print("💥 SOME TESTS FAILED - Max-Min priority needs adjustment")
