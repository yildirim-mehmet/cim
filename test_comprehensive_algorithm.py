#!/usr/bin/env python3
"""
Test comprehensive scheduling algorithm with all constraints
"""

from database import Database
from scheduler import DutyScheduler

def test_comprehensive_algorithm():
    """Test all comprehensive constraints"""
    print("🔍 TESTING COMPREHENSIVE SCHEDULING ALGORITHM")
    print("=" * 60)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    for month in [10, 11, 12]:
        print(f"\nTesting {2025}-{month:02d}")
        schedule = scheduler.generate_schedule(2025, month, 3, 4)
        print(f"Generated {len(schedule)} assignments")
        
        unassigned = sum(1 for _, person_id, _ in schedule if person_id is None)
        print(f"Unassigned days: {unassigned}")
        
        consecutive = scheduler.detect_consecutive_assignments(schedule)
        print(f"Consecutive assignments: {len(consecutive)}")
        
        weekend_assignments = {}
        for scheduled_date, person_id, day_name in schedule:
            if person_id and day_name in ['Cumartesi', 'Pazar']:
                if person_id not in weekend_assignments:
                    weekend_assignments[person_id] = {'Cumartesi': 0, 'Pazar': 0}
                weekend_assignments[person_id][day_name] += 1
        
        weekend_violations = 0
        for person_id, assignments in weekend_assignments.items():
            total_weekends = assignments['Cumartesi'] + assignments['Pazar']
            if total_weekends > 2:
                weekend_violations += 1
            elif total_weekends == 2:
                if assignments['Cumartesi'] == 2 or assignments['Pazar'] == 2:
                    weekend_violations += 1
        
        print(f"Weekend violations: {weekend_violations}")
        print('---')
    
    print("\n✅ COMPREHENSIVE ALGORITHM TEST COMPLETE")

if __name__ == "__main__":
    test_comprehensive_algorithm()
