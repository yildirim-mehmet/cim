
from database import Database
from scheduler import DutyScheduler
from datetime import date

# Debug why tut=1 is not working for PersonelID=2 on 2025-06-20
db = Database()
scheduler = DutyScheduler(db)

# Clear test data
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
cursor.execute('DELETE FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
conn.commit()

# Add test mazeret entry with tut=1
cursor.execute('INSERT INTO Mazeret (personelId, tarih, tut) VALUES (2, "2025-06-20", 1)')
conn.commit()
conn.close()

print('=== Debugging tut=1 force assignment ===')
print('Added mazeret entry: PersonelID=2, Date=2025-06-20, tut=1 (force assign)')

# Get exemptions to verify it's being read correctly
exemptions = scheduler.get_exemptions(2025, 6)
print(f'Exemptions found: {exemptions}')

# Get personnel and check if PersonelID=2 exists and is active
personnel = scheduler.get_active_personnel()
personnel_ids = [p[0] for p in personnel]
print(f'Active personnel IDs: {personnel_ids}')
print(f'PersonelID=2 is active: {2 in personnel_ids}')

# Check what day of week 2025-06-20 is
target_date = date(2025, 6, 20)
print(f'2025-06-20 is a {target_date.strftime("%A")} (weekday {target_date.weekday()})')

# Check if there are any conflicts for PersonelID=2 on that date
print('\n=== Checking conflicts for PersonelID=2 on 2025-06-20 ===')

# Generate partial schedule up to June 19 to check for conflicts
schedule_partial = []
for day in range(1, 20):  # Days 1-19
    current_date = date(2025, 6, day)
    # Simulate assignment to check conflicts
    schedule_partial.append((current_date, 1, 'test'))  # Assign to PersonelID=1 for testing

# Check consecutive days conflict
has_consecutive = scheduler.has_consecutive_days_conflict(2, target_date, schedule_partial)
print(f'Consecutive days conflict: {has_consecutive}')

# Check Thursday-Saturday conflict
has_thu_sat = scheduler.has_thursday_saturday_conflict(2, target_date, schedule_partial)
print(f'Thursday-Saturday conflict: {has_thu_sat}')

# Check Ramazan-Kurban conflict
has_ramazan_kurban = scheduler.is_ramazan_kurban_conflict(2, target_date, schedule_partial)
print(f'Ramazan-Kurban conflict: {has_ramazan_kurban}')

# Clean up
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
conn.commit()
conn.close()

