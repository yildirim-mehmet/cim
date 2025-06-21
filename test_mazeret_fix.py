#!/usr/bin/env python3
"""
Test script to verify Mazeret logic fixes
"""

from database import Database
from scheduler import DutyScheduler
from datetime import datetime, date

def test_mazeret_tut_logic():
    """Test that tut=1 overrides ALL constraints including consecutive days"""
    print("=== Testing Mazeret tut=1 Logic Override ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Mazeret WHERE personelId = 2")
    cursor.execute("DELETE FROM Nobet WHERE strftime('%Y-%m', tarih) = '2025-06'")
    conn.commit()
    
    cursor.execute("INSERT INTO Mazeret (personelId, tarih, tut) VALUES (?, ?, ?)", 
                  (2, '2025-06-20', 1))
    
    cursor.execute("INSERT INTO Mazeret (personelId, tarih, tut) VALUES (?, ?, ?)", 
                  (3, '2025-06-15', 0))
    
    conn.commit()
    conn.close()
    
    print("✅ Added test mazeret entries:")
    print("   PersonelID=2, Date=2025-06-20, tut=1 (FORCE assignment)")
    print("   PersonelID=3, Date=2025-06-15, tut=0 (PREVENT assignment)")
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    if schedule:
        print(f"✅ Schedule generated with {len(schedule)} days")
        
        june_20_assignment = None
        june_15_assignment = None
        
        for scheduled_date, person_id, day_type in schedule:
            if scheduled_date == date(2025, 6, 20):
                june_20_assignment = person_id
            elif scheduled_date == date(2025, 6, 15):
                june_15_assignment = person_id
        
        if june_20_assignment == 2:
            print("✅ PASS: PersonelID=2 assigned to June 20 (tut=1 override worked)")
        else:
            print(f"❌ FAIL: PersonelID={june_20_assignment} assigned to June 20, expected PersonelID=2")
        
        if june_15_assignment != 3:
            print("✅ PASS: PersonelID=3 NOT assigned to June 15 (tut=0 exclusion worked)")
        else:
            print("❌ FAIL: PersonelID=3 assigned to June 15 despite tut=0")
        
        june_19_assignment = None
        june_21_assignment = None
        
        for scheduled_date, person_id, day_type in schedule:
            if scheduled_date == date(2025, 6, 19):
                june_19_assignment = person_id
            elif scheduled_date == date(2025, 6, 21):
                june_21_assignment = person_id
        
        print(f"   June 19: PersonelID={june_19_assignment}")
        print(f"   June 20: PersonelID={june_20_assignment} (FORCED)")
        print(f"   June 21: PersonelID={june_21_assignment}")
        
        if june_20_assignment == 2:
            if june_19_assignment == 2 or june_21_assignment == 2:
                print("✅ EXCELLENT: tut=1 override worked even with consecutive days constraint!")
            else:
                print("✅ GOOD: tut=1 assignment successful (no consecutive days conflict)")
    else:
        print("❌ No schedule generated!")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Mazeret WHERE personelId IN (2, 3)")
    cursor.execute("DELETE FROM Nobet WHERE strftime('%Y-%m', tarih) = '2025-06'")
    conn.commit()
    conn.close()
    
    print("✅ Test cleanup completed")

def test_gui_integration():
    """Test GUI integration with new functionality"""
    print("\n=== Testing GUI Integration ===")
    
    try:
        import tkinter as tk
        from gui import DutySchedulerGUI
        
        root = tk.Tk()
        app = DutySchedulerGUI(root)
        
        if hasattr(app, 'generate_schedule_display'):
            print("✅ generate_schedule_display method exists")
        else:
            print("❌ generate_schedule_display method missing")
        
        from datetime import datetime, date
        test_date = datetime.strptime('2025-06-20', '%Y-%m-%d').date()
        print(f"✅ datetime import working: {test_date}")
        
        root.destroy()
        print("✅ GUI instantiation successful")
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")

if __name__ == "__main__":
    test_mazeret_tut_logic()
    test_gui_integration()
    print("\n🎉 All tests completed!")
