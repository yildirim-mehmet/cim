#!/usr/bin/env python3

from database import Database
import tkinter as tk
from gui import DutySchedulerGUI

def test_gun_deger_operations():
    print("=== Testing GunDeger CRUD Operations ===")
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("1. Testing GunDeger insertion...")
    cursor.execute("INSERT INTO GunDeger (ad, deger) VALUES (?, ?)", ("Test Gün", 2.5))
    conn.commit()
    
    cursor.execute("SELECT id, ad, deger FROM GunDeger WHERE ad = 'Test Gün'")
    result = cursor.fetchone()
    
    if result:
        print(f"   ✅ GunDeger inserted: ID={result[0]}, Ad={result[1]}, Deger={result[2]}")
        test_id = result[0]
        
        print("2. Testing GunDeger update...")
        cursor.execute("UPDATE GunDeger SET deger = ? WHERE id = ?", (3.0, test_id))
        conn.commit()
        
        cursor.execute("SELECT deger FROM GunDeger WHERE id = ?", (test_id,))
        updated_result = cursor.fetchone()
        
        if updated_result and updated_result[0] == 3.0:
            print("   ✅ GunDeger updated successfully")
        else:
            print("   ❌ GunDeger update failed")
        
        print("3. Testing GunDeger deletion...")
        cursor.execute("DELETE FROM GunDeger WHERE id = ?", (test_id,))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM GunDeger WHERE id = ?", (test_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("   ✅ GunDeger deleted successfully")
        else:
            print("   ❌ GunDeger deletion failed")
    else:
        print("   ❌ GunDeger insertion failed")
    
    conn.close()

def test_tatil_operations():
    print("\n=== Testing Tatil CRUD Operations ===")
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM GunDeger LIMIT 1")
    gun_deger_id = cursor.fetchone()[0]
    
    print("1. Testing Tatil insertion...")
    cursor.execute("INSERT INTO Tatil (gunDegerId, ad, tarih) VALUES (?, ?, ?)", 
                  (gun_deger_id, "Test Tatil", "2025-12-25"))
    conn.commit()
    
    cursor.execute("SELECT id, gunDegerId, ad, tarih FROM Tatil WHERE ad = 'Test Tatil'")
    result = cursor.fetchone()
    
    if result:
        print(f"   ✅ Tatil inserted: ID={result[0]}, GunDegerId={result[1]}, Ad={result[2]}, Tarih={result[3]}")
        test_id = result[0]
        
        print("2. Testing Tatil update...")
        cursor.execute("UPDATE Tatil SET ad = ? WHERE id = ?", ("Updated Test Tatil", test_id))
        conn.commit()
        
        cursor.execute("SELECT ad FROM Tatil WHERE id = ?", (test_id,))
        updated_result = cursor.fetchone()
        
        if updated_result and updated_result[0] == "Updated Test Tatil":
            print("   ✅ Tatil updated successfully")
        else:
            print("   ❌ Tatil update failed")
        
        print("3. Testing Tatil deletion...")
        cursor.execute("DELETE FROM Tatil WHERE id = ?", (test_id,))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM Tatil WHERE id = ?", (test_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("   ✅ Tatil deleted successfully")
        else:
            print("   ❌ Tatil deletion failed")
    else:
        print("   ❌ Tatil insertion failed")
    
    conn.close()

def test_gui_instantiation():
    print("\n=== Testing GUI Instantiation with New Methods ===")
    
    try:
        root = tk.Tk()
        app = DutySchedulerGUI(root)
        
        required_methods = [
            'open_old_duties_window',
            'open_gun_deger_window', 
            'open_tatil_window',
            'export_to_excel'
        ]
        
        for method in required_methods:
            if hasattr(app, method):
                print(f"   ✅ {method} method exists")
            else:
                print(f"   ❌ {method} method missing")
        
        root.destroy()
        print("   ✅ GUI instantiation successful")
        
    except Exception as e:
        print(f"   ❌ GUI instantiation failed: {e}")

if __name__ == "__main__":
    test_gun_deger_operations()
    test_tatil_operations()
    test_gui_instantiation()
    print("\n🎉 All GUI screen tests completed!")
