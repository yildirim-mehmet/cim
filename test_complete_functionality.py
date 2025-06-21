#!/usr/bin/env python3

from database import Database
from scheduler import DutyScheduler
from excel_exporter import ExcelExporter
from datetime import date
import os

def test_excel_export_fix():
    print("=== Testing Excel Export Fix ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    exporter = ExcelExporter(db)
    
    print("1. Generating schedule...")
    schedule = scheduler.generate_schedule(2025, 6)
    
    if schedule:
        print(f"   Generated schedule with {len(schedule)} days")
        
        print("2. Testing in-memory Excel export...")
        filename = "test_in_memory_fixed.xlsx"
        result = exporter.export_in_memory_schedule(schedule, 2025, 6, filename)
        
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"   ✅ In-memory Excel export successful: {filename} ({file_size} bytes)")
            
            if file_size > 1000:
                print("   ✅ File size indicates proper content (not empty)")
            else:
                print("   ❌ File size too small, may be empty")
        else:
            print("   ❌ Excel file not created")
        
        print("3. Testing database Excel export after save...")
        scheduler.save_schedule(schedule, 2025, 6)
        
        filename2 = "test_database_fixed.xlsx"
        result2 = exporter.export_monthly_schedule(2025, 6, filename2)
        
        if os.path.exists(filename2):
            file_size2 = os.path.getsize(filename2)
            print(f"   ✅ Database Excel export successful: {filename2} ({file_size2} bytes)")
        else:
            print("   ❌ Database Excel file not created")
    else:
        print("   ❌ Schedule generation failed")

def test_database_operations():
    print("\n=== Testing Database CRUD Operations ===")
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("1. Testing GunDeger operations...")
    cursor.execute("INSERT INTO GunDeger (ad, deger) VALUES (?, ?)", ("Test Day", 2.5))
    conn.commit()
    
    cursor.execute("SELECT id FROM GunDeger WHERE ad = 'Test Day'")
    test_id = cursor.fetchone()[0]
    print(f"   ✅ GunDeger inserted with ID: {test_id}")
    
    cursor.execute("UPDATE GunDeger SET deger = ? WHERE id = ?", (3.0, test_id))
    conn.commit()
    print("   ✅ GunDeger updated")
    
    cursor.execute("DELETE FROM GunDeger WHERE id = ?", (test_id,))
    conn.commit()
    print("   ✅ GunDeger deleted")
    
    print("2. Testing Tatil operations...")
    cursor.execute("SELECT id FROM GunDeger LIMIT 1")
    gun_deger_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO Tatil (gunDegerId, ad, tarih) VALUES (?, ?, ?)", 
                  (gun_deger_id, "Test Holiday", "2025-12-25"))
    conn.commit()
    
    cursor.execute("SELECT id FROM Tatil WHERE ad = 'Test Holiday'")
    tatil_id = cursor.fetchone()[0]
    print(f"   ✅ Tatil inserted with ID: {tatil_id}")
    
    cursor.execute("DELETE FROM Tatil WHERE id = ?", (tatil_id,))
    conn.commit()
    print("   ✅ Tatil deleted")
    
    print("3. Testing Eski Nöbetler query...")
    cursor.execute("""
        SELECT COUNT(*) FROM Nobet n
        JOIN Personel p ON n.personelId = p.id
        WHERE strftime('%Y-%m', n.tarih) = ?
    """, ("2025-06",))
    
    count = cursor.fetchone()[0]
    print(f"   ✅ Found {count} duty records for June 2025")
    
    conn.close()

def test_gui_methods_exist():
    print("\n=== Testing GUI Method Existence ===")
    
    try:
        import sys
        sys.path.append('/home/ubuntu/repos/cim')
        
        from gui import DutySchedulerGUI
        
        required_methods = [
            'export_to_excel',
            'open_old_duties_window',
            'open_gun_deger_window',
            'open_tatil_window',
            'create_date_picker'
        ]
        
        for method in required_methods:
            if hasattr(DutySchedulerGUI, method):
                print(f"   ✅ {method} method exists")
            else:
                print(f"   ❌ {method} method missing")
        
        print("   ✅ GUI class loaded successfully")
        
    except Exception as e:
        print(f"   ❌ GUI test failed: {e}")

if __name__ == "__main__":
    test_excel_export_fix()
    test_database_operations()
    test_gui_methods_exist()
    print("\n🎉 Complete functionality test completed!")
