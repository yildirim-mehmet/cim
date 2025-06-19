#!/usr/bin/env python3
import sqlite3
from datetime import date

def check_database_state():
    print("=== Checking Database State ===")
    
    conn = sqlite3.connect('nobet_programi.db')
    cursor = conn.cursor()
    
    # Check total Nobet records
    cursor.execute('SELECT COUNT(*) FROM Nobet')
    total_count = cursor.fetchone()[0]
    print(f'Total Nobet records: {total_count}')
    
    # Check June 2025 records
    cursor.execute('SELECT COUNT(*) FROM Nobet WHERE strftime("%Y-%m", tarih) = "2025-06"')
    june_count = cursor.fetchone()[0]
    print(f'June 2025 Nobet records: {june_count}')
    
    # Sample records
    cursor.execute('SELECT tarih, personelId, ad, deger FROM Nobet LIMIT 5')
    sample = cursor.fetchall()
    print(f'Sample Nobet records: {sample}')
    
    # Check if there are any records with personnel names
    cursor.execute('''
        SELECT n.tarih, p.ad, p.statu 
        FROM Nobet n
        JOIN Personel p ON n.personelId = p.id
        WHERE strftime("%Y-%m", n.tarih) = "2025-06"
        LIMIT 5
    ''')
    joined_sample = cursor.fetchall()
    print(f'Sample joined records (Nobet + Personel): {joined_sample}')
    
    conn.close()

if __name__ == "__main__":
    check_database_state()
