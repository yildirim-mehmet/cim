
from database import Database
from scheduler import DutyScheduler
from datetime import date

# Test current Mazeret logic
db = Database()
scheduler = DutyScheduler(db)

# Clear test data
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
cursor.execute('DELETE FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
conn.commit()

# Add test mazeret entries
cursor.execute('INSERT INTO Mazeret (personelId, tarih, tut) VALUES (1, "2025-06-15", 0)')  # exclude
cursor.execute('INSERT INTO Mazeret (personelId, tarih, tut) VALUES (2, "2025-06-20", 1)')  # force assign
conn.commit()
conn.close()

print('Added test mazeret entries:')
print('- PersonelID=1, Date=2025-06-15, tut=0 (exclude)')
print('- PersonelID=2, Date=2025-06-20, tut=1 (force assign)')

# Generate schedule and check results
schedule = scheduler.generate_schedule(2025, 6)

june_15_assignment = None
june_20_assignment = None

for scheduled_date, person_id, day_type in schedule:
    if scheduled_date == date(2025, 6, 15):
        june_15_assignment = person_id
    elif scheduled_date == date(2025, 6, 20):
        june_20_assignment = person_id

print(f'June 15 assignment (should NOT be PersonelID=1): {june_15_assignment}')
print(f'June 20 assignment (should be PersonelID=2): {june_20_assignment}')

# Verify results
if june_15_assignment != 1:
    print('✅ PASS: PersonelID=1 excluded from 2025-06-15')
else:
    print('❌ FAIL: PersonelID=1 should be excluded from 2025-06-15')

if june_20_assignment == 2:
    print('✅ PASS: PersonelID=2 forced assignment to 2025-06-20')
else:
    print('❌ FAIL: PersonelID=2 should be assigned to 2025-06-20')

# Clean up
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
cursor.execute('DELETE FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
conn.commit()
conn.close()

print('Test data cleaned up')

