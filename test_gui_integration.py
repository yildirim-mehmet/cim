#!/usr/bin/env python3
"""
Test GUI integration for new features
"""

import tkinter as tk
from gui import DutySchedulerGUI

def test_gui_integration():
    """Test that GUI can be instantiated and has new methods"""
    print("=== Testing GUI Integration ===")
    
    try:
        root = tk.Tk()
        app = DutySchedulerGUI(root)
        
        methods = ['open_mazeret_window', 'show_duty_change_menu']
        for method in methods:
            if hasattr(app, method):
                print(f'✅ Method {method} exists')
            else:
                print(f'❌ Method {method} missing')
        
        if callable(getattr(app, 'open_mazeret_window', None)):
            print('✅ Mazeret functionality is accessible')
        else:
            print('❌ Mazeret functionality not accessible')
            
        root.destroy()
        print('✅ GUI instantiation successful')
        
    except Exception as e:
        print(f'❌ GUI test failed: {e}')

if __name__ == "__main__":
    test_gui_integration()
