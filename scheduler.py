import sqlite3
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict
import random

class DutyScheduler:
    def __init__(self, database):
        self.db = database
        
    def get_active_personnel(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, statu FROM Personel WHERE Aktif = 1")
        personnel = cursor.fetchall()
        conn.close()
        return personnel
    
    def get_day_values(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, deger FROM GunDeger")
        day_values = {row[0]: {'name': row[1], 'value': row[2]} for row in cursor.fetchall()}
        conn.close()
        return day_values
    
    def get_holidays(self, year, month):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gunDegerId, ad, tarih FROM Tatil 
            WHERE strftime('%Y-%m', tarih) = ?
        """, (f"{year:04d}-{month:02d}",))
        holidays = cursor.fetchall()
        conn.close()
        return holidays
    
    def get_exemptions(self, year, month):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT personelId, tarih, tut FROM Mazeret 
            WHERE strftime('%Y-%m', tarih) = ?
        """, (f"{year:04d}-{month:02d}",))
        exemptions = cursor.fetchall()
        conn.close()
        return exemptions
    
    def get_personnel_duty_stats(self, personnel_ids):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        for person_id in personnel_ids:
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(deger), 0) as total_value 
                FROM Nobet WHERE personelId = ?
            """, (person_id,))
            result = cursor.fetchone()
            stats[person_id] = {
                'count': result[0] if result[0] else 0,
                'total_value': float(result[1]) if result[1] else 0.0
            }
        
        conn.close()
        return stats
    
    def get_last_month_last_duty(self, year, month):
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        
        last_day = calendar.monthrange(prev_year, prev_month)[1]
        last_date = date(prev_year, prev_month, last_day)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT personelId FROM Nobet WHERE tarih = ?", (last_date,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_weekday_id(self, weekday):
        weekday_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}
        return weekday_mapping.get(weekday, 1)
    
    def is_ramazan_kurban_conflict(self, person_id, target_date, existing_schedule):
        ramazan_dates = set()
        kurban_dates = set()
        
        for scheduled_date, scheduled_person, day_type in existing_schedule:
            if scheduled_person == person_id:
                if 'Ramazan' in day_type:
                    ramazan_dates.add(scheduled_date)
                elif 'Kurban' in day_type:
                    kurban_dates.add(scheduled_date)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ad FROM Tatil WHERE tarih = ?", (target_date,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            holiday_name = result[0]
            if 'Ramazan' in holiday_name and kurban_dates:
                return True
            if 'Kurban' in holiday_name and ramazan_dates:
                return True
        
        return False
    
    def has_thursday_saturday_conflict(self, person_id, target_date, existing_schedule):
        target_weekday = target_date.weekday()
        
        if target_weekday not in [3, 5]:  # Thursday=3, Saturday=5
            return False
        
        target_week_start = target_date - timedelta(days=target_weekday)
        target_week_end = target_week_start + timedelta(days=6)
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and target_week_start <= scheduled_date <= target_week_end:
                scheduled_weekday = scheduled_date.weekday()
                if (target_weekday == 3 and scheduled_weekday == 5) or (target_weekday == 5 and scheduled_weekday == 3):
                    return True
        
        return False
    
    def has_consecutive_days_conflict(self, person_id, target_date, existing_schedule):
        prev_day = target_date - timedelta(days=1)
        next_day = target_date + timedelta(days=1)
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and (scheduled_date == prev_day or scheduled_date == next_day):
                return True
        
        return False
    
    def get_day_type_count(self, person_id, target_date, existing_schedule):
        target_day_name = calendar.day_name[target_date.weekday()]
        day_type_count = 0
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id:
                if calendar.day_name[scheduled_date.weekday()] == target_day_name:
                    day_type_count += 1
        
        return day_type_count
    
    def has_day_type_limit_conflict(self, person_id, target_date, existing_schedule, max_same_day_type=2):
        return self.get_day_type_count(person_id, target_date, existing_schedule) >= max_same_day_type
    
    def calculate_priority_score(self, person_id, stats, total_avg_count, total_avg_value, target_date, existing_schedule, min_nob=0, max_nob=10):
        person_stats = stats[person_id]
        
        count_diff = total_avg_count - person_stats['count']
        value_diff = total_avg_value - person_stats['total_value']
        
        base_score = count_diff * 2 + value_diff
        
        if person_stats['count'] < min_nob:
            base_score += 100
        
        day_type_count = self.get_day_type_count(person_id, target_date, existing_schedule)
        if day_type_count == 0:
            base_score += 50
        elif day_type_count == 1:
            base_score -= 25
        
        return base_score
    
    def generate_schedule(self, year, month, min_nob=0, max_nob=10):
        personnel = self.get_active_personnel()
        day_values = self.get_day_values()
        holidays = self.get_holidays(year, month)
        exemptions = self.get_exemptions(year, month)
        
        personnel_ids = [p[0] for p in personnel]
        stats = self.get_personnel_duty_stats(personnel_ids)
        
        total_count = sum(s['count'] for s in stats.values())
        total_value = sum(s['total_value'] for s in stats.values())
        avg_count = total_count / len(personnel_ids) if personnel_ids else 0
        avg_value = total_value / len(personnel_ids) if personnel_ids else 0
        
        last_month_duty_person = self.get_last_month_last_duty(year, month)
        
        holiday_dict = {date.fromisoformat(h[2]): h[0] for h in holidays}
        exemption_dict = defaultdict(dict)
        for e in exemptions:
            exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]
        
        days_in_month = calendar.monthrange(year, month)[1]
        schedule = []
        
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(weekday)
            
            if day_value_id not in day_values:
                day_value_id = 1
            
            day_info = day_values[day_value_id]
            
            eligible_personnel = []
            for person_id in personnel_ids:
                if day == 1 and person_id == last_month_duty_person:
                    continue
                
                if person_id in exemption_dict and current_date in exemption_dict[person_id]:
                    if not exemption_dict[person_id][current_date]:
                        continue
                
                if stats[person_id]['count'] >= max_nob:
                    continue
                
                if self.is_ramazan_kurban_conflict(person_id, current_date, schedule):
                    continue
                
                if self.has_thursday_saturday_conflict(person_id, current_date, schedule):
                    continue
                
                if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                    continue
                
                if self.has_day_type_limit_conflict(person_id, current_date, schedule):
                    continue
                
                priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value, current_date, schedule, min_nob, max_nob)
                eligible_personnel.append((person_id, priority_score))
            
            if eligible_personnel:
                eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                selected_person_id = eligible_personnel[0][0]
                
                person_name = next(p[1] for p in personnel if p[0] == selected_person_id)
                schedule.append((current_date, selected_person_id, day_info['name']))
                
                stats[selected_person_id]['count'] += 1
                stats[selected_person_id]['total_value'] += day_info['value']
            else:
                schedule.append((current_date, None, day_info['name']))
        
        return schedule
    
    def save_schedule(self, schedule, year, month):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Nobet WHERE strftime('%Y-%m', tarih) = ?", (f"{year:04d}-{month:02d}",))
        
        day_values = self.get_day_values()
        day_value_lookup = {v['name']: k for k, v in day_values.items()}
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                person_name = self.get_person_name(person_id)
                day_value_id = day_value_lookup.get(day_type, 1)
                day_value = day_values[day_value_id]['value']
                
                cursor.execute("""
                    INSERT INTO Nobet (personelId, gunDegerId, ad, deger, tarih, kayit, degisiklik)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (person_id, day_value_id, person_name, day_value, scheduled_date, datetime.now(), 0))
        
        conn.commit()
        conn.close()
    
    def get_person_name(self, person_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ad FROM Personel WHERE id = ?", (person_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Bilinmeyen"
    
    def display_schedule(self, schedule, year, month):
        personnel_counts = defaultdict(int)
        personnel_names = {}
        
        personnel = self.get_active_personnel()
        for person_id, name, status in personnel:
            personnel_names[person_id] = name
            personnel_counts[person_id] = 0
        
        for _, person_id, _ in schedule:
            if person_id:
                personnel_counts[person_id] += 1
        
        month_name = calendar.month_name[month]
        output = [f"\n{month_name} {year} Nöbet Listesi"]
        output.append("=" * 30)
        
        for day in schedule:
            date_obj, person_id, day_type = day
            day_name = calendar.day_name[date_obj.weekday()]
            date_str = date_obj.strftime("%d.%m.%Y")
            
            if person_id:
                person_name = personnel_names.get(person_id, "Bilinmeyen")
                count = personnel_counts[person_id]
                line = f"{date_str} {day_name.ljust(10)} - {day_type.ljust(12)}: {person_name} [{count}]"
            else:
                line = f"{date_str} {day_name.ljust(10)} - {day_type.ljust(12)}: ATAMA YAPILMADI"
            
            output.append(line)
        
        output.append("\nPersonel Nöbet Özeti:")
        output.append("-" * 25)
        for person_id, count in sorted(personnel_counts.items(), key=lambda x: x[1], reverse=True):
            output.append(f"{personnel_names[person_id].ljust(20)}: {count} nöbet")
        
        return "\n".join(output)
