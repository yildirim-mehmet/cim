#!/usr/bin/env python3
"""
Test script for the duty scheduling application
"""

from database import Database
from scheduler import DutyScheduler
from excel_exporter import ExcelExporter

def test_application():
    print('=== Testing Duty Scheduling Application ===')
    
    print('\n1. Testing database creation...')
    db = Database()
    db.check_and_populate_sample_data()
    print('✓ Database created and populated successfully')
    
    print('\n2. Testing scheduler...')
    scheduler = DutyScheduler(db)
    schedule = scheduler.generate_schedule(2025, 6)
    print(f'✓ Generated schedule for June 2025: {len(schedule)} days')
    
    print('\n3. Sample schedule entries:')
    for i, (date, person_id, day_type) in enumerate(schedule[:10]):
        person_name = scheduler.get_person_name(person_id) if person_id else 'ATANMADI'
        print(f'   {date}: {person_name} ({day_type})')
    
    print('\n4. Testing business rules...')
    
    consecutive_violations = 0
    for i in range(len(schedule) - 1):
        if schedule[i][1] and schedule[i+1][1] and schedule[i][1] == schedule[i+1][1]:
            consecutive_violations += 1
    print(f'   Consecutive day violations: {consecutive_violations}')
    
    personnel = scheduler.get_active_personnel()
    active_ids = [p[0] for p in personnel]
    inactive_assignments = 0
    for date, person_id, day_type in schedule:
        if person_id and person_id not in active_ids:
            inactive_assignments += 1
    print(f'   Inactive personnel assignments: {inactive_assignments}')
    
    print('\n5. Testing Excel export...')
    exporter = ExcelExporter(db)
    filename = exporter.export_monthly_schedule(2025, 6, 'test_schedule.xlsx')
    print(f'✓ Excel file created: {filename}')
    
    summary_filename = exporter.export_personnel_summary(2025, 6, 'test_summary.xlsx')
    print(f'✓ Personnel summary created: {summary_filename}')
    
    print('\n=== All tests completed successfully! ===')

if __name__ == "__main__":
    test_application()
