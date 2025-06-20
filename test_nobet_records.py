
# Test the right-click menu error
from database import Database
from datetime import date

db = Database()
conn = db.get_connection()
cursor = conn.cursor()

# Check if there are any Nobet records for June 2025
cursor.execute('SELECT COUNT(*) FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
count = cursor.fetchone()[0]
print(f'Nobet records for June 2025: {count}')

# Check the structure of Nobet table
cursor.execute('PRAGMA table_info(Nobet)')
columns = cursor.fetchall()
print('Nobet table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Check if there are any records at all
cursor.execute('SELECT COUNT(*) FROM Nobet')
total_count = cursor.fetchone()[0]
print(f'Total Nobet records: {total_count}')

# Check a sample record if any exist
if total_count > 0:
    cursor.execute('SELECT * FROM Nobet LIMIT 1')
    sample = cursor.fetchone()
    print(f'Sample record: {sample}')

conn.close()

