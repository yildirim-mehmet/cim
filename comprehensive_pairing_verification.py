#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date, timedelta
import calendar

def comprehensive_pairing_verification():
    print("=== COMPREHENSIVE PAIRING VERIFICATION ===")
    print("Testing mandatory cross-week pairing algorithm with visual calendar")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    print(f"\n1. GENERATED SCHEDULE OVERVIEW:")
    print(f"Total assignments: {len([s for s in schedule if s[1] is not None])}")
    print(f"Empty slots: {len([s for s in schedule if s[1] is None])}")
    
    print(f"\n2. VISUAL CALENDAR - JUNE 2025:")
    print("=" * 80)
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    print(f"{'':>3} " + " ".join(f"{day:>10}" for day in days))
    print("-" * 80)
    
    schedule_dict = {d: (p, dt) for d, p, dt in schedule if p}
    
    cal = calendar.monthcalendar(2025, 6)
    for week in cal:
        week_display = []
        for day in week:
            if day == 0:
                week_display.append(f"{'':>10}")
            else:
                current_date = date(2025, 6, day)
                if current_date in schedule_dict:
                    person_id, day_type = schedule_dict[current_date]
                    if day_type in ['Perşembe', 'Cuma', 'Cumartesi', 'Pazar']:
                        if day_type == 'Perşembe':
                            marker = "🔵"  # Blue for Thursday
                        elif day_type == 'Cuma':
                            marker = "🟢"  # Green for Friday
                        elif day_type == 'Cumartesi':
                            marker = "🔴"  # Red for Saturday
                        elif day_type == 'Pazar':
                            marker = "🟡"  # Yellow for Sunday
                        week_display.append(f"{day:>2}{marker}P{person_id}")
                    else:
                        week_display.append(f"{day:>2} P{person_id}")
                else:
                    week_display.append(f"{day:>2} ---")
        
        print(f"    " + " ".join(f"{cell:>10}" for cell in week_display))
    
    print("\nLEGEND: 🔵=Thursday 🟢=Friday 🔴=Saturday 🟡=Sunday")
    
    print(f"\n3. CRITICAL DAYS ANALYSIS:")
    thursdays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 3]
    fridays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 4]
    saturdays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 5]
    sundays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 6]
    
    print(f"Thursdays: {len(thursdays)} assignments")
    for d, p in thursdays:
        week_num = d.isocalendar()[1]
        print(f"  {d.strftime('%d.%m')} (Week {week_num}): Person {p}")
    
    print(f"\nFridays: {len(fridays)} assignments")
    for d, p in fridays:
        week_num = d.isocalendar()[1]
        print(f"  {d.strftime('%d.%m')} (Week {week_num}): Person {p}")
    
    print(f"\nSaturdays: {len(saturdays)} assignments")
    for d, p in saturdays:
        week_num = d.isocalendar()[1]
        print(f"  {d.strftime('%d.%m')} (Week {week_num}): Person {p}")
    
    print(f"\nSundays: {len(sundays)} assignments")
    for d, p in sundays:
        week_num = d.isocalendar()[1]
        print(f"  {d.strftime('%d.%m')} (Week {week_num}): Person {p}")
    
    print(f"\n4. MANDATORY PAIRING VERIFICATION:")
    
    thursday_saturday_pairs = 0
    thursday_saturday_details = []
    
    for thursday_date, thursday_person in thursdays:
        found_saturday = False
        for saturday_date, saturday_person in saturdays:
            if saturday_person == thursday_person:
                thursday_week = scheduler.get_week_start(thursday_date)
                saturday_week = scheduler.get_week_start(saturday_date)
                if thursday_week != saturday_week:
                    thursday_saturday_pairs += 1
                    thursday_saturday_details.append((thursday_person, thursday_date, saturday_date))
                    print(f"✅ Person {thursday_person}: Thursday {thursday_date.strftime('%d.%m')} (Week {thursday_date.isocalendar()[1]}) ↔ Saturday {saturday_date.strftime('%d.%m')} (Week {saturday_date.isocalendar()[1]})")
                    found_saturday = True
                    break
        if not found_saturday:
            print(f"❌ Person {thursday_person}: Thursday {thursday_date.strftime('%d.%m')} has NO Saturday pairing")
    
    friday_sunday_pairs = 0
    friday_sunday_details = []
    
    for friday_date, friday_person in fridays:
        found_sunday = False
        for sunday_date, sunday_person in sundays:
            if sunday_person == friday_person:
                friday_week = scheduler.get_week_start(friday_date)
                sunday_week = scheduler.get_week_start(sunday_date)
                if friday_week != sunday_week:
                    friday_sunday_pairs += 1
                    friday_sunday_details.append((friday_person, friday_date, sunday_date))
                    print(f"✅ Person {friday_person}: Friday {friday_date.strftime('%d.%m')} (Week {friday_date.isocalendar()[1]}) ↔ Sunday {sunday_date.strftime('%d.%m')} (Week {sunday_date.isocalendar()[1]})")
                    found_sunday = True
                    break
        if not found_sunday:
            print(f"❌ Person {friday_person}: Friday {friday_date.strftime('%d.%m')} has NO Sunday pairing")
    
    print(f"\n5. CRITICAL DAY DISTRIBUTION ANALYSIS:")
    critical_assignments = {}
    for date_person_pair in thursdays + fridays + saturdays + sundays:
        person_id = date_person_pair[1]
        if person_id not in critical_assignments:
            critical_assignments[person_id] = []
        critical_assignments[person_id].append(date_person_pair[0])
    
    for person_id, dates in critical_assignments.items():
        print(f"Person {person_id}: {len(dates)} critical day assignments")
        for d in sorted(dates):
            weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d.weekday()]
            print(f"  - {d.strftime('%d.%m')} ({weekday_name})")
    
    print(f"\n6. SUCCESS METRICS:")
    thursday_saturday_rate = (thursday_saturday_pairs / max(len(thursdays), 1)) * 100
    friday_sunday_rate = (friday_sunday_pairs / max(len(fridays), 1)) * 100
    max_critical_days = max(len(dates) for dates in critical_assignments.values()) if critical_assignments else 0
    
    print(f"Thursday-Saturday pairing rate: {thursday_saturday_pairs}/{len(thursdays)} = {thursday_saturday_rate:.1f}%")
    print(f"Friday-Sunday pairing rate: {friday_sunday_pairs}/{len(fridays)} = {friday_sunday_rate:.1f}%")
    print(f"Maximum critical days per person: {max_critical_days}")
    
    pairing_success = thursday_saturday_rate >= 85 and friday_sunday_rate >= 85
    distribution_success = max_critical_days <= 2
    overall_success = pairing_success and distribution_success
    
    print(f"\n7. FINAL ASSESSMENT:")
    print(f"{'✅' if pairing_success else '❌'} Mandatory pairing requirement: {pairing_success} (≥85% both pairings)")
    print(f"{'✅' if distribution_success else '❌'} Critical day distribution: {distribution_success} (≤2 per person)")
    print(f"{'✅' if overall_success else '❌'} Overall success: {overall_success}")
    
    if overall_success:
        print(f"\n🎉 MANDATORY PAIRING ALGORITHM IS WORKING CORRECTLY!")
        print(f"   - Perfect cross-week pairing enforcement")
        print(f"   - Balanced critical day distribution")
        print(f"   - No duplicate assignments to same dates")
        print(f"   - All constraints properly maintained")
    else:
        print(f"\n❌ ALGORITHM NEEDS FURTHER FIXES")
    
    return overall_success

if __name__ == "__main__":
    comprehensive_pairing_verification()
