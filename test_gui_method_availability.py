import sys
sys.path.append('.')

def test_gui_method_availability():
    """Test that all methods required by GUI are available and working"""
    print("🧪 TESTING GUI METHOD AVAILABILITY")
    
    try:
        from database import Database
        from scheduler import DutyScheduler
        
        db = Database()
        print("✅ Database class imported successfully")
        
        if hasattr(db, 'populate_sample_data'):
            print("✅ Database.populate_sample_data method exists")
            db.populate_sample_data()
            print("✅ Database.populate_sample_data() executed successfully")
        else:
            print("❌ Database.populate_sample_data method missing")
            return False
        
        scheduler = DutyScheduler(db)
        print("✅ DutyScheduler class imported successfully")
        
        if hasattr(scheduler, 'generate_schedule_with_global_optimization'):
            print("✅ DutyScheduler.generate_schedule_with_global_optimization method exists")
            schedule = scheduler.generate_schedule_with_global_optimization(2025, 2, 0, 10)
            print("✅ DutyScheduler.generate_schedule_with_global_optimization() executed successfully")
            
            person_counts = {}
            for _, person_id, _ in schedule:
                if person_id:
                    person_counts[person_id] = person_counts.get(person_id, 0) + 1
            
            if person_counts:
                min_duties = min(person_counts.values())
                max_duties = max(person_counts.values())
                diff = max_duties - min_duties
                print(f"✅ Schedule quality: Min={min_duties}, Max={max_duties}, Difference={diff}")
                
                if diff <= 1:
                    print("✅ Max-Min priority maintained (difference ≤ 1)")
                else:
                    print(f"❌ Unequal distribution (difference = {diff} > 1)")
                    return False
        else:
            print("❌ DutyScheduler.generate_schedule_with_global_optimization method missing")
            return False
        
        try:
            from gui import DutySchedulerGUI
            print("✅ GUI class can be imported successfully")
        except Exception as e:
            print(f"❌ GUI import failed: {e}")
            return False
        
        print("🎉 ALL GUI METHODS AVAILABLE AND WORKING!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_method_availability()
    if success:
        print("\n✅ VERIFICATION COMPLETE: User's AttributeError issues are fixed!")
    else:
        print("\n❌ VERIFICATION FAILED: Issues still exist!")
