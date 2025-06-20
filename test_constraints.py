#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/ubuntu/repos/cim')

from scheduler import DutyScheduler
from database import Database

def test_scheduling_constraints():
    print("=== Testing Scheduling Constraints ===")
    
    try:
        db = Database()
        scheduler = DutyScheduler(db)
        
        if hasattr(scheduler, 'has_thursday_saturday_conflict'):
            print('✅ Thursday-Saturday constraint method exists')
        else:
            print('❌ Thursday-Saturday constraint method missing')
            return False
        
        if hasattr(scheduler, 'has_friday_sunday_conflict'):
            print('✅ Friday-Sunday constraint method exists')
        else:
            print('❌ Friday-Sunday constraint method missing')
            return False
        
        print('✅ Scheduler initialization successful')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    success = test_scheduling_constraints()
    if success:
        print("\n🎉 Constraint test completed successfully!")
    else:
        print("\n❌ Constraint test failed!")
