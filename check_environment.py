#!/usr/bin/env python3
"""
Environment verification script for Nöbet Programı
Run this to check if your environment is properly set up
"""

import sys
import os

def check_python_version():
    """Check Python version compatibility"""
    print(f"Python version: {sys.version}")
    version_info = sys.version_info
    if version_info.major == 3 and version_info.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python version should be 3.8 or higher")
        return False

def check_database():
    """Check Database class and methods"""
    try:
        from database import Database
        print("✅ Database import successful")
        
        db = Database()
        print("✅ Database instance created")
        
        if hasattr(db, 'populate_sample_data'):
            print("✅ populate_sample_data method exists")
            
            db.populate_sample_data()
            print("✅ populate_sample_data method executed successfully")
            return True
        else:
            print("❌ populate_sample_data method missing")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_scheduler():
    """Check DutyScheduler class and methods"""
    try:
        from database import Database
        from scheduler import DutyScheduler
        print("✅ DutyScheduler import successful")
        
        db = Database()
        scheduler = DutyScheduler(db)
        print("✅ DutyScheduler instance created")
        
        if hasattr(scheduler, 'generate_schedule'):
            print("✅ generate_schedule method exists")
        else:
            print("❌ generate_schedule method missing")
            
        if hasattr(scheduler, 'generate_schedule_with_global_optimization'):
            print("✅ generate_schedule_with_global_optimization method exists")
        else:
            print("❌ generate_schedule_with_global_optimization method missing")
            
        return True
        
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        return False

def check_tkinter():
    """Check tkinter availability for GUI"""
    try:
        import tkinter as tk
        print("✅ tkinter import successful")
        
        root = tk.Tk()
        root.withdraw()  # Hide it immediately
        root.destroy()
        print("✅ tkinter GUI creation successful")
        return True
        
    except ImportError as e:
        print(f"❌ tkinter import error: {e}")
        print("   Solution: Install tkinter support")
        print("   Ubuntu/Debian: sudo apt-get install python3-tk")
        print("   CentOS/RHEL: sudo yum install tkinter")
        print("   macOS: brew install python-tk")
        return False
    except Exception as e:
        print(f"❌ tkinter error: {e}")
        print("   This might be a display issue (normal in headless environments)")
        return False

def check_dependencies():
    """Check required Python packages"""
    required_packages = ['pandas', 'openpyxl']
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            print(f"   Install with: pip install {package}")
            all_good = False
    
    return all_good

def check_files():
    """Check if required files exist"""
    required_files = [
        'database.py',
        'scheduler.py', 
        'gui.py',
        'main.py',
        'excel_exporter.py'
    ]
    
    all_good = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_good = False
    
    return all_good

def main():
    """Run all environment checks"""
    print("🔍 ENVIRONMENT VERIFICATION FOR NÖBET PROGRAMI")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_files),
        ("Dependencies", check_dependencies),
        ("Database Module", check_database),
        ("Scheduler Module", check_scheduler),
        ("tkinter (GUI)", check_tkinter),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Your environment is ready.")
        print("\nYou can now run:")
        print("  python3 test_max_min_priority.py  # Console tests")
        print("  python3 main.py                   # GUI application")
    else:
        print("⚠️  SOME CHECKS FAILED. Please fix the issues above.")
        print("\nFor detailed solutions, see ENVIRONMENT_SETUP.md")
    
    return all_passed

if __name__ == "__main__":
    main()
