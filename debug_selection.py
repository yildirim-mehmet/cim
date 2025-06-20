
from database import Database
from scheduler import DutyScheduler
from datetime import date

# Debug the actual selection process for 2025-06-20
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

print('=== Debugging selection process for 2025-06-20 ===')

# Get all the data needed for scheduling
personnel = scheduler.get_active_personnel()
day_values = scheduler.get_day_values()
holidays = scheduler.get_holidays(2025, 6)
exemptions = scheduler.get_exemptions(2025, 6)

personnel_ids = [p[0] for p in personnel]
stats = scheduler.get_personnel_duty_stats(personnel_ids)

total_count = sum(s['count'] for s in stats.values())
total_value = sum(s['total_value'] for s in stats.values())
avg_count = total_count / len(personnel_ids) if personnel_ids else 0
avg_value = total_value / len(personnel_ids) if personnel_ids else 0

# Build exemption dict like in the actual code
from collections import defaultdict
exemption_dict = defaultdict(dict)
for e in exemptions:
    exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]

print(f'Exemption dict: {dict(exemption_dict)}')

# Simulate the selection process for June 20th
current_date = date(2025, 6, 20)
weekday = current_date.weekday()
day_value_id = scheduler.get_weekday_id(weekday)
day_info = day_values[day_value_id]

print(f'Date: {current_date}, Weekday: {weekday}, Day value ID: {day_value_id}')
print(f'Day info: {day_info}')

# Check eligible personnel for June 20th
eligible_personnel = []
for person_id in personnel_ids:
    print(f'\nChecking PersonelID={person_id}:')
    
    # Check exemption
    if person_id in exemption_dict and current_date in exemption_dict[person_id]:
        tut_value = exemption_dict[person_id][current_date]
        print(f'  Has exemption: tut={tut_value}')
        if tut_value == 0:
            print('  EXCLUDED due to tut=0')
            continue
    else:
        print('  No exemption found')
    
    # Calculate priority score
    priority_score = scheduler.calculate_priority_score(person_id, stats, avg_count, avg_value)
    print(f'  Base priority score: {priority_score}')
    
    # Check for tut=1 boost
    if person_id in exemption_dict and current_date in exemption_dict[person_id]:
        if exemption_dict[person_id][current_date] == 1:
            priority_score += 1000
            print(f'  BOOSTED priority score: {priority_score} (tut=1)')
    
    eligible_personnel.append((person_id, priority_score))
    print(f'  Final: PersonelID={person_id}, Priority={priority_score}')

print(f'\nEligible personnel: {eligible_personnel}')

if eligible_personnel:
    eligible_personnel.sort(key=lambda x: x[1], reverse=True)
    selected_person_id = eligible_personnel[0][0]
    print(f'Selected PersonelID: {selected_person_id}')
else:
    print('No eligible personnel!')

# Clean up
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
conn.commit()
conn.close()

