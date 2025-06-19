#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database

def test_display_schedule():
    print("=== TESTING DISPLAY_SCHEDULE FUNCTION ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    display_output = scheduler.display_schedule(schedule, 2025, 6)
    
    print("Display Schedule Output:")
    print("=" * 50)
    print(display_output)
    print("=" * 50)
    
    lines = display_output.split('\n')
    print(f"\nTotal lines in output: {len(lines)}")
    
    has_header = any("Nöbet Listesi" in line for line in lines)
    has_personnel_summary = any("Personel Nöbet Özeti" in line for line in lines)
    has_duty_assignments = any("[" in line and "]" in line for line in lines)
    
    print(f"Has header: {has_header}")
    print(f"Has personnel summary: {has_personnel_summary}")
    print(f"Has duty count brackets: {has_duty_assignments}")
    
    print("\nSample assignment lines:")
    for line in lines:
        if "[" in line and "]" in line and ":" in line:
            print(f"  {line}")
            break
    
    print("\nSample summary lines:")
    for i, line in enumerate(lines):
        if "Personel Nöbet Özeti" in line and i + 2 < len(lines):
            print(f"  {lines[i+2]}")
            break

if __name__ == "__main__":
    test_display_schedule()
