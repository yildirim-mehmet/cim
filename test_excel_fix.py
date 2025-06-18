#!/usr/bin/env python3
"""
Test script to verify Excel export parameter fix
"""

def test_excel_export_fix():
    """Test that the Excel export uses correct parameter"""
    print("Testing Excel export parameter fix...")
    
    with open('gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'initialname=' in content:
        print("❌ FAIL: Still using 'initialname' parameter")
        return False
    
    if 'initialfile=' in content:
        print("✅ PASS: Using correct 'initialfile' parameter")
        return True
    
    print("❌ FAIL: Neither initialname nor initialfile found")
    return False

def test_calendar_implementation():
    """Test that calendar view is implemented"""
    print("Testing calendar view implementation...")
    
    with open('gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('setup_calendar_view', 'Calendar setup method'),
        ('create_day_cell', 'Day cell creation method'),
        ('populate_calendar', 'Calendar population method'),
        ('get_day_color', 'Color coding method'),
        ('Pazartesi', 'Turkish weekday names'),
        ('#E6F3FF', 'Weekend color coding'),
        ('#FFE4B5', 'Holiday color coding')
    ]
    
    passed = 0
    for check, description in checks:
        if check in content:
            print(f"✅ PASS: {description}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
    
    return passed == len(checks)

if __name__ == "__main__":
    print("=== Testing Excel Export Fix and Calendar Implementation ===")
    
    excel_ok = test_excel_export_fix()
    calendar_ok = test_calendar_implementation()
    
    if excel_ok and calendar_ok:
        print("\n🎉 All tests passed! Ready to create PR.")
    else:
        print("\n❌ Some tests failed. Check implementation.")
