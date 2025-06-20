#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

def test_turkish_months_constants():
    print("=== Testing Turkish Month Names Constants ===")
    
    expected_months = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
        7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    
    print("1. Testing GUI class constant...")
    try:
        with open('/home/ubuntu/repos/cim/gui.py', 'r') as f:
            gui_content = f.read()
        
        if 'TURKISH_MONTHS = {' in gui_content:
            print("   ✅ GUI has TURKISH_MONTHS constant")
            for month_num, expected_name in expected_months.items():
                if f'{month_num}: "{expected_name}"' in gui_content:
                    print(f"   ✅ Month {month_num}: {expected_name}")
                else:
                    print(f"   ❌ Month {month_num}: {expected_name} not found")
        else:
            print("   ❌ GUI missing TURKISH_MONTHS constant")
    except Exception as e:
        print(f"   ❌ Error reading GUI file: {e}")
    
    print("\n2. Testing ExcelExporter class constant...")
    try:
        with open('/home/ubuntu/repos/cim/excel_exporter.py', 'r') as f:
            excel_content = f.read()
        
        if 'TURKISH_MONTHS = {' in excel_content:
            print("   ✅ ExcelExporter has TURKISH_MONTHS constant")
            for month_num, expected_name in expected_months.items():
                if f'{month_num}: "{expected_name}"' in excel_content:
                    print(f"   ✅ Month {month_num}: {expected_name}")
                else:
                    print(f"   ❌ Month {month_num}: {expected_name} not found")
        else:
            print("   ❌ ExcelExporter missing TURKISH_MONTHS constant")
    except Exception as e:
        print(f"   ❌ Error reading ExcelExporter file: {e}")
    
    print("\n3. Testing GUI month combo replacement...")
    try:
        if 'self.TURKISH_MONTHS[i]' in gui_content and 'calendar.month_name[i]' not in gui_content:
            print("   ✅ GUI month combo uses Turkish months")
        else:
            print("   ❌ GUI month combo still uses English months")
    except:
        print("   ❌ Could not verify GUI month combo")
    
    print("\n4. Testing Excel export title replacement...")
    try:
        if 'self.TURKISH_MONTHS[month]' in excel_content and 'calendar.month_name[month]' not in excel_content:
            print("   ✅ Excel export uses Turkish months")
        else:
            print("   ❌ Excel export still uses English months")
    except:
        print("   ❌ Could not verify Excel export")
    
    print("\n5. Testing main screen refresh logic...")
    try:
        if 'if year == self.selected_year and month == self.selected_month:' in gui_content:
            print("   ✅ Main screen refresh logic added")
            if 'self.load_existing_schedule()' in gui_content and 'self.update_stats()' in gui_content:
                print("   ✅ Refresh calls load_existing_schedule and update_stats")
            else:
                print("   ❌ Missing refresh method calls")
        else:
            print("   ❌ Main screen refresh logic not found")
    except:
        print("   ❌ Could not verify refresh logic")

if __name__ == "__main__":
    test_turkish_months_constants()
    print("\n🎉 Turkish month names verification completed!")
