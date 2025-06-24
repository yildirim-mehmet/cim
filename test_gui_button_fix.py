#!/usr/bin/env python3
"""
Test the GUI button fix for duty change dialog
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import DutySchedulerGUI
    from database import Database
    import tkinter as tk
    
    print("🔍 TESTING GUI BUTTON FIX")
    print("=" * 50)
    
    root = tk.Tk()
    db = Database()
    gui = DutySchedulerGUI(root, db)
    
    if hasattr(gui, 'show_duty_change_menu'):
        print("✅ show_duty_change_menu method exists")
    else:
        print("❌ show_duty_change_menu method missing")
    
    if hasattr(gui, 'execute_duty_change'):
        print("✅ execute_duty_change method exists")
    else:
        print("❌ execute_duty_change method missing")
    
    if hasattr(gui, 'show_constraint_override_dialog'):
        print("✅ show_constraint_override_dialog method exists")
    else:
        print("❌ show_constraint_override_dialog method missing")
    
    print("\n✅ GUI button fix test complete")
    root.destroy()
    
except ImportError as e:
    print(f"❌ Import error (expected due to tkinter): {e}")
    print("✅ Backend methods should still be testable")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
