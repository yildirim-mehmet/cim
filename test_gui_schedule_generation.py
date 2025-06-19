#!/usr/bin/env python3

import sys
sys.path.append('.')
from scheduler import DutyScheduler
from database import Database
from datetime import date
import tkinter as tk
from tkinter import ttk

def test_gui_schedule_generation():
    """Test schedule generation and display in a simple GUI calendar view"""
    print("=== TESTING GUI SCHEDULE GENERATION ===")
    
    db = Database()
    scheduler = DutyScheduler(db)
    
    schedule = scheduler.generate_schedule(2025, 6)
    
    root = tk.Tk()
    root.title("Nöbet Programı Test - Haziran 2025")
    root.geometry("800x600")
    
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    for i, day in enumerate(days):
        label = ttk.Label(frame, text=day, font=('Arial', 10, 'bold'))
        label.grid(row=0, column=i, padx=2, pady=2, sticky='ew')
    
    schedule_dict = {d: (p, dt) for d, p, dt in schedule if p}
    
    current_date = date(2025, 6, 1)
    start_weekday = current_date.weekday()  # Monday = 0
    
    row = 1
    col = start_weekday
    
    for day in range(1, 31):  # June has 30 days
        current_date = date(2025, 6, day)
        
        if current_date in schedule_dict:
            person_id, day_type = schedule_dict[current_date]
            text = f"{day}\nPerson {person_id}\n{day_type}"
            
            bg_color = 'white'
            if day_type in ['Perşembe', 'Cuma', 'Cumartesi', 'Pazar']:
                if day_type == 'Perşembe':
                    bg_color = 'lightblue'
                elif day_type == 'Cuma':
                    bg_color = 'lightgreen'
                elif day_type == 'Cumartesi':
                    bg_color = 'lightcoral'
                elif day_type == 'Pazar':
                    bg_color = 'lightyellow'
        else:
            text = f"{day}\n(Boş)"
            bg_color = 'lightgray'
        
        label = ttk.Label(frame, text=text, background=bg_color, relief='solid', borderwidth=1)
        label.grid(row=row, column=col, padx=1, pady=1, sticky='ew', ipadx=5, ipady=5)
        
        col += 1
        if col > 6:
            col = 0
            row += 1
    
    for i in range(7):
        frame.columnconfigure(i, weight=1)
    
    analysis_frame = ttk.Frame(root)
    analysis_frame.pack(fill=tk.X, padx=10, pady=5)
    
    thursdays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 3]
    saturdays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 5]
    fridays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 4]
    sundays = [(d, p) for d, p, dt in schedule if p and d.weekday() == 6]
    
    thursday_saturday_pairs = 0
    for thursday_date, thursday_person in thursdays:
        for saturday_date, saturday_person in saturdays:
            if (saturday_person == thursday_person and 
                scheduler.get_week_start(thursday_date) != scheduler.get_week_start(saturday_date)):
                thursday_saturday_pairs += 1
                break
    
    friday_sunday_pairs = 0
    for friday_date, friday_person in fridays:
        for sunday_date, sunday_person in sundays:
            if (sunday_person == friday_person and 
                scheduler.get_week_start(friday_date) != scheduler.get_week_start(sunday_date)):
                friday_sunday_pairs += 1
                break
    
    analysis_text = f"""
PAIRING ANALYSIS:
Thursday-Saturday pairs: {thursday_saturday_pairs}/{len(thursdays)} = {(thursday_saturday_pairs/max(len(thursdays),1)*100):.1f}%
Friday-Sunday pairs: {friday_sunday_pairs}/{len(fridays)} = {(friday_sunday_pairs/max(len(fridays),1)*100):.1f}%

LEGEND:
Perşembe (Thursday) = Light Blue
Cuma (Friday) = Light Green  
Cumartesi (Saturday) = Light Coral
Pazar (Sunday) = Light Yellow
"""
    
    analysis_label = ttk.Label(analysis_frame, text=analysis_text, font=('Arial', 9))
    analysis_label.pack()
    
    print("GUI calendar opened. Check for visual pairing verification.")
    print("Close the window to continue...")
    
    root.mainloop()

if __name__ == "__main__":
    test_gui_schedule_generation()
