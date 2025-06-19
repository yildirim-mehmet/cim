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
        İKİ AŞAMALI ZORUNLU EŞLEŞTİRME ALGORİTMASI
        AŞAMA 1: Zorunlu eşleştirmeleri (Perşembe-Cumartesi, Cuma-Pazar) önce ata
        AŞAMA 2: Kalan günleri eşit dağıtım ile ata
        """
        personnel = self.get_active_personnel()
        day_values = self.get_day_values()
        holidays = self.get_holidays(year, month)
        exemptions = self.get_exemptions(year, month)
        
        if not personnel:
            return []
        
        personnel_ids = [p[0] for p in personnel]
        stats = self.get_personnel_duty_stats(personnel_ids)
        
        total_duties_count = sum(s['count'] for s in stats.values())
        total_duties_value = sum(s['total_value'] for s in stats.values())
        avg_count_overall = total_duties_count / len(personnel_ids) if personnel_ids else 0
        avg_value_overall = total_duties_value / len(personnel_ids) if personnel_ids else 0.0
        
        for person_id in personnel_ids:
            if stats[person_id]['count'] == 0 and stats[person_id]['total_value'] == 0:
                stats[person_id]['count'] = avg_count_overall
                stats[person_id]['total_value'] = avg_value_overall
        
        last_month_duty_person = self.get_last_month_last_duty(year, month)
        all_holidays_in_year = self.get_holidays_for_year(year)
        
        exemption_dict = defaultdict(dict)
        for e in exemptions:
            exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]
        
        days_in_month = calendar.monthrange(year, month)[1]
        
        all_days = []
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            
            day_value_id = self.get_weekday_id(weekday)
            holiday_dict = {date.fromisoformat(h[2]): h[0] for h in holidays}
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            
            if day_value_id in day_values:
                day_info = day_values[day_value_id]
            else:
                weekday_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
                weekday_values = [1.2, 1.1, 1.1, 0.9, 1.4, 2.0, 1.6]
                
                if 0 <= weekday < 7:
                    day_info = {'name': weekday_names[weekday], 'value': weekday_values[weekday]}
                else:
                    day_info = {'name': 'Bilinmeyen', 'value': 1.0}
            
            all_days.append((current_date, day_info, weekday))
        
        schedule = []
        assigned_dates = set()
        critical_day_assignees = set()
        
        # Perşembe-Cumartesi çiftlerini bul
        thursdays = [(d, info) for d, info, wd in all_days if wd == 3 and d not in assigned_dates]
        saturdays = [(d, info) for d, info, wd in all_days if wd == 5 and d not in assigned_dates]
        
        mandatory_pairs = []
        
        # Perşembe-Cumartesi eşleştirmeleri (farklı haftalarda)
        used_saturdays = set()
        for thursday_date, thursday_info in thursdays:
            for saturday_date, saturday_info in saturdays:
                if (saturday_date not in used_saturdays and 
                    self.get_week_start(thursday_date) != self.get_week_start(saturday_date)):
                    mandatory_pairs.append((thursday_date, thursday_info, saturday_date, saturday_info, 'Perşembe-Cumartesi'))
                    used_saturdays.add(saturday_date)
                    break
        
        # Cuma-Pazar eşleştirmeleri (farklı haftalarda)
        fridays = [(d, info) for d, info, wd in all_days if wd == 4 and d not in assigned_dates]
        sundays = [(d, info) for d, info, wd in all_days if wd == 6 and d not in assigned_dates]
        
        used_sundays = set()
        for friday_date, friday_info in fridays:
            for sunday_date, sunday_info in sundays:
                if (sunday_date not in used_sundays and 
                    self.get_week_start(friday_date) != self.get_week_start(sunday_date)):
                    mandatory_pairs.append((friday_date, friday_info, sunday_date, sunday_info, 'Cuma-Pazar'))
                    used_sundays.add(sunday_date)
                    break
        
        for day1_date, day1_info, day2_date, day2_info, pair_type in mandatory_pairs:
            eligible_for_pair = []
            
            for person_id in personnel_ids:
                if person_id in critical_day_assignees:
                    continue
                
                # Her iki gün için de uygunluk kontrolü
                can_assign_day1 = self.can_assign_day_enhanced(person_id, day1_date, schedule, exemption_dict, last_month_duty_person, all_holidays_in_year)
                can_assign_day2 = self.can_assign_day_enhanced(person_id, day2_date, schedule, exemption_dict, last_month_duty_person, all_holidays_in_year)
                
                if can_assign_day1 and can_assign_day2:
                    count_diff = avg_count_overall - stats[person_id]['count']
                    value_diff = avg_value_overall - stats[person_id]['total_value']
                    priority = count_diff * 10 + value_diff
                    
                    eligible_for_pair.append((person_id, priority))
            
            if eligible_for_pair:
                eligible_for_pair.sort(key=lambda x: x[1], reverse=True)
                selected_person = eligible_for_pair[0][0]
                
                schedule.append((day1_date, selected_person, day1_info['name']))
                schedule.append((day2_date, selected_person, day2_info['name']))
                
                assigned_dates.add(day1_date)
                assigned_dates.add(day2_date)
                critical_day_assignees.add(selected_person)
                
                # İstatistikleri güncelle
                stats[selected_person]['count'] += 2
                stats[selected_person]['total_value'] += day1_info['value'] + day2_info['value']
        
        for current_date, day_info, weekday in all_days:
            if current_date in assigned_dates:
                continue  # Zaten atanmış
            
            eligible_personnel = []
            
            for person_id in personnel_ids:
                # Kritik günlerde (Cuma, Cumartesi, Pazar) zaten kritik gün alanları geç
                if weekday in [4, 5, 6] and person_id in critical_day_assignees:
                    continue
                
                if self.can_assign_day_enhanced(person_id, current_date, schedule, exemption_dict, last_month_duty_person, all_holidays_in_year):
                    count_diff = avg_count_overall - stats[person_id]['count']
                    value_diff = avg_value_overall - stats[person_id]['total_value']
                    priority = count_diff * 10 + value_diff
                    
                    eligible_personnel.append((person_id, priority))
            
            if eligible_personnel:
                eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                selected_person_id = eligible_personnel[0][0]
                
                schedule.append((current_date, selected_person_id, day_info['name']))
                assigned_dates.add(current_date)  # KRITIK FIX: Tarihi atanmış olarak işaretle
                
                # Kritik günlerde atananları kaydet
                if weekday in [4, 5, 6]:
                    critical_day_assignees.add(selected_person_id)
                
                # İstatistikleri güncelle
                stats[selected_person_id]['count'] += 1
                stats[selected_person_id]['total_value'] += day_info['value']
            else:
                schedule.append((current_date, None, day_info['name']))
                assigned_dates.add(current_date)  # Boş günü de işaretle
        
        schedule.sort(key=lambda x: x[0])
        return schedule
    
    def get_holidays_for_year(self, year):
        """Yıl bazında tüm tatilleri getirir (Ramazan-Kurban çakışma kontrolü için)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tarih, gunDegerId, ad FROM Tatil
            WHERE strftime('%Y', tarih) = ?
        """, (str(year),))
        holidays = {date.fromisoformat(row[0]): (row[1], row[2]) for row in cursor.fetchall()}
        conn.close()
        return holidays
    
    def is_ramazan_kurban_conflict_enhanced(self, person_id, target_date, stats, all_holidays):
        """
        Gelişmiş tatil çakışma kontrolü - Kullanıcı örneğinden
        1. Ramazan-Kurban çapraz atama: Aynı yıl içinde Ramazan nöbeti olana Kurban verilemez (ve tersi)
        2. Genel tatil çakışma: Geçmiş tatil nöbeti olana yeni farklı tatil verilemez
        """
        target_holiday_info = all_holidays.get(target_date)
        
        if not target_holiday_info:
            return False
        
        target_holiday_name = target_holiday_info[1]
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.ad FROM Nobet n
            JOIN Tatil t ON n.tarih = t.tarih
            WHERE n.personelId = ? AND strftime('%Y', n.tarih) = ?
        """, (person_id, str(target_date.year)))
        
        yearly_holidays = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tut FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                     (person_id, target_date))
        mazeret_result = cursor.fetchone()
        conn.close()
        
        if mazeret_result and mazeret_result[0] == 1:
            return False
        
        if 'Ramazan' in target_holiday_name and any('Kurban' in h for h in yearly_holidays):
            return True
            
        if 'Kurban' in target_holiday_name and any('Ramazan' in h for h in yearly_holidays):
            return True
        
        return False
    
    def has_consecutive_days_conflict_enhanced(self, person_id, target_date, current_schedule, stats):
        """
        Gelişmiş ardışık gün çakışma kontrolü - Kullanıcı örneğinden
        Geçmiş nöbet kayıtlarını ve mevcut program için planlanan nöbetleri kontrol eder
        """
        prev_day = target_date - timedelta(days=1)
        next_day = target_date + timedelta(days=1)
        
        # Mevcut programdaki çakışmaları kontrol et
        for scheduled_date, scheduled_person, _ in current_schedule:
            if scheduled_person == person_id and (scheduled_date == prev_day or scheduled_date == next_day):
                return True
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tarih FROM Nobet 
            WHERE personelId = ? AND (tarih = ? OR tarih = ?)
        """, (person_id, prev_day, next_day))
        
        if cursor.fetchone():
            conn.close()
            return True
        
        conn.close()
        return False
    
    def calculate_enhanced_priority_score(self, person_id, stats, target_count, target_value, target_date, schedule):
        """
        Gelişmiş öncelik puanı hesaplama - Kullanıcı örneğinden
        1. Eşit dağılım (sayı ve puan) - MUTLAK ÖNCELİK
        2. Eşleştirme bonusu
        3. Yeni personel bonusu
        """
        person_stats = stats[person_id]
        
        # Temel adalet puanları (eşit dağıtım ÖNCELİKLİ)
        count_diff = target_count - person_stats['count']
        value_diff = target_value - person_stats['total_value']
        
        priority_score = count_diff * 10 + value_diff * 1.5
        
        if person_stats['count'] == 0 and person_stats['total_value'] == 0:
            priority_score += 500
        
        pairing_bonus = self.calculate_enhanced_pairing_bonus(person_id, target_date, schedule)
        priority_score += pairing_bonus
        
        return priority_score
    
    def can_assign_day_enhanced(self, person_id, target_date, schedule, exemption_dict, last_month_duty_person, all_holidays_in_year):
        """
        Gelişmiş gün atama uygunluk kontrolü - tüm kısıtlamaları kontrol eder
        """
        is_forced_assignment = (person_id in exemption_dict and 
                              target_date in exemption_dict[person_id] and 
                              exemption_dict[person_id][target_date] == 1)
        is_exempt = (person_id in exemption_dict and 
                   target_date in exemption_dict[person_id] and 
                   exemption_dict[person_id][target_date] == 0)
        
        if is_exempt and not is_forced_assignment:
            return False
        
        # Zorunlu atama hariç tüm kısıtlamaları kontrol et
        if not is_forced_assignment:
            # Önceki ayın son günü nöbetçi kontrolü
            if target_date.day == 1 and person_id == last_month_duty_person:
                return False
            
            if self.is_ramazan_kurban_conflict_enhanced(person_id, target_date, {}, all_holidays_in_year):
                return False
            
            # Ardışık gün kontrolü
            if self.has_consecutive_days_conflict_enhanced(person_id, target_date, schedule, {}):
                return False
        
        return True
    
    def calculate_enhanced_pairing_bonus(self, person_id, target_date, schedule):
        """
        Gelişmiş zorunlu eşleştirme bonusu - Kullanıcı örneğinden
        Perşembe-Cumartesi ve Cuma-Pazar eşleştirmelerini güçlü şekilde teşvik eder
        """
        target_weekday = target_date.weekday()
        bonus = 0
        
        person_duties_this_month = [
            (d, p) for d, p, _ in schedule if p == person_id and d.month == target_date.month
        ]
        
        # Perşembe-Cumartesi eşleştirmesi
        has_thursday_this_month = any(d.weekday() == 3 for d, _ in person_duties_this_month)
        has_saturday_this_month = any(d.weekday() == 5 for d, _ in person_duties_this_month)

        if target_weekday == 3 and not has_saturday_this_month:  # Perşembe atanıyor ve Cumartesi yoksa
            bonus += 200  # Cumartesi eşleşmesi için güçlü teşvik
        elif target_weekday == 5 and not has_thursday_this_month:  # Cumartesi atanıyor ve Perşembe yoksa
            bonus += 200  # Perşembe eşleşmesi için güçlü teşvik
        
        # Cuma-Pazar eşleştirmesi
        has_friday_this_month = any(d.weekday() == 4 for d, _ in person_duties_this_month)
        has_sunday_this_month = any(d.weekday() == 6 for d, _ in person_duties_this_month)

        if target_weekday == 4 and not has_sunday_this_month:  # Cuma atanıyor ve Pazar yoksa
            bonus += 200  # Pazar eşleşmesi için güçlü teşvik
        elif target_weekday == 6 and not has_friday_this_month:  # Pazar atanıyor ve Cuma yoksa
            bonus += 200  # Cuma eşleşmesi için güçlü teşvik

        return bonus
    
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
    
    def get_current_schedule_monthly_stats(self, current_schedule, base_monthly_stats):
        """
        Mevcut programdaki atamalarla aylık istatistikleri güncelle
        """
        updated_stats = {}
        for person_id, day_counts in base_monthly_stats.items():
            updated_stats[person_id] = day_counts.copy()
        
        for scheduled_date, person_id, day_type in current_schedule:
            if person_id:
                if person_id not in updated_stats:
                    updated_stats[person_id] = {}
                if day_type not in updated_stats[person_id]:
                    updated_stats[person_id][day_type] = 0
                updated_stats[person_id][day_type] += 1
        
        return updated_stats
    
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
                    bonus += 3000
                    break
        
        elif weekday == 3:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 5 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 3000
                    break
        
        elif weekday == 6:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 4 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 3000
                    break
        
        elif weekday == 4:
            for scheduled_date, scheduled_person, _ in existing_schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.weekday() == 6 and
                    scheduled_date.month == target_date.month and
                    self.get_week_start(scheduled_date) != target_week):
                    bonus += 3000
                    break
        
        return bonus
    
    def has_same_day_distribution_conflict(self, person_id, target_date, day_type, monthly_stats):
        """
        Aynı gün türü dağıtım çakışması kontrolü - ULTRA SIKI
        Kritik günlerde (Cuma, Cumartesi, Pazar) aynı kişiye tekrar atama KESINLIKLE engelleme
        """
        if person_id not in monthly_stats:
            return False
        
        person_monthly = monthly_stats[person_id]
        
        critical_days = ['Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        if day_type in critical_days:
            total_critical_days = 0
            for critical_day in critical_days:
                if critical_day in person_monthly:
                    total_critical_days += person_monthly[critical_day]
            
            if total_critical_days > 0:
                return True
        
        # Normal gün türü kontrolü
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
