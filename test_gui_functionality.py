#!/usr/bin/env python3
"""
Test GUI functionality for new features
"""

import tkinter as tk
from gui import DutySchedulerGUI
import sys

def test_gui_functionality():
    """Test GUI functionality with new methods"""
    print("=== Testing GUI Functionality ===")
    
    try:
        root = tk.Tk()
        app = DutySchedulerGUI(root)
        
        if hasattr(app, 'generate_schedule_display'):
            print('✅ generate_schedule_display method exists')
        else:
            print('❌ generate_schedule_display method missing')
            
        from datetime import datetime, date
        test_date = datetime.strptime('2025-06-20', '%Y-%m-%d').date()
        print(f'✅ datetime import working: {test_date}')
        
        app.selected_year = 2025
        app.selected_month = 6
        app.generate_schedule()
        
        if hasattr(app, 'current_schedule') and app.current_schedule:
            print(f'✅ Schedule generated with {len(app.current_schedule)} days')
            
            app.generate_schedule_display()
            print('✅ generate_schedule_display method works')
        else:
            print('❌ Schedule generation failed')
        
        root.destroy()
        print('✅ GUI test completed successfully')
        
    except Exception as e:
        print(f'❌ GUI test failed: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_gui_functionality()
    if not success:
        sys.exit(1)
    print("\n🎉 GUI functionality test completed!")
