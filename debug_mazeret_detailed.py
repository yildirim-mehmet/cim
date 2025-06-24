#!/usr/bin/env python3
"""
Debug why Mazeret tut=1 assignments are failing
"""

from database import Database
from scheduler import DutyScheduler
from datetime import date

def debug_mazeret_detailed():
    """Debug why mandatory exemptions are not working"""
    print("🔍 DETAILED MAZERET DEBUG")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    personnel = scheduler.get_active_personnel()
    print(f"Active personnel: {len(personnel)}")
    for person_id, name, status in personnel:
        print(f"  Person {person_id}: {name} ({status})")
    
    exemptions = scheduler.get_exemptions(2025, 6)
    print(f"\nExemptions for June 2025: {len(exemptions)}")
    
    exemption_dict = {}
    for exemption in exemptions:
        person_id = exemption[0]
        exemption_date = exemption[1]
        tut_value = exemption[2]
        
        print(f"  Person {person_id} on {exemption_date}: tut={tut_value}")
        
        if person_id not in exemption_dict:
            exemption_dict[person_id] = {}
        exemption_dict[person_id][exemption_date] = tut_value
    
    for exemption in exemptions:
        person_id = exemption[0]
        tut_value = exemption[2]
        
        if tut_value == 1:  # Mandatory
            is_active = any(p[0] == person_id for p in personnel)
            print(f"\nPerson {person_id} (mandatory): Active = {is_active}")
            
            if not is_active:
                print(f"  ❌ PROBLEM: Person {person_id} is not active!")
    
    test_dates = [date(2025, 6, 15), date(2025, 6, 23)]
    
    for test_date in test_dates:
        print(f"\nTesting {test_date}:")
        
        for person_id in [5, 7]:  # The failing people
            if (person_id in exemption_dict and 
                test_date in exemption_dict[person_id] and 
                exemption_dict[person_id][test_date] == 1):
                print(f"  Person {person_id}: MANDATORY EXEMPTION DETECTED")
            else:
                print(f"  Person {person_id}: No mandatory exemption found")
                
                if person_id in exemption_dict:
                    print(f"    Exemption dates for Person {person_id}: {list(exemption_dict[person_id].keys())}")
                else:
                    print(f"    Person {person_id} not in exemption_dict")

if __name__ == "__main__":
    debug_mazeret_detailed()
