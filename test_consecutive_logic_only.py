#!/usr/bin/env python3
"""
Test script for consecutive duty detection logic without GUI
"""

from datetime import date
from database import Database
from scheduler import DutyScheduler

def test_consecutive_detection_logic():
    """Test consecutive duty detection functionality without GUI"""
    print("🔍 TESTING CONSECUTIVE DUTY DETECTION LOGIC")
    print("=" * 50)
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    test_schedule = [
        (date(2025, 10, 1), 1, 'Çarşamba'),   # Ayşe Wednesday
        (date(2025, 10, 2), 2, 'Perşembe'),   # Mehmet Thursday
        (date(2025, 10, 3), 3, 'Cuma'),       # Zeynep Friday
        (date(2025, 10, 4), 1, 'Cumartesi'),  # Ayşe Saturday
        (date(2025, 10, 5), 2, 'Pazar'),      # Mehmet Sunday
        (date(2025, 10, 10), 3, 'Cuma'),      # Zeynep Friday
        (date(2025, 10, 11), 3, 'Cumartesi'), # Zeynep Saturday (CONSECUTIVE!)
        (date(2025, 10, 12), 1, 'Pazar'),     # Ayşe Sunday
        (date(2025, 10, 15), 2, 'Çarşamba'),  # Mehmet Wednesday
        (date(2025, 10, 16), 2, 'Perşembe'),  # Mehmet Thursday (CONSECUTIVE!)
    ]
    
    consecutive = scheduler.detect_consecutive_assignments(test_schedule)
    print(f"Consecutive assignments detected: {len(consecutive)} assignments")
    
    expected_consecutive = [
        (date(2025, 10, 10), 3),  # Zeynep Oct 10
        (date(2025, 10, 11), 3),  # Zeynep Oct 11
        (date(2025, 10, 15), 2),  # Mehmet Oct 15
        (date(2025, 10, 16), 2),  # Mehmet Oct 16
    ]
    
    success = True
    for expected in expected_consecutive:
        if expected not in consecutive:
            print(f"❌ Missing consecutive assignment: {expected}")
            success = False
        else:
            print(f"✅ Found consecutive assignment: {expected}")
    
    print("\n📋 TESTING DISPLAY WITH HIGHLIGHTING")
    print("-" * 40)
    display = scheduler.display_schedule(test_schedule, 2025, 10)
    
    if "⚠️ UYARI: ARDIŞIK NÖBET ATAMALARI TESPİT EDİLDİ!" in display:
        print("✅ Warning message appears in display")
    else:
        print("❌ Warning message missing from display")
        success = False
    
    consecutive_markers = display.count("⚠️ ARDIŞIK NÖBET")
    expected_markers = 4  # 2 for Zeynep + 2 for Mehmet
    if consecutive_markers == expected_markers:
        print(f"✅ Correct number of consecutive markers: {consecutive_markers}")
    else:
        print(f"❌ Wrong number of consecutive markers: {consecutive_markers}, expected: {expected_markers}")
        success = False
    
    print("\n📄 DISPLAY OUTPUT:")
    print(display)
    
    return success

if __name__ == "__main__":
    print("🚀 STARTING CONSECUTIVE DUTY DETECTION LOGIC TEST")
    print("=" * 60)
    
    success = test_consecutive_detection_logic()
    
    print("\n" + "=" * 60)
    print("📊 CONSECUTIVE DUTY DETECTION TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ ALL TESTS PASSED - Consecutive detection logic working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check implementation")
    
    print("\nNext steps:")
    print("1. Test GUI visual highlighting manually")
    print("2. Test warning system integration")
    print("3. Test save/export blocking")
