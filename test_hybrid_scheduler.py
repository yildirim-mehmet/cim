import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database

def test_both_methods():
    db = Database()
    db.populate_sample_data()
    scheduler = DutyScheduler(db)
    
    print("🧪 TESTING HYBRID SCHEDULER COMPATIBILITY")
    
    schedule1 = scheduler.generate_schedule(2025, 2)
    print("✅ Max-Min priority method works")
    
    schedule2 = scheduler.generate_schedule_with_global_optimization(2025, 2, 0, 10)
    print("✅ Global optimization method works")
    
    for schedule, name in [(schedule1, "Max-Min"), (schedule2, "Global Opt")]:
        person_counts = {}
        for _, person_id, _ in schedule:
            if person_id:
                person_counts[person_id] = person_counts.get(person_id, 0) + 1
        
        if person_counts:
            min_duties = min(person_counts.values())
            max_duties = max(person_counts.values())
            diff = max_duties - min_duties
            print(f"✅ {name}: Min={min_duties}, Max={max_duties}, Difference={diff}")
            
            if diff <= 1:
                print(f"✅ {name}: Equal distribution maintained (difference ≤ 1)")
            else:
                print(f"❌ {name}: Unequal distribution (difference > 1)")

if __name__ == "__main__":
    test_both_methods()
