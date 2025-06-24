#!/usr/bin/env python3
"""
Test schedule generation and display functionality
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler import DutyScheduler
from database import Database

def test_schedule_display():
    print("🔍 TESTING SCHEDULE GENERATION AND DISPLAY")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 10, 3, 4)
    print(f'✅ Schedule generated: {len(schedule)} days')
    
    display = scheduler.display_schedule(schedule, 2025, 10)
    print('✅ Schedule display generated successfully')
    print('First 5 lines:')
    print('\n'.join(display.split('\n')[:5]))
    
    consecutive = scheduler.detect_consecutive_assignments(schedule)
    print(f'\n✅ Consecutive detection: {len(consecutive)} consecutive assignments found')
    
    duty_counts = {}
    for date_obj, person_id, day_name in schedule:
        if person_id:
            person_name = scheduler.get_person_name(person_id)
            duty_counts[person_name] = duty_counts.get(person_name, 0) + 1
    
    print(f'\n✅ Personnel duty counts calculated:')
    for person, count in sorted(duty_counts.items()):
        print(f'   {person}: {count} nöbet')
    
    print(f'\n✅ Schedule display test complete')

if __name__ == "__main__":
    test_schedule_display()
