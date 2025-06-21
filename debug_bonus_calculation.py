#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date

def debug_bonus_calculation():
    print("=== DEBUGGING PAIRING BONUS CALCULATION ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    thursdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 3]
    fridays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 4]
    saturdays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 5]
    sundays = [(d, p) for d, p, _ in schedule if p and d.weekday() == 6]
    
    thursday_people = {}
    friday_people = {}
    saturday_people = {}
    sunday_people = {}
    
    for date_obj, person_id in thursdays:
        if person_id not in thursday_people:
            thursday_people[person_id] = []
        thursday_people[person_id].append(date_obj)
    
    for date_obj, person_id in fridays:
        if person_id not in friday_people:
            friday_people[person_id] = []
        friday_people[person_id].append(date_obj)
    
    for date_obj, person_id in saturdays:
        if person_id not in saturday_people:
            saturday_people[person_id] = []
        saturday_people[person_id].append(date_obj)
    
    for date_obj, person_id in sundays:
        if person_id not in sunday_people:
            sunday_people[person_id] = []
        sunday_people[person_id].append(date_obj)
    
    print("UNPAIRED THURSDAY ANALYSIS:")
    unpaired_thursday = None
    for thursday_date, thursday_person in thursdays:
        thursday_week = thursday_date.isocalendar()[1]
        paired = False
        for saturday_date, saturday_person in saturdays:
            saturday_week = saturday_date.isocalendar()[1]
            if (saturday_person == thursday_person and thursday_week != saturday_week):
                paired = True
                break
        
        if not paired:
            unpaired_thursday = (thursday_date, thursday_person)
            print(f"❌ UNPAIRED Thursday: Person {thursday_person} - {thursday_date} (W{thursday_week})")
            break
    
    print("\nUNPAIRED FRIDAY ANALYSIS:")
    unpaired_friday = None
    for friday_date, friday_person in fridays:
        friday_week = friday_date.isocalendar()[1]
        paired = False
        for sunday_date, sunday_person in sundays:
            sunday_week = sunday_date.isocalendar()[1]
            if (sunday_person == friday_person and friday_week != sunday_week):
                paired = True
                break
        
        if not paired:
            unpaired_friday = (friday_date, friday_person)
            print(f"❌ UNPAIRED Friday: Person {friday_person} - {friday_date} (W{friday_week})")
            break
    
    if unpaired_thursday:
        thursday_date, thursday_person = unpaired_thursday
        thursday_week = thursday_date.isocalendar()[1]
        
        print(f"\nTesting Saturday bonus for Person {thursday_person} (has Thursday {thursday_date}):")
        
        for saturday_date, saturday_person in saturdays:
            saturday_week = saturday_date.isocalendar()[1]
            if saturday_week != thursday_week:  # Different week
                bonus = scheduler.calculate_weekly_block_pairing_bonus(
                    thursday_person, saturday_date, 'Cumartesi', saturday_week,
                    thursday_people, friday_people, sunday_people, saturday_people, {}
                )
                print(f"  {saturday_date} (W{saturday_week}): bonus={bonus} (currently assigned to Person {saturday_person})")
    
    if unpaired_friday:
        friday_date, friday_person = unpaired_friday
        friday_week = friday_date.isocalendar()[1]
        
        print(f"\nTesting Sunday bonus for Person {friday_person} (has Friday {friday_date}):")
        
        for sunday_date, sunday_person in sundays:
            sunday_week = sunday_date.isocalendar()[1]
            if sunday_week != friday_week:  # Different week
                bonus = scheduler.calculate_weekly_block_pairing_bonus(
                    friday_person, sunday_date, 'Pazar', sunday_week,
                    thursday_people, friday_people, sunday_people, saturday_people, {}
                )
                print(f"  {sunday_date} (W{sunday_week}): bonus={bonus} (currently assigned to Person {sunday_person})")

if __name__ == "__main__":
    debug_bonus_calculation()
