#!/usr/bin/env python3

from database import Database
from scheduler import DutyScheduler
from excel_exporter import ExcelExporter
from datetime import date
import os

def test_excel_export_functionality():
    print("=== Testing Excel Export Functionality ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    exporter = ExcelExporter(db)
    
    print("1. Testing in-memory schedule export...")
    schedule = scheduler.generate_schedule(2025, 6)
    
    if schedule:
        print(f"   Generated schedule with {len(schedule)} days")
        
        filename = "test_in_memory_export.xlsx"
        result = exporter.export_in_memory_schedule(schedule, 2025, 6, filename)
        
        if os.path.exists(filename):
            print(f"   ✅ In-memory Excel export successful: {filename}")
            file_size = os.path.getsize(filename)
            print(f"   File size: {file_size} bytes")
        else:
            print("   ❌ In-memory Excel export failed")
    else:
        print("   ❌ Schedule generation failed")
    
    print("\n2. Testing database schedule export...")
    scheduler.save_schedule(schedule, 2025, 6)
    
    filename2 = "test_database_export.xlsx"
    result2 = exporter.export_monthly_schedule(2025, 6, filename2)
    
    if os.path.exists(filename2):
        print(f"   ✅ Database Excel export successful: {filename2}")
        file_size2 = os.path.getsize(filename2)
        print(f"   File size: {file_size2} bytes")
    else:
        print("   ❌ Database Excel export failed")

def test_old_duties_functionality():
    print("\n=== Testing Old Duties Database Queries ===")
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("1. Testing duty listing query...")
    cursor.execute("""
        SELECT n.tarih, p.ad, p.statu, n.deger, n.degisiklik
        FROM Nobet n
        JOIN Personel p ON n.personelId = p.id
        WHERE strftime('%Y-%m', n.tarih) = ?
        ORDER BY n.tarih
    """, ("2025-06",))
    
    duties = cursor.fetchall()
    print(f"   Found {len(duties)} duty records for June 2025")
    
    if duties:
        print("   Sample records:")
        for duty in duties[:3]:
            print(f"     {duty[0]} - {duty[1]} ({duty[2]}) - {duty[3]} points")
    
    print("\n2. Testing delete functionality...")
    cursor.execute("SELECT COUNT(*) FROM Nobet WHERE strftime('%Y-%m', tarih) = ?", ("2025-06",))
    before_count = cursor.fetchone()[0]
    print(f"   Records before delete: {before_count}")
    
    cursor.execute("DELETE FROM Nobet WHERE strftime('%Y-%m', tarih) = ?", ("2025-06",))
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f"   Deleted {deleted_count} records")
    
    cursor.execute("SELECT COUNT(*) FROM Nobet WHERE strftime('%Y-%m', tarih) = ?", ("2025-06",))
    after_count = cursor.fetchone()[0]
    print(f"   Records after delete: {after_count}")
    
    conn.close()

if __name__ == "__main__":
    test_excel_export_functionality()
    test_old_duties_functionality()
    print("\n🎉 All tests completed!")
