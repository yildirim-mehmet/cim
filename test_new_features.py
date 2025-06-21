#!/usr/bin/env python3
"""
Test script for new Mazeret and duty change features
"""

from database import Database
from scheduler import DutyScheduler
from datetime import datetime, date

def test_mazeret_functionality():
    """Test Mazeret database operations"""
    print("=== Testing Mazeret Functionality ===")
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    test_personel_id = 1
    test_date = '2025-06-15'
    test_tut = 1
    
    try:
        cursor.execute("INSERT INTO Mazeret (personelId, tarih, tut) VALUES (?, ?, ?)", 
                      (test_personel_id, test_date, test_tut))
        conn.commit()
        print("✅ Mazeret entry added successfully")
        
        cursor.execute("SELECT * FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                      (test_personel_id, test_date))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Mazeret entry verified: ID={result[0]}, PersonelID={result[1]}, Tarih={result[2]}, Tut={result[3]}")
        else:
            print("❌ Mazeret entry not found after insertion")
            
        cursor.execute("DELETE FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                      (test_personel_id, test_date))
        conn.commit()
        print("✅ Test mazeret entry cleaned up")
        
    except Exception as e:
        print(f"❌ Mazeret test failed: {e}")
    finally:
        conn.close()

def test_duty_change_functionality():
    """Test duty change database operations"""
    print("\n=== Testing Duty Change Functionality ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    if not schedule:
        print("❌ No schedule generated for testing")
        return
    
    scheduler.save_schedule(schedule, 2025, 6)
    print("✅ Test schedule saved")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, personelId, tarih FROM Nobet WHERE tarih LIKE '2025-06%' LIMIT 1")
        test_duty = cursor.fetchone()
        
        if not test_duty:
            print("❌ No duty entries found for testing")
            return
            
        duty_id, old_personel_id, duty_date = test_duty
        new_personel_id = 2 if old_personel_id != 2 else 3
        
        print(f"Testing duty change: ID={duty_id}, Date={duty_date}, Old PersonelID={old_personel_id}, New PersonelID={new_personel_id}")
        
        cursor.execute("""
            UPDATE Nobet 
            SET personelId = ?, degisiklik = 1, esTarih = ?, yenTarih = ?
            WHERE id = ?
        """, (new_personel_id, duty_date, duty_date, duty_id))
        
        conn.commit()
        
        cursor.execute("SELECT personelId, degisiklik, esTarih, yenTarih FROM Nobet WHERE id = ?", (duty_id,))
        result = cursor.fetchone()
        
        if result and result[0] == new_personel_id and result[1] == 1:
            print("✅ Duty change updated successfully")
            print(f"   PersonelID: {result[0]}, Degisiklik: {result[1]}, EsTarih: {result[2]}, YenTarih: {result[3]}")
        else:
            print("❌ Duty change verification failed")
            
    except Exception as e:
        print(f"❌ Duty change test failed: {e}")
    finally:
        conn.close()

def test_gui_imports():
    """Test that GUI has all necessary imports"""
    print("\n=== Testing GUI Imports ===")
    
    try:
        from gui import DutySchedulerGUI
        import tkinter as tk
        from tkinter import ttk, messagebox
        from datetime import datetime
        
        print("✅ All GUI imports successful")
        
        gui_methods = ['open_mazeret_window', 'show_duty_change_menu']
        
        for method in gui_methods:
            if hasattr(DutySchedulerGUI, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")

if __name__ == "__main__":
    test_gui_imports()
    test_mazeret_functionality()
    test_duty_change_functionality()
    print("\n🎉 All tests completed!")
