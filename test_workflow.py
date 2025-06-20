
# Test the current workflow to understand why no Nobet records exist
from database import Database
from scheduler import DutyScheduler
from datetime import date

db = Database()
scheduler = DutyScheduler(db)

print('=== Testing current workflow ===')

# Generate a schedule
print('Generating schedule for June 2025...')
schedule = scheduler.generate_schedule(2025, 6)

if schedule:
    print(f'Schedule generated with {len(schedule)} days')
    
    # Check first few days
    for i, (scheduled_date, person_id, day_type) in enumerate(schedule[:5]):
        person_name = scheduler.get_person_name(person_id) if person_id else 'ATANMADI'
        print(f'  {scheduled_date}: {person_name} ({day_type})')
    
    # Check if save_schedule works
    print('\nTesting save_schedule...')
    scheduler.save_schedule(schedule, 2025, 6)
    
    # Verify records were saved
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
    count = cursor.fetchone()[0]
    print(f'Nobet records after save: {count}')
    
    if count > 0:
        cursor.execute('SELECT tarih, ad FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06" LIMIT 5')
        records = cursor.fetchall()
        print('Sample saved records:')
        for record in records:
            print(f'  {record[0]}: {record[1]}')
    
    conn.close()
else:
    print('No schedule generated!')

