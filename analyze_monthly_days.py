#!/usr/bin/env python3
"""
Analyze how many of each day type (Monday-Sunday) occur in different months
"""
import calendar
from datetime import date, timedelta

def analyze_monthly_day_distribution():
    """Analyze day distribution for different months"""
    print("=== MONTHLY DAY DISTRIBUTION ANALYSIS ===\n")
    
    # Test different months
    test_months = [
        (2025, 1),   # January
        (2025, 2),   # February (28 days)
        (2025, 6),   # June (30 days)
        (2025, 7),   # July (31 days)
        (2024, 2),   # February leap year (29 days)
    ]
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for year, month in test_months:
        print(f"--- {calendar.month_name[month]} {year} ---")
        
        # Count each day type
        day_counts = [0] * 7  # Monday=0, Sunday=6
        
        # Get all days in the month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        current_date = first_day
        while current_date <= last_day:
            day_of_week = current_date.weekday()  # Monday=0, Sunday=6
            day_counts[day_of_week] += 1
            current_date += timedelta(days=1)
        
        # Display results
        total_days = sum(day_counts)
        print(f"Total days: {total_days}")
        for i, count in enumerate(day_counts):
            print(f"{day_names[i]}: {count}")
        
        # Check maximum occurrences
        max_count = max(day_counts)
        min_count = min(day_counts)
        print(f"Max occurrences: {max_count}, Min occurrences: {min_count}")
        
        if max_count > 2:
            print(f"⚠️  Some days occur more than 2 times ({max_count})")
        else:
            print("✅ All days occur ≤2 times")
        
        print()

if __name__ == "__main__":
    analyze_monthly_day_distribution()
