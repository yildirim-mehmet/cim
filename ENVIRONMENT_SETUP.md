# Environment Setup Guide

## Common Issues and Solutions

### 1. AttributeError: 'Database' object has no attribute 'populate_sample_data'

**Root Cause**: This error typically occurs when using an outdated version of the code or incorrect Python environment.

**Solutions**:
```bash
# Ensure you have the latest code
git pull origin main

# Use the correct Python version
python3 --version  # Should be 3.8 or higher

# Verify the method exists
python3 -c "from database import Database; print(hasattr(Database(), 'populate_sample_data'))"
```

### 2. GUI "maximum recursion depth exceeded" Error

**Root Cause**: This is actually a tkinter import failure, not a real recursion issue.

**Solutions**:

#### Option 1: Use System Python (Recommended)
```bash
# Instead of: python3 main.py
/usr/bin/python3 main.py
```

#### Option 2: Install tkinter Support
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
# or
sudo dnf install python3-tkinter

# macOS (with Homebrew)
brew install python-tk
```

#### Option 3: Rebuild Python with tkinter
If using pyenv or custom Python installation:
```bash
# Install tkinter development packages first
sudo apt-get install tk-dev

# Then rebuild Python
pyenv install 3.12.5
```

### 3. Testing Your Environment

Run these commands to verify your setup:

```bash
# Test console functionality
python3 test_max_min_priority.py

# Test GUI method availability
python3 test_gui_method_availability.py

# Test hybrid scheduler compatibility
python3 test_hybrid_scheduler.py

# Test GUI imports (will show tkinter issues)
python3 test_gui_recursion_debug.py
```

### 4. Expected Test Results

**Console Tests (should work)**:
```
✅ Max-Min priority working (difference = 1)
✅ All constraints preserved
✅ Database.populate_sample_data() executed successfully
```

**GUI Tests (may show tkinter issues)**:
```
❌ GUI import failed: No module named '_tkinter'
```

This is normal if tkinter is not properly installed. Use the solutions above to fix it.

## Quick Start for New Users

```bash
# Clone the repository
git clone https://github.com/yildirim-mehmet/cim.git
cd cim

# Install dependencies
pip install -r requirements.txt

# Test console functionality (should always work)
python3 test_max_min_priority.py

# Test GUI (may need tkinter setup)
python3 main.py
```

## Troubleshooting

### If you still get AttributeError after following the guide:
1. Check your Python version: `python3 --version`
2. Verify you're in the correct directory: `ls -la` (should show database.py, scheduler.py, etc.)
3. Check if the method exists: `python3 -c "from database import Database; db = Database(); db.populate_sample_data()"`

### If GUI still shows recursion errors:
1. The error is likely tkinter-related, not actual recursion
2. Try using system Python: `/usr/bin/python3 main.py`
3. Install tkinter support as shown above
4. Check tkinter availability: `python3 -c "import tkinter; print('tkinter works')"`

## Environment Verification Script

Create and run this script to check your environment:

```python
#!/usr/bin/env python3
import sys
print(f"Python version: {sys.version}")

try:
    from database import Database
    print("✅ Database import successful")
    
    db = Database()
    print("✅ Database instance created")
    
    db.populate_sample_data()
    print("✅ populate_sample_data method works")
    
except Exception as e:
    print(f"❌ Database error: {e}")

try:
    import tkinter
    print("✅ tkinter import successful")
except Exception as e:
    print(f"❌ tkinter error: {e}")

try:
    from scheduler import DutyScheduler
    scheduler = DutyScheduler(Database())
    print("✅ DutyScheduler import successful")
    
    if hasattr(scheduler, 'generate_schedule_with_global_optimization'):
        print("✅ generate_schedule_with_global_optimization method exists")
    else:
        print("❌ generate_schedule_with_global_optimization method missing")
        
except Exception as e:
    print(f"❌ Scheduler error: {e}")
```

Save this as `check_environment.py` and run: `python3 check_environment.py`
