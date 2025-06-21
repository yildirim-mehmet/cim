
from database import Database
from scheduler import DutyScheduler
from datetime import date

# Debug the priority scoring for tut=1
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

print('Added mazeret entry: PersonelID=2, Date=2025-06-20, tut=1 (force assign)')

# Get personnel and stats to understand priority calculation
personnel = scheduler.get_active_personnel()
personnel_ids = [p[0] for p in personnel]
stats = scheduler.get_personnel_duty_stats(personnel_ids)

total_count = sum(s['count'] for s in stats.values())
total_value = sum(s['total_value'] for s in stats.values())
avg_count = total_count / len(personnel_ids) if personnel_ids else 0
avg_value = total_value / len(personnel_ids) if personnel_ids else 0

print(f'Personnel stats:')
for pid in personnel_ids:
    priority = scheduler.calculate_priority_score(pid, stats, avg_count, avg_value)
    print(f'  PersonelID={pid}: count={stats[pid]["count"]}, value={stats[pid]["total_value"]:.1f}, priority={priority:.1f}')

print(f'Average count: {avg_count:.1f}, Average value: {avg_value:.1f}')

# Clean up
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('DELETE FROM Mazeret WHERE personelId IN (1, 2)')
conn.commit()
conn.close()

