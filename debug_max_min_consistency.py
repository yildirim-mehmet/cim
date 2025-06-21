import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database

def debug_max_min_consistency():
    """Debug why Max-Min priority shows different results in different tests"""
    print("🔍 DEBUGGING MAX-MIN PRIORITY CONSISTENCY")
    
    print("\n=== TEST 1: Fresh Database (like test_max_min_priority.py) ===")
    db1 = Database()
    db1.populate_sample_data()
    
    conn1 = db1.get_connection()
    cursor1 = conn1.cursor()
    cursor1.execute('DELETE FROM Nobet')
    conn1.commit()
    conn1.close()
    
    scheduler1 = DutyScheduler(db1)
    schedule1 = scheduler1.generate_schedule(2025, 2)
    
    person_counts1 = {}
    for _, person_id, _ in schedule1:
        if person_id:
            person_counts1[person_id] = person_counts1.get(person_id, 0) + 1
    
    if person_counts1:
        min1 = min(person_counts1.values())
        max1 = max(person_counts1.values())
        diff1 = max1 - min1
        print(f"Fresh DB: Min={min1}, Max={max1}, Difference={diff1}")
    
    print("\n=== TEST 2: Fresh Database (like test_gui_method_availability.py) ===")
    db2 = Database()
    db2.populate_sample_data()
    
    scheduler2 = DutyScheduler(db2)
    schedule2 = scheduler2.generate_schedule_with_global_optimization(2025, 2, 0, 10)
    
    person_counts2 = {}
    for _, person_id, _ in schedule2:
        if person_id:
            person_counts2[person_id] = person_counts2.get(person_id, 0) + 1
    
    if person_counts2:
        min2 = min(person_counts2.values())
        max2 = max(person_counts2.values())
        diff2 = max2 - min2
        print(f"Fresh DB (global opt): Min={min2}, Max={max2}, Difference={diff2}")
    
    print("\n=== TEST 3: Check Existing Duties ===")
    conn3 = db2.get_connection()
    cursor3 = conn3.cursor()
    cursor3.execute('SELECT COUNT(*) FROM Nobet')
    duty_count = cursor3.fetchone()[0]
    print(f"Existing duties in database: {duty_count}")
    
    if duty_count > 0:
        cursor3.execute('SELECT personelId, COUNT(*) FROM Nobet GROUP BY personelId')
        existing_duties = cursor3.fetchall()
        print("Existing duty distribution:")
        for person_id, count in existing_duties:
            print(f"  Person {person_id}: {count} duties")
    
    conn3.close()
    
    return diff1, diff2

if __name__ == "__main__":
    diff1, diff2 = debug_max_min_consistency()
    
    if diff1 <= 1 and diff2 <= 1:
        print(f"\n✅ CONSISTENT RESULTS: Both tests show ≤1 difference")
    else:
        print(f"\n❌ INCONSISTENT RESULTS: Test1={diff1}, Test2={diff2}")
