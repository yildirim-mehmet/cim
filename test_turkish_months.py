#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from gui import DutySchedulerGUI
from excel_exporter import ExcelExporter
from database import Database

def test_turkish_months():
    print("=== Testing Turkish Month Names ===")
    
    print("1. Testing GUI Turkish months...")
    gui = DutySchedulerGUI.__new__(DutySchedulerGUI)
    
    expected_months = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
        7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    
    if hasattr(gui, 'TURKISH_MONTHS'):
        print(f"   ✅ GUI has TURKISH_MONTHS constant")
        for month_num, expected_name in expected_months.items():
            if gui.TURKISH_MONTHS.get(month_num) == expected_name:
                print(f"   ✅ Month {month_num}: {expected_name}")
            else:
                print(f"   ❌ Month {month_num}: Expected {expected_name}, got {gui.TURKISH_MONTHS.get(month_num)}")
    else:
        print("   ❌ GUI missing TURKISH_MONTHS constant")
    
    print("\n2. Testing ExcelExporter Turkish months...")
    db = Database()
    exporter = ExcelExporter(db)
    
    if hasattr(exporter, 'TURKISH_MONTHS'):
        print(f"   ✅ ExcelExporter has TURKISH_MONTHS constant")
        for month_num, expected_name in expected_months.items():
            if exporter.TURKISH_MONTHS.get(month_num) == expected_name:
                print(f"   ✅ Month {month_num}: {expected_name}")
            else:
                print(f"   ❌ Month {month_num}: Expected {expected_name}, got {exporter.TURKISH_MONTHS.get(month_num)}")
    else:
        print("   ❌ ExcelExporter missing TURKISH_MONTHS constant")
    
    print("\n3. Testing Excel export with Turkish month names...")
    try:
        filename = "test_turkish_export.xlsx"
        result = exporter.export_monthly_schedule(2025, 6, filename)
        
        if os.path.exists(filename):
            print(f"   ✅ Excel file created: {filename}")
            
            from openpyxl import load_workbook
            wb = load_workbook(filename)
            ws = wb.active
            
            if ws.title == "2025 Haziran":
                print(f"   ✅ Worksheet title in Turkish: {ws.title}")
            else:
                print(f"   ❌ Worksheet title not Turkish: {ws.title}")
        else:
            print("   ❌ Excel file not created")
    except Exception as e:
        print(f"   ❌ Excel export failed: {e}")

if __name__ == "__main__":
    test_turkish_months()
    print("\n🎉 Turkish month names test completed!")
