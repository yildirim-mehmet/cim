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
        cursor.execute("SELECT id, ad, statu FROM Personel WHERE Aktif = 1 OR Aktif = 'true'")
        personnel = cursor.fetchall()
        conn.close()
        return personnel
    
    def get_day_values(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, deger FROM GunDeger")
        day_values = {row[0]: {'name': row[1], 'value': row[2]} for row in cursor.fetchall()}
        conn.close()
        
        if not day_values:
            default_values = [
                (1, 'Pazartesi', 1.2), (2, 'Salı', 1.1), (3, 'Çarşamba', 1.1),
                (4, 'Perşembe', 0.9), (5, 'Cuma', 1.4), (6, 'Cumartesi', 2.0),
                (7, 'Pazar', 1.6), (8, 'Resmi Tatil', 2.2)
            ]
            for dv in default_values:
                day_values[dv[0]] = {'name': dv[1], 'value': dv[2]}
        
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
    
    def calculate_priority_score(self, person_id, stats, total_avg_count, total_avg_value, target_date, existing_schedule, day_type, monthly_stats, personnel_ids):
        """
        Gelişmiş öncelik puanı hesaplama
        Temel adalet + zorunlu eşleştirme bonusu + dağıtım dengeleme + tatil döngüsü
        """
        person_stats = stats[person_id]
        
        count_diff = total_avg_count - person_stats['count']
        value_diff = total_avg_value - person_stats['total_value']
        base_score = count_diff * 2 + value_diff
        
        pairing_bonus = self.calculate_pairing_bonus(person_id, target_date, existing_schedule)
        
        distribution_penalty = -50 if self.has_same_day_distribution_conflict(person_id, target_date, day_type, monthly_stats) else 0
        
        cycle_bonus = 100 if self.should_prioritize_for_holiday_cycle(person_id, target_date, day_type, personnel_ids, existing_schedule) else 0
        
        return base_score + pairing_bonus + distribution_penalty + cycle_bonus
    

    
    def generate_schedule(self, year, month):
        """
        Gelişmiş nöbet programı oluşturma
        Zorunlu eşleştirme, dağıtım dengeleme ve tatil döngüsü ile
        """
        personnel = self.get_active_personnel()
        day_values = self.get_day_values()
        holidays = self.get_holidays(year, month)
        exemptions = self.get_exemptions(year, month)
        
        if not personnel:
            return []
        
        personnel_ids = [p[0] for p in personnel]
        stats = self.get_personnel_duty_stats(personnel_ids)
        monthly_stats = self.get_monthly_duty_stats(personnel_ids, year, month)
        
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
            
            if day_value_id in day_values:
                day_info = day_values[day_value_id]
                day_type = day_info['name']
            else:
                weekday_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
                weekday_values = [1.2, 1.1, 1.1, 0.9, 1.4, 2.0, 1.6]
                
                if 0 <= weekday < 7:
                    day_type = weekday_names[weekday]
                    day_info = {'name': day_type, 'value': weekday_values[weekday]}
                else:
                    day_info = {'name': 'Bilinmeyen', 'value': 1.0}
                    day_type = 'Bilinmeyen'
            
            eligible_personnel = []
            for person_id in personnel_ids:
                if day == 1 and person_id == last_month_duty_person:
                    continue
                
                if person_id in exemption_dict and current_date in exemption_dict[person_id]:
                    if not exemption_dict[person_id][current_date]:
                        continue
                
                if self.is_ramazan_kurban_conflict(person_id, current_date, schedule):
                    continue
                
                if self.has_thursday_saturday_conflict(person_id, current_date, schedule):
                    continue
                
                if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                    continue
                
                if self.has_month_boundary_consecutive_conflict(person_id, current_date):
                    continue
                
                priority_score = self.calculate_priority_score(
                    person_id, stats, avg_count, avg_value, current_date, 
                    schedule, day_type, monthly_stats, personnel_ids
                )
                eligible_personnel.append((person_id, priority_score))
            
            if eligible_personnel:
                mandatory_pairing_candidates = []
                regular_candidates = []
                
                for person_id, score in eligible_personnel:
                    pairing_bonus = self.calculate_pairing_bonus(person_id, current_date, schedule)
                    
                    if pairing_bonus > 0:
                        mandatory_pairing_candidates.append((person_id, score + pairing_bonus + 2000))
                    else:
                        regular_candidates.append((person_id, score))
                
                if mandatory_pairing_candidates:
                    mandatory_pairing_candidates.sort(key=lambda x: x[1], reverse=True)
                    selected_person_id = mandatory_pairing_candidates[0][0]
                else:
                    regular_candidates.sort(key=lambda x: x[1], reverse=True)
                    selected_person_id = regular_candidates[0][0]
                
                person_name = next(p[1] for p in personnel if p[0] == selected_person_id)
                schedule.append((current_date, selected_person_id, day_info['name']))
                
                stats[selected_person_id]['count'] += 1
                stats[selected_person_id]['total_value'] += day_info['value']
                
                if selected_person_id not in monthly_stats:
                    monthly_stats[selected_person_id] = {}
                if day_type not in monthly_stats[selected_person_id]:
                    monthly_stats[selected_person_id][day_type] = 0
                monthly_stats[selected_person_id][day_type] += 1
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
    
    def get_monthly_duty_stats(self, personnel_ids, year, month):
        """
        Aylık nöbet istatistiklerini getir - Dağıtım dengeleme için
        Her personelin o ay hangi gün türlerinde kaç nöbet tuttuğunu takip eder
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        for person_id in personnel_ids:
            cursor.execute("""
                SELECT gd.ad, COUNT(*) as count
                FROM Nobet n
                JOIN GunDeger gd ON n.gunDegerId = gd.id
                WHERE n.personelId = ? AND strftime('%Y-%m', n.tarih) = ?
                GROUP BY gd.ad
            """, (person_id, f"{year:04d}-{month:02d}"))
            
            day_type_counts = dict(cursor.fetchall())
            stats[person_id] = day_type_counts
        
        conn.close()
        return stats
    
    def get_week_start(self, target_date):
        """
        Haftanın başlangıç tarihini hesapla (Pazartesi)
        """
        return target_date - timedelta(days=target_date.weekday())
    
    def needs_thursday_saturday_pairing(self, person_id, target_date, existing_schedule):
        """
        Perşembe-Cumartesi zorunlu eşleştirme kontrolü - DÜZELTME
        1-Cumartesi yazılmışsa Perşembe yazılmalı
        2-Perşembe yazılmışsa Cumartesi yazılmalı
        """
        target_week = self.get_week_start(target_date)
        
        if target_date.weekday() == 5:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 3 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    return True
        
        if target_date.weekday() == 3:
            has_saturday_in_different_week = False
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 5 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    has_saturday_in_different_week = True
                    break
            
            if not has_saturday_in_different_week:
                saturdays_in_month = []
                for day in range(1, 32):
                    try:
                        test_date = date(target_date.year, target_date.month, day)
                        if test_date.weekday() == 5 and self.get_week_start(test_date) != target_week:
                            saturdays_in_month.append(test_date)
                    except ValueError:
                        break
                
                if saturdays_in_month:
                    return True
        
        return False
    
    def needs_friday_sunday_pairing(self, person_id, target_date, existing_schedule):
        """
        Cuma-Pazar zorunlu eşleştirme kontrolü - DÜZELTME
        3-Pazar yazılmışsa Cuma yazılmalı
        4-Cuma yazılmışsa Pazar yazılmalı
        """
        target_week = self.get_week_start(target_date)
        
        if target_date.weekday() == 6:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 4 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    return True
        
        if target_date.weekday() == 4:
            has_sunday_in_different_week = False
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 6 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    has_sunday_in_different_week = True
                    break
            
            if not has_sunday_in_different_week:
                sundays_in_month = []
                for day in range(1, 32):
                    try:
                        test_date = date(target_date.year, target_date.month, day)
                        if test_date.weekday() == 6 and self.get_week_start(test_date) != target_week:
                            sundays_in_month.append(test_date)
                    except ValueError:
                        break
                
                if sundays_in_month:
                    return True
        
        return False
    
    def calculate_pairing_bonus(self, person_id, target_date, existing_schedule):
        """
        Zorunlu eşleştirme bonusu hesaplama - GELİŞTİRİLMİŞ
        1-Cumartesi yazılmışsa Perşembe yazılmalı
        2-Perşembe yazılmışsa Cumartesi yazılmalı  
        3-Pazar yazılmışsa Cuma yazılmalı
        4-Cuma yazılmışsa Pazar yazılmalı
        """
        bonus = 0
        weekday = target_date.weekday()
        target_week = self.get_week_start(target_date)
        
        if weekday == 5:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 3 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 1000
                    break
        
        elif weekday == 3:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 5 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 1000
                    break
        
        elif weekday == 6:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 4 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 1000
                    break
        
        elif weekday == 4:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 6 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 1000
                    break
        
        return bonus
    
    def has_same_day_distribution_conflict(self, person_id, target_date, day_type, monthly_stats):
        """
        Aynı gün türü dağıtım çakışması kontrolü - GELİŞTİRİLMİŞ
        Kritik günlerde (Cuma, Cumartesi, Pazar) aynı kişiye tekrar atama engelleme
        """
        if person_id not in monthly_stats:
            return False
        
        person_monthly = monthly_stats[person_id]
        
        critical_days = ['Cuma', 'Cumartesi', 'Pazar']
        if day_type in critical_days:
            for critical_day in critical_days:
                if critical_day in person_monthly and person_monthly[critical_day] > 0:
                    return True
        
        if day_type in person_monthly and person_monthly[day_type] > 0:
            return True
        
        return False
    
    def get_holiday_cycle_position(self, person_id, personnel_ids):
        """
        10 kişilik tatil nöbet döngüsündeki pozisyonu hesapla
        Personel ID'sine göre döngüsel sıralama
        """
        sorted_personnel = sorted(personnel_ids)
        if person_id in sorted_personnel:
            return sorted_personnel.index(person_id) % 10
        return 0
    
    def should_prioritize_for_holiday_cycle(self, person_id, target_date, day_type, personnel_ids, existing_schedule):
        """
        Tatil günü döngüsel öncelik kontrolü
        Cumartesi, Pazar ve tatil günleri için 10 kişilik döngü
        """
        if day_type not in ['Cumartesi', 'Pazar'] and 'Tatil' not in day_type:
            return False
        
        cycle_position = self.get_holiday_cycle_position(person_id, personnel_ids)
        
        holiday_weekend_count = 0
        for scheduled_date, _, scheduled_day_type in existing_schedule:
            if (scheduled_date < target_date and 
                (scheduled_day_type in ['Cumartesi', 'Pazar'] or 'Tatil' in scheduled_day_type)):
                holiday_weekend_count += 1
        
        expected_position = holiday_weekend_count % 10
        return cycle_position == expected_position
    
    def has_month_boundary_consecutive_conflict(self, person_id, target_date):
        """
        Ay sonu-ay başı ardışık gün çakışması kontrolü
        Önceki ayın son günü veya sonraki ayın ilk günü kontrolü
        """
        if target_date.day == 1:
            return self.get_last_month_last_duty(target_date.year, target_date.month) == person_id
        
        last_day = calendar.monthrange(target_date.year, target_date.month)[1]
        if target_date.day == last_day:
            next_month = target_date.month + 1 if target_date.month < 12 else 1
            next_year = target_date.year if target_date.month < 12 else target_date.year + 1
            
            first_day_next_month = date(next_year, next_month, 1)
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT personelId FROM Nobet WHERE tarih = ?", (first_day_next_month,))
            result = cursor.fetchone()
            conn.close()
            
            return result and result[0] == person_id
        
        return False
    
    def validate_manual_change(self, person_id, target_date, year, month):
        """
        Manuel değişiklik doğrulama
        Ardışık gün ve ay sınırı çakışmalarını kontrol eder
        """
        warnings = []
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tarih, personelId FROM Nobet 
            WHERE strftime('%Y-%m', tarih) = ?
            ORDER BY tarih
        """, (f"{year:04d}-{month:02d}",))
        
        existing_duties = cursor.fetchall()
        conn.close()
        
        prev_day = target_date - timedelta(days=1)
        next_day = target_date + timedelta(days=1)
        
        for duty_date_str, duty_person_id in existing_duties:
            duty_date = date.fromisoformat(duty_date_str)
            if duty_person_id == person_id and (duty_date == prev_day or duty_date == next_day):
                warnings.append(f"UYARI: {duty_date.strftime('%d.%m.%Y')} tarihinde ardışık nöbet!")
        
        if self.has_month_boundary_consecutive_conflict(person_id, target_date):
            warnings.append("UYARI: Ay sonu/başı ardışık nöbet çakışması!")
        
        return warnings

    def get_person_name(self, person_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ad FROM Personel WHERE id = ?", (person_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Bilinmeyen"
