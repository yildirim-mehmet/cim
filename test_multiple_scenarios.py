
print('Testing equal distribution across multiple scenarios...')
import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
import calendar

test_cases = [
    (2025, 1),   # January: 31 days
    (2025, 2),   # February: 28 days (reported issue)
    (2025, 3),   # March: 31 days
    (2025, 6),   # June: 30 days (has holidays)
    (2025, 7),   # July: 31 days
    (2025, 12),  # December: 31 days
]

all_fair = True

for year, month in test_cases:
    print(f'\nTesting {calendar.month_name[month]} {year}:')
    
    db = Database()
    db.populate_sample_data()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Nobet')
    conn.commit()
    conn.close()
    
    scheduler = DutyScheduler(db)
    schedule = scheduler.generate_schedule(year, month)
    
    person_counts = {}
    for _, person_id, _ in schedule:
        if person_id:
            person_counts[person_id] = person_counts.get(person_id, 0) + 1
    
    if person_counts:
        min_duties = min(person_counts.values())
        max_duties = max(person_counts.values())
        difference = max_duties - min_duties
        
        print(f'  Min duties: {min_duties}, Max duties: {max_duties}, Difference: {difference}')
        
        if difference > 1:
            print(f'  ❌ UNEQUAL DISTRIBUTION: Difference = {difference}')
            for person_id, count in sorted(person_counts.items(), key=lambda x: x[1]):
                name = scheduler.get_person_name(person_id)
                print(f'    {name}: {count} duties')
            all_fair = False
        else:
            print(f'  ✅ Fair distribution (difference = {difference})')
    else:
        print('  ⚠️ No duties assigned')

print(f'\n=== OVERALL RESULT ===')
if all_fair:
    print('🎉 All months show fair distribution (max difference = 1)')
else:
    print('💥 Some months have unequal distribution (difference > 1)')

