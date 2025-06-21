#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_reservation_analysis():
    print("=== DEBUGGING RESERVATION ANALYSIS ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    day_values = scheduler.get_day_values()
    holidays = scheduler.get_holidays(2025, 6)
    exemptions = scheduler.get_exemptions(2025, 6)
    
    personnel_ids = [p[0] for p in personnel]
    stats = scheduler.get_personnel_duty_stats(personnel_ids)
    
    total_count = sum(s['count'] for s in stats.values())
    total_value = sum(s['total_value'] for s in stats.values())
    avg_count = total_count / len(personnel_ids) if personnel_ids else 0
    avg_value = total_value / len(personnel_ids) if personnel_ids else 0
    
    holiday_dict = {date.fromisoformat(h[2]): h[0] for h in holidays}
    exemption_dict = {}
    for e in exemptions:
        if e[0] not in exemption_dict:
            exemption_dict[e[0]] = {}
        exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]
    
    last_month_duty_person = scheduler.get_last_month_last_duty(2025, 6)
    
    import calendar
    days_in_month = calendar.monthrange(2025, 6)[1]
    weeks = {}
    
    for day in range(1, days_in_month + 1):
        current_date = date(2025, 6, day)
        weekday = current_date.weekday()
        week_number = current_date.isocalendar()[1]
        
        if current_date in holiday_dict:
            day_value_id = holiday_dict[current_date]
        else:
            day_value_id = scheduler.get_weekday_id(weekday)
        
        day_info = day_values[day_value_id]
        day_name = day_info['name']
        
        day_data = (current_date, day_name, week_number, day_info)
        
        if week_number not in weeks:
            weeks[week_number] = []
        weeks[week_number].append(day_data)
    
    print("Weekly groups:")
    for week_num in sorted(weeks.keys()):
        print(f"  Week {week_num}: {len(weeks[week_num])} days")
        for day_data in weeks[week_num]:
            print(f"    {day_data[0]} ({day_data[1]})")
    
    reserved_assignments = {}
    
    print(f"\nTesting reservation process:")
    print(f"Personnel: {personnel_ids}")
    print(f"Stats: {[(pid, stats[pid]) for pid in personnel_ids]}")
    
    scheduler.reserve_mandatory_pairing_slots(weeks, personnel_ids, stats, avg_count, avg_value,
                                           exemption_dict, last_month_duty_person, reserved_assignments)
    
    print(f"\nReserved assignments: {len(reserved_assignments)}")
    for date_obj, (_, person_id, day_name) in reserved_assignments.items():
        print(f"  {date_obj} ({day_name}): Person {person_id}")
    
    all_critical_days = []
    for week_num, week_days in weeks.items():
        for day_data in week_days:
            if day_data[1] in ['Perşembe', 'Cuma', 'Cumartesi', 'Pazar', 'Pazartesi']:
                all_critical_days.append((day_data[0], day_data[1], week_num))
    
    print(f"\nAll critical days: {len(all_critical_days)}")
    unreserved_critical = []
    for date_obj, day_name, week_num in all_critical_days:
        if date_obj not in reserved_assignments:
            unreserved_critical.append((date_obj, day_name, week_num))
    
    print(f"Unreserved critical days: {len(unreserved_critical)}")
    for date_obj, day_name, week_num in unreserved_critical:
        print(f"  {date_obj} ({day_name}, W{week_num})")
    
    person_assignments = {}
    for _, person_id, day_name in reserved_assignments.values():
        if person_id not in person_assignments:
            person_assignments[person_id] = []
        person_assignments[person_id].append(day_name)
    
    print(f"\nReserved assignments per person:")
    for person_id in personnel_ids:
        assignments = person_assignments.get(person_id, [])
        print(f"  Person {person_id}: {len(assignments)} assignments - {assignments}")

if __name__ == "__main__":
    debug_reservation_analysis()
