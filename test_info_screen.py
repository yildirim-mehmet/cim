#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

import tkinter as tk
from gui import DutySchedulerGUI

def test_info_screen():
    print("=== Testing Info Screen Implementation ===")
    
    try:
        root = tk.Tk()
        app = DutySchedulerGUI(root)
        
        if hasattr(app, 'open_info_window'):
            print('✅ Info window method exists')
        else:
            print('❌ Info window method missing')
            return False
        
        print('✅ GUI initialization successful')
        root.destroy()
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    success = test_info_screen()
    if success:
        print("\n🎉 Info screen test completed successfully!")
    else:
        print("\n❌ Info screen test failed!")
