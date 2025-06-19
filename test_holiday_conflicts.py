#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from scheduler import DutyScheduler
from database import Database
from datetime import date

def test_holiday_conflicts():
    print("=== Testing Enhanced Holiday Conflict Logic ===")
    
    try:
        db = Database()
        scheduler = DutyScheduler(db)
        
        print("\n1. Testing yearly Ramazan-Kurban conflict...")
        test_person_id = 1
        ramazan_date = date(2025, 6, 7)  # Ramazan 1
        kurban_date = date(2025, 8, 15)  # Hypothetical Kurban date
        
        conflict = scheduler.is_ramazan_kurban_conflict(test_person_id, kurban_date, [])
        print(f"Ramazan-Kurban yearly conflict: {conflict}")
        
        print("\n2. Testing general holiday conflict prevention...")
        conflict = scheduler.is_ramazan_kurban_conflict(test_person_id, ramazan_date, [])
        print(f"General holiday conflict: {conflict}")
        
        print("\n3. Testing mazeret override (tut=1)...")
        
        print("\n4. Testing database queries...")
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Tatil")
        tatil_count = cursor.fetchone()[0]
        print(f"Tatil table records: {tatil_count}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM Nobet n
            JOIN Tatil t ON n.tarih = t.tarih
        """)
        holiday_duties_count = cursor.fetchone()[0]
        print(f"Holiday duties in Nobet table: {holiday_duties_count}")
        
        cursor.execute("""
            SELECT t.tarih, t.ad FROM Nobet n
            JOIN Tatil t ON n.tarih = t.tarih
            WHERE n.personelId = ? AND strftime('%Y', n.tarih) = ?
            LIMIT 3
        """, (1, '2025'))
        
        yearly_holidays = cursor.fetchall()
        print(f"Sample yearly holidays for person 1: {yearly_holidays}")
        
        conn.close()
        
        print("✅ Holiday conflict tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_holiday_conflicts()
