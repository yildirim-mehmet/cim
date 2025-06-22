#!/usr/bin/env python3
"""
Test script for enhanced day priority rules and critical day restrictions
"""

from database import Database
from scheduler import DutyScheduler
from datetime import date
import calendar

def test_same_day_priority_system():
    """Test same-day priority ordering"""
    print("🎯 TESTING SAME-DAY PRIORITY SYSTEM")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    priority_order = ['Salı', 'Çarşamba', 'Pazartesi', 'Cuma', 'Pazar', 'Perşembe', 'Cumartesi']
    print("Expected priority order:", " > ".join(priority_order))
    
    schedule = scheduler.generate_schedule(2025, 6, 3, 4)
    
    same_day_assignments = {}
    for scheduled_date, person_id, day_name in schedule:
        if person_id:
            if person_id not in same_day_assignments:
                same_day_assignments[person_id] = {}
            if day_name not in same_day_assignments[person_id]:
                same_day_assignments[person_id][day_name] = 0
            same_day_assignments[person_id][day_name] += 1
    
    print("\nSame-day assignment analysis:")
    violations = 0
    for person_id, day_counts in same_day_assignments.items():
        for day_name, count in day_counts.items():
            if count > 1:
                priority = scheduler.SAME_DAY_PRIORITY.get(day_name, 8) if hasattr(scheduler, 'SAME_DAY_PRIORITY') else 8
                status = "✅" if priority <= 3 else "❌"
                print(f"  Person {person_id} - {day_name}: {count} times {status}")
                if priority > 3 and count > 1:
                    violations += 1
    
    print(f"\nSame-day priority violations: {violations}")
    return violations == 0

def test_critical_day_restrictions():
    """Test critical day same-value restrictions"""
    print("\n🚫 TESTING CRITICAL DAY RESTRICTIONS")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6, 3, 4)
    
    critical_days = ['Cuma', 'Cumartesi', 'Perşembe', 'Pazar']
    critical_assignments = {}
    
    for scheduled_date, person_id, day_name in schedule:
        if person_id and day_name in critical_days:
            if person_id not in critical_assignments:
                critical_assignments[person_id] = []
            critical_assignments[person_id].append(day_name)
    
    print("Critical day assignments:")
    violations = 0
    for person_id, days in critical_assignments.items():
        day_counts = {}
        for day in days:
            day_counts[day] = day_counts.get(day, 0) + 1
        
        person_violations = sum(1 for count in day_counts.values() if count > 1)
        violations += person_violations
        
        status = "✅" if person_violations == 0 else "❌"
        print(f"  Person {person_id}: {dict(day_counts)} {status}")
    
    print(f"\nCritical day violations: {violations}")
    return violations == 0

def test_enhanced_day_pairing():
    """Test enhanced day pairing rules"""
    print("\n🔗 TESTING ENHANCED DAY PAIRING")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6, 3, 4)
    
    pairing_success = 0
    pairing_total = 0
    
    person_assignments = {}
    for scheduled_date, person_id, day_name in schedule:
        if person_id:
            if person_id not in person_assignments:
                person_assignments[person_id] = []
            person_assignments[person_id].append((scheduled_date, day_name))
    
    print("Enhanced pairing analysis:")
    for person_id, assignments in person_assignments.items():
        saturdays = [d for d, n in assignments if n == 'Cumartesi']
        thursdays = [d for d, n in assignments if n == 'Perşembe']
        sundays = [d for d, n in assignments if n == 'Pazar']
        mondays = [d for d, n in assignments if n == 'Pazartesi']
        
        for sat_date in saturdays:
            pairing_total += 1
            sat_week = sat_date.isocalendar()[1]
            has_paired_thursday = any(thu_date.isocalendar()[1] != sat_week for thu_date in thursdays)
            if has_paired_thursday:
                pairing_success += 1
                print(f"  ✅ Person {person_id}: Saturday-Thursday paired")
            else:
                print(f"  ❌ Person {person_id}: Saturday without Thursday pair")
        
        for sun_date in sundays:
            pairing_total += 1
            sun_week = sun_date.isocalendar()[1]
            has_paired_monday = any(mon_date.isocalendar()[1] != sun_week for mon_date in mondays)
            if has_paired_monday:
                pairing_success += 1
                print(f"  ✅ Person {person_id}: Sunday-Monday paired")
            else:
                print(f"  ❌ Person {person_id}: Sunday without Monday pair")
    
    pairing_rate = (pairing_success / max(pairing_total, 1)) * 100
    print(f"\nEnhanced pairing success rate: {pairing_success}/{pairing_total} = {pairing_rate:.1f}%")
    return pairing_rate >= 80

def test_min_max_preservation():
    """Test that Min/Max constraints are still working"""
    print("\n⚖️ TESTING MIN/MAX CONSTRAINT PRESERVATION")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6, 3, 4)
    
    person_counts = {}
    for _, person_id, _ in schedule:
        if person_id:
            person_counts[person_id] = person_counts.get(person_id, 0) + 1
    
    if person_counts:
        min_duties = min(person_counts.values())
        max_duties = max(person_counts.values())
        
        within_bounds = all(3 <= count <= 4 for count in person_counts.values())
        status = "✅ PRESERVED" if within_bounds else "❌ BROKEN"
        
        print(f"Min/Max constraints (3-4): {status}")
        print(f"Actual distribution: Min={min_duties}, Max={max_duties}")
        
        for person_id, count in person_counts.items():
            bound_status = "✅" if 3 <= count <= 4 else "❌"
            print(f"  Person {person_id}: {count} duties {bound_status}")
        
        return within_bounds
    
    return False

if __name__ == "__main__":
    print("🚀 STARTING ENHANCED DAY PRIORITY RULES TEST")
    print("=" * 80)
    
    same_day_ok = test_same_day_priority_system()
    critical_day_ok = test_critical_day_restrictions()
    pairing_ok = test_enhanced_day_pairing()
    min_max_ok = test_min_max_preservation()
    
    print("\n" + "=" * 80)
    print("📊 ENHANCED DAY PRIORITY RULES TEST RESULTS")
    print("=" * 80)
    
    results = [
        ("Same-day priority system", same_day_ok),
        ("Critical day restrictions", critical_day_ok),
        ("Enhanced day pairing", pairing_ok),
        ("Min/Max constraint preservation", min_max_ok)
    ]
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("🎉 ALL ENHANCED DAY PRIORITY RULES WORKING PERFECTLY!")
    else:
        print("❌ SOME RULES NEED ADJUSTMENT")
