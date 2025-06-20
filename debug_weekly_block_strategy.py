#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_weekly_block_strategy():
    print("=== DEBUGGING WEEKLY BLOCK STRATEGY ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    print("Testing weekly block pairing bonus calculation:")
    
    thursday_people = {1: [date(2025, 6, 5)]}  # Person 1 has Thursday
    friday_people = {2: [date(2025, 6, 6)]}    # Person 2 has Friday
    sunday_people = {3: [date(2025, 6, 8)]}    # Person 3 has Sunday
    saturday_people = {}
    monday_people = {}
    
    saturday_bonus = scheduler.calculate_weekly_block_pairing_bonus(
        1, date(2025, 6, 14), 'Cumartesi', 24,  # Different week Saturday
        thursday_people, friday_people, sunday_people, saturday_people, monday_people
    )
    print(f"Person 1 (has Thursday) Saturday bonus: {saturday_bonus}")
    
    sunday_bonus = scheduler.calculate_weekly_block_pairing_bonus(
        2, date(2025, 6, 15), 'Pazar', 24,  # Different week Sunday
        thursday_people, friday_people, sunday_people, saturday_people, monday_people
    )
    print(f"Person 2 (has Friday) Sunday bonus: {sunday_bonus}")
    
    monday_bonus = scheduler.calculate_weekly_block_pairing_bonus(
        3, date(2025, 6, 16), 'Pazartesi', 24,  # Different week Monday
        thursday_people, friday_people, sunday_people, saturday_people, monday_people
    )
    print(f"Person 3 (has Sunday) Monday bonus: {monday_bonus}")
    
    no_bonus = scheduler.calculate_weekly_block_pairing_bonus(
        4, date(2025, 6, 14), 'Cumartesi', 24,
        thursday_people, friday_people, sunday_people, saturday_people, monday_people
    )
    print(f"Person 4 (no assignments) Saturday bonus: {no_bonus}")
    
    print("\nTesting cross-week pairing completion:")
    
    schedule = [
        (date(2025, 6, 5), 1, 'Perşembe'),   # Thursday assigned
        (date(2025, 6, 6), 2, 'Cuma'),       # Friday assigned
        (date(2025, 6, 8), 3, 'Pazar'),      # Sunday assigned
        (date(2025, 6, 14), None, 'Cumartesi'),  # Unassigned Saturday
        (date(2025, 6, 15), None, 'Pazar'),      # Unassigned Sunday
        (date(2025, 6, 16), None, 'Pazartesi'),  # Unassigned Monday
    ]
    
    print("Before cross-week completion:")
    for date_obj, person, day_type in schedule:
        print(f"  {date_obj} ({day_type}): Person {person}")
    
    day_values = scheduler.get_day_values()
    stats = {1: {'count': 1, 'total_value': 0.9}, 
             2: {'count': 1, 'total_value': 1.4}, 
             3: {'count': 1, 'total_value': 1.6}}
    
    scheduler.complete_cross_week_pairings(
        schedule, thursday_people, friday_people, sunday_people, 
        saturday_people, monday_people, stats, day_values
    )
    
    print("\nAfter cross-week completion:")
    for date_obj, person, day_type in schedule:
        print(f"  {date_obj} ({day_type}): Person {person}")

if __name__ == "__main__":
    debug_weekly_block_strategy()
