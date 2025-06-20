
from database import Database
from scheduler import DutyScheduler
from datetime import date

# Test full schedule generation to see why tut=1 fails
db = Database()
scheduler = DutyScheduler(db)

# Clear test data and add mazeret entry
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
cursor.execute('DELETE FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
cursor.execute('INSERT INTO Mazeret (personelId, tarih, tut) VALUES (2, "2025-06-20", 1)')
conn.commit()
conn.close()

print('=== Testing full schedule generation ===')

# Generate full schedule
schedule = scheduler.generate_schedule(2025, 6)

# Check what happened on June 20th
june_20_assignment = None
june_19_assignment = None
june_21_assignment = None

for scheduled_date, person_id, day_type in schedule:
    if scheduled_date == date(2025, 6, 19):
        june_19_assignment = person_id
    elif scheduled_date == date(2025, 6, 20):
        june_20_assignment = person_id
    elif scheduled_date == date(2025, 6, 21):
        june_21_assignment = person_id

print(f'June 19 assignment: PersonelID={june_19_assignment}')
print(f'June 20 assignment: PersonelID={june_20_assignment} (should be 2)')
print(f'June 21 assignment: PersonelID={june_21_assignment}')

# Check if PersonelID=2 was assigned to consecutive days
person_2_assignments = []
for scheduled_date, person_id, day_type in schedule:
    if person_id == 2:
        person_2_assignments.append(scheduled_date)

print(f'PersonelID=2 assignments: {person_2_assignments}')

# Check if consecutive days rule is blocking the assignment
if june_19_assignment == 2:
    print('ISSUE: PersonelID=2 assigned to June 19, consecutive days rule blocks June 20')
elif june_21_assignment == 2:
    print('ISSUE: PersonelID=2 assigned to June 21, consecutive days rule blocks June 20')

# Clean up
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
conn.commit()
conn.close()

