# Nöbet Programı - Duty Scheduling System ✅ Min/Max Kısıtlama Çözüldü!

A comprehensive duty scheduling management system for hospital/clinic personnel with Python GUI and SQLite backend.

## 🎯 YENİ: Min/Max Kısıtlama Sistemi Tamamen Çözüldü!

**SORUN ÇÖZÜLDÜ**: Min=3, Max=4 girdiğinizde artık tüm personel 3-4 nöbet alıyor!

### Önceki Durum (HATALI):
```
Min=3, Max=4 girdiğinizde:
Eda                 : 2 nöbet  ❌ (Min=3'ün altında)
Elif                : 2 nöbet  ❌ (Min=3'ün altında)
```

### Şimdiki Durum (MÜKEMMEL):
```
Min=3, Max=4 girdiğinizde:
✅ Tüm personel 3-4 nöbet alıyor
✅ Progressive penalty sistemi (1,000,000x ceza)
✅ Exponential priority scoring (100,000x bonus)
✅ Tamamen dinamik algorithm
```

### Test Sonuçları:
- ✅ **Min=3, Max=4**: MÜKEMMEL (Ana kullanıcı sorunu %100 çözüldü)
- ✅ **Min=3, Max=5**: MÜKEMMEL 
- ✅ **Min=2, Max=6**: MÜKEMMEL

## Features

- **Max-Min Priority System**: Ensures maximum 1 duty difference between personnel
- **Complex Constraint Handling**: Mazeret (exemptions), consecutive days, holiday conflicts
- **GUI Interface**: User-friendly tkinter-based interface
- **Excel Export**: Generate professional duty schedule reports
- **Database Management**: SQLite backend with comprehensive data management

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yildirim-mehmet/cim.git
cd cim
pip install -r requirements.txt
```

### 2. Test Console Functionality
```bash
# Test Max-Min priority system
python3 test_max_min_priority.py

# Test method availability
python3 test_gui_method_availability.py

# Test hybrid scheduler compatibility
python3 test_hybrid_scheduler.py
```

### 3. Run GUI Application
```bash
# Standard method
python3 main.py

# If you get tkinter errors, try system Python
/usr/bin/python3 main.py
```

## Expected Test Results

### Console Tests (Should Always Work)
```
🎯 TESTING MAX-MIN PRIORITY SYSTEM
Testing February 2025: Min duties: 3, Max duties: 4, Difference: 1
✅ Max-Min priority working (difference = 1)
🎉 ALL TESTS PASSED - Max-Min priority system working!
```

### GUI Tests (May Need tkinter Setup)
```
✅ Database.populate_sample_data() executed successfully
✅ DutyScheduler.generate_schedule_with_global_optimization() executed successfully
✅ Schedule quality: Min=3, Max=4, Difference=1
❌ GUI import failed: No module named '_tkinter'  # This is normal if tkinter not installed
```

## Troubleshooting

### Common Issue 1: AttributeError
```
AttributeError: 'Database' object has no attribute 'populate_sample_data'
```

**Solution**: This usually means you're using an outdated version or wrong Python environment.
```bash
git pull origin main  # Get latest code
python3 --version    # Check Python version (should be 3.8+)
```

### Common Issue 2: GUI Recursion Error
```
maximum recursion depth exceeded
```

**Solution**: This is actually a tkinter import failure, not recursion.
```bash
# Try system Python
/usr/bin/python3 main.py

# Or install tkinter
sudo apt-get install python3-tk  # Ubuntu/Debian
```

See [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for detailed troubleshooting.

## System Requirements

- Python 3.8 or higher
- tkinter (for GUI) - usually included with Python
- pandas, openpyxl (installed via requirements.txt)

## Usage

### Console Mode
```python
from database import Database
from scheduler import DutyScheduler

db = Database()
db.populate_sample_data()
scheduler = DutyScheduler(db)

# Generate schedule for February 2025
schedule = scheduler.generate_schedule(2025, 2)
```

### GUI Mode
1. Run `python3 main.py`
2. Select year and month
3. Click "Nöbet Hazırla" to generate schedule
4. Click "Excel'e Aktar" to export
5. Click "Kaydet" to save to database

## Architecture

- **database.py**: SQLite database management
- **scheduler.py**: Core scheduling algorithm with Max-Min priority
- **gui.py**: tkinter-based user interface
- **excel_exporter.py**: Excel report generation
- **main.py**: Application entry point

## Testing

The project includes comprehensive test suites:

- `test_max_min_priority.py`: Core algorithm testing
- `test_gui_method_availability.py`: Method existence verification
- `test_hybrid_scheduler.py`: Backward compatibility testing
- `test_gui_recursion_debug.py`: GUI import debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests to ensure functionality
4. Submit a pull request

## License

This project is developed for hospital/clinic duty scheduling management.

## Support

If you encounter issues:

1. Check [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for common solutions
2. Run the test suite to verify your environment
3. Ensure you have the latest code from main branch
4. Verify Python and tkinter installation

For persistent issues, please provide:
- Python version (`python3 --version`)
- Operating system
- Full error message
- Output of test commands
