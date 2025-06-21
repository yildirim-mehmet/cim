import sys
sys.path.append('.')

def test_gui_import():
    """Test GUI import to check for recursion issues"""
    print("🧪 TESTING GUI IMPORT FOR RECURSION ISSUES")
    
    try:
        print("Importing tkinter...")
        import tkinter as tk
        print("✅ tkinter imported successfully")
        
        print("Importing database...")
        from database import Database
        print("✅ Database imported successfully")
        
        print("Importing scheduler...")
        from scheduler import DutyScheduler
        print("✅ DutyScheduler imported successfully")
        
        print("Importing excel_exporter...")
        from excel_exporter import ExcelExporter
        print("✅ ExcelExporter imported successfully")
        
        print("Importing gui...")
        from gui import DutySchedulerGUI
        print("✅ DutySchedulerGUI imported successfully")
        
        print("Creating tkinter root...")
        root = tk.Tk()
        root.withdraw()  # Hide the window
        print("✅ tkinter root created successfully")
        
        print("Creating GUI instance...")
        app = DutySchedulerGUI(root)
        print("✅ DutySchedulerGUI instance created successfully")
        
        print("Destroying root...")
        root.destroy()
        print("✅ GUI test completed successfully")
        
        return True
        
    except RecursionError as e:
        print(f"❌ RecursionError detected: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_import()
    if success:
        print("\n✅ NO RECURSION ISSUES DETECTED!")
    else:
        print("\n❌ RECURSION OR OTHER ISSUES DETECTED!")
