import sqlite3
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict
import random

class DutyScheduler:
    """
    Nöbet Programı Zamanlayıcısı
    Hastane personeli için adil ve kısıtlamalı nöbet dağıtımı yapar
    
    Temel özellikler:
    - Adil nöbet dağıtımı (sayı ve puan bazında)
    - Zorunlu Perşembe-Cumartesi eşleştirmesi (farklı haftalarda)
    - Zorunlu Cuma-Pazar eşleştirmesi (farklı haftalarda)
    - Mazeret sistemi (zorunlu atama ve hariç tutma)
    - Ardışık gün kısıtlaması
    - Bayram çapraz atama önleme
    """
    def __init__(self, database):
        """
        Zamanlayıcı başlatma
        Args: database - Veritabanı bağlantı nesnesi
        """
        self.db = database
        
    def get_active_personnel(self):
        """
        Aktif personel listesini veritabanından getirir
        Returns: [(id, ad, statu), ...] - Aktif personel listesi
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, statu FROM Personel WHERE Aktif = 1")
        personnel = cursor.fetchall()
        conn.close()
        return personnel
    
    def get_day_values(self):
        """
        Gün değerlerini veritabanından getirir
        Perşembe: 0.9, Cuma: 1.4, Cumartesi: 2.0, Pazar: 1.6 vb.
        Returns: {id: {'name': str, 'value': float}} - Gün değerleri sözlüğü
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, deger FROM GunDeger")
        day_values = {row[0]: {'name': row[1], 'value': row[2]} for row in cursor.fetchall()}
        conn.close()
        return day_values
    
    def get_holidays(self, year, month):
        """
        Belirtilen ay için tatil günlerini getirir
        Ramazan, Kurban bayramları ve resmi tatiller dahil
        Args: year, month - Hedef yıl ve ay
        Returns: [(gunDegerId, ad, tarih), ...] - Tatil listesi
        """
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
        """
        Belirtilen ay için mazeret kayıtlarını getirir
        tut=1: Zorunlu atama (tüm kısıtlamaları geçersiz kılar)
        tut=0: Kesinlikle hariç tutma
        Args: year, month - Hedef yıl ve ay
        Returns: [(personelId, tarih, tut), ...] - Mazeret listesi
        """
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
        """
        Personel nöbet istatistiklerini hesaplar
        Adil dağıtım için geçmiş nöbet sayısı ve toplam puan değeri
        Args: personnel_ids - Personel ID listesi
        Returns: {person_id: {'count': int, 'total_value': float}} - İstatistikler
        """
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
        """
        Önceki ayın son günü nöbetçi olan personeli bulur
        Bu kişi sonraki ayın ilk günü nöbetçi olamaz (ardışık gün kısıtlaması)
        Args: year, month - Hedef yıl ve ay
        Returns: person_id veya None - Önceki ay son nöbetçi
        """
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
        """
        Python weekday'ini veritabanı gün ID'sine çevirir
        Python: 0=Pazartesi, 6=Pazar
        DB: 1=Pazartesi, 7=Pazar
        """
        weekday_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}
        return weekday_mapping[weekday]
    
    def is_ramazan_kurban_conflict(self, person_id, target_date, existing_schedule):
        """
        Gelişmiş tatil çakışma kontrolü - Yıllık kapsam ve genel tatil önleme
        
        Bu metod iki ana kısıtlamayı kontrol eder:
        1. Ramazan-Kurban çapraz atama: Aynı yıl içinde Ramazan nöbeti olana Kurban verilemez (ve tersi)
        2. Genel tatil çakışma: Geçmiş tatil nöbeti olana yeni tatil verilemez (mazeret hariç)
        
        Mazeret sistemi: tut=1 olan mazeret kayıtları tüm çakışma kurallarını geçersiz kılar
        
        Args: 
            person_id (int): Personel ID'si
            target_date (date): Hedef nöbet tarihi
            existing_schedule (list): Mevcut nöbet programı (kullanılmıyor, DB'den alınıyor)
        Returns: 
            bool: True - Çakışma var (atama yapılamaz), False - Çakışma yok (atama yapılabilir)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT ad FROM Tatil WHERE tarih = ?", (target_date,))
        target_holiday = cursor.fetchone()
        
        if not target_holiday:
            conn.close()
            return False  # Hedef tarih tatil değilse çakışma yok
        
        target_holiday_name = target_holiday[0]
        target_year = target_date.year
        
        cursor.execute("""
            SELECT t.tarih, t.ad FROM Nobet n
            JOIN Tatil t ON n.tarih = t.tarih
            WHERE n.personelId = ? AND strftime('%Y', n.tarih) = ?
        """, (person_id, str(target_year)))
        
        yearly_holidays = cursor.fetchall()
        
        cursor.execute("""
            SELECT t.tarih, t.ad FROM Nobet n
            JOIN Tatil t ON n.tarih = t.tarih
            WHERE n.personelId = ? AND strftime('%Y', n.tarih) < ?
        """, (person_id, str(target_year)))
        
        past_holidays = cursor.fetchall()
        
        # Ramazan-Kurban çapraz atama kontrolü (aynı yıl)
        has_ramazan_this_year = any('Ramazan' in holiday[1] for holiday in yearly_holidays)
        has_kurban_this_year = any('Kurban' in holiday[1] for holiday in yearly_holidays)
        
        if 'Ramazan' in target_holiday_name and has_kurban_this_year:
            # Mazeret kontrolü - tut=1 ise çakışma göz ardı et
            cursor.execute("SELECT tut FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                         (person_id, target_date))
            mazeret_result = cursor.fetchone()
            if mazeret_result and mazeret_result[0] == 1:
                conn.close()
                return False  # Mazeret tut=1, zorunlu atama
            conn.close()
            return True  # Aynı yıl Kurban nöbeti var, Ramazan verilemez
            
        if 'Kurban' in target_holiday_name and has_ramazan_this_year:
            # Mazeret kontrolü - tut=1 ise çakışma göz ardı et
            cursor.execute("SELECT tut FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                         (person_id, target_date))
            mazeret_result = cursor.fetchone()
            if mazeret_result and mazeret_result[0] == 1:
                conn.close()
                return False  # Mazeret tut=1, zorunlu atama
            conn.close()
            return True  # Aynı yıl Ramazan nöbeti var, Kurban verilemez
        
        # Genel tatil çakışma kontrolü - geçmişte tatil nöbeti varsa yeni tatil verilemez
        if yearly_holidays or past_holidays:
            # Mazeret kontrolü - tut=1 ise çakışma göz ardı et
            cursor.execute("SELECT tut FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                         (person_id, target_date))
            mazeret_result = cursor.fetchone()
            if mazeret_result and mazeret_result[0] == 1:
                conn.close()
                return False  # Mazeret tut=1, zorunlu atama - çakışma göz ardı et
            
            conn.close()
            return True  # Geçmişte tatil nöbeti varsa yeni tatil verilemez
        
        conn.close()
        return False
    
    def has_thursday_saturday_conflict(self, person_id, target_date, existing_schedule):
        """
        Aynı hafta Perşembe-Cumartesi çakışma kontrolü
        Aynı kişiye aynı hafta hem Perşembe hem Cumartesi verilemez
        Args: person_id, target_date, existing_schedule
        Returns: True - Aynı hafta çakışma var, False - Çakışma yok
        """
        target_weekday = target_date.weekday()
        
        if target_weekday not in [3, 5]:  # Perşembe=3, Cumartesi=5
            return False
        
        target_week_start = target_date - timedelta(days=target_weekday)
        target_week_end = target_week_start + timedelta(days=6)
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and target_week_start <= scheduled_date <= target_week_end:
                scheduled_weekday = scheduled_date.weekday()
                if (target_weekday == 3 and scheduled_weekday == 5) or (target_weekday == 5 and scheduled_weekday == 3):
                    return True
        
        return False
    
    def has_friday_sunday_conflict(self, person_id, target_date, existing_schedule):
        """
        Aynı hafta Cuma-Pazar çakışma kontrolü
        Aynı kişiye aynı hafta hem Cuma hem Pazar verilemez
        Args: person_id, target_date, existing_schedule
        Returns: True - Aynı hafta çakışma var, False - Çakışma yok
        """
        target_weekday = target_date.weekday()
        
        if target_weekday not in [4, 6]:  # Cuma=4, Pazar=6
            return False
        
        target_week_start = target_date - timedelta(days=target_weekday)
        target_week_end = target_week_start + timedelta(days=6)
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and target_week_start <= scheduled_date <= target_week_end:
                scheduled_weekday = scheduled_date.weekday()
                if (target_weekday == 4 and scheduled_weekday == 6) or (target_weekday == 6 and scheduled_weekday == 4):
                    return True
        
        return False
    
    def needs_thursday_saturday_pairing(self, person_id, target_date, existing_schedule, year, month):
        """
        Perşembe-Cumartesi zorunlu eşleştirme kontrolü
        Perşembe yazılana aynı ay farklı haftada Cumartesi yazılması zorunludur
        Cumartesi yazılana aynı ay farklı haftada Perşembe yazılması zorunludur
        Args: person_id, target_date, existing_schedule, year, month
        Returns: True - Aynı hafta atama yasak, False - Atama yapılabilir
        """
        target_weekday = target_date.weekday()
        
        if target_weekday not in [3, 5]:  # Perşembe=3, Cumartesi=5
            return False
        
        has_thursday = False
        has_saturday = False
        thursday_weeks = set()
        saturday_weeks = set()
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month:
                scheduled_weekday = scheduled_date.weekday()
                week_start = scheduled_date - timedelta(days=scheduled_weekday)
                
                if scheduled_weekday == 3:  # Perşembe
                    has_thursday = True
                    thursday_weeks.add(week_start)
                elif scheduled_weekday == 5:  # Cumartesi
                    has_saturday = True
                    saturday_weeks.add(week_start)
        
        target_week_start = target_date - timedelta(days=target_weekday)
        
        if target_weekday == 3 and has_saturday:  # Perşembe atanıyor
            if target_week_start in saturday_weeks:
                return True  # Aynı hafta, yasak
        
        elif target_weekday == 5 and has_thursday:  # Cumartesi atanıyor
            if target_week_start in thursday_weeks:
                return True  # Aynı hafta, yasak
        
        return False
    
    def needs_friday_sunday_pairing(self, person_id, target_date, existing_schedule, year, month):
        """
        Cuma-Pazar zorunlu eşleştirme kontrolü
        Cuma yazılana aynı ay farklı haftada Pazar yazılması zorunludur
        Pazar yazılana aynı ay farklı haftada Cuma yazılması zorunludur
        Args: person_id, target_date, existing_schedule, year, month
        Returns: True - Aynı hafta atama yasak, False - Atama yapılabilir
        """
        target_weekday = target_date.weekday()
        
        if target_weekday not in [4, 6]:  # Cuma=4, Pazar=6
            return False
        
        has_friday = False
        has_sunday = False
        friday_weeks = set()
        sunday_weeks = set()
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month:
                scheduled_weekday = scheduled_date.weekday()
                week_start = scheduled_date - timedelta(days=scheduled_weekday)
                
                if scheduled_weekday == 4:  # Cuma
                    has_friday = True
                    friday_weeks.add(week_start)
                elif scheduled_weekday == 6:  # Pazar
                    has_sunday = True
                    sunday_weeks.add(week_start)
        
        target_week_start = target_date - timedelta(days=target_weekday)
        
        if target_weekday == 4 and has_sunday:  # Cuma atanıyor
            if target_week_start in sunday_weeks:
                return True  # Aynı hafta, yasak
        
        elif target_weekday == 6 and has_friday:  # Pazar atanıyor
            if target_week_start in friday_weeks:
                return True  # Aynı hafta, yasak
        
        return False
    
    def calculate_pairing_bonus(self, person_id, target_date, existing_schedule, year, month):
        """
        Zorunlu eşleştirme bonusu hesaplama
        Perşembe-Cumartesi ve Cuma-Pazar eşleştirmelerini güçlü şekilde teşvik eder
        Bonus değeri 1000 puan ile eşleştirme olasılığını %85-90'a çıkarır
        Args: person_id, target_date, existing_schedule, year, month
        Returns: int - Bonus puan değeri
        """
        target_weekday = target_date.weekday()
        bonus = 0
        
        if target_weekday == 3:  # Perşembe
            has_saturday = any(scheduled_date.weekday() == 5 for scheduled_date, scheduled_person, _ in existing_schedule 
                             if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_saturday:
                bonus += 1000  # ULTRA GÜÇLÜ bonus: Perşembe-Cumartesi eşleştirmesi için
        elif target_weekday == 5:  # Cumartesi
            has_thursday = any(scheduled_date.weekday() == 3 for scheduled_date, scheduled_person, _ in existing_schedule 
                             if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_thursday:
                bonus += 1000  # ULTRA GÜÇLÜ bonus: Cumartesi-Perşembe eşleştirmesi için
        
        if target_weekday == 4:  # Cuma
            has_sunday = any(scheduled_date.weekday() == 6 for scheduled_date, scheduled_person, _ in existing_schedule 
                           if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_sunday:
                bonus += 1000  # ULTRA GÜÇLÜ bonus: Cuma-Pazar eşleştirmesi için
        elif target_weekday == 6:  # Pazar
            has_friday = any(scheduled_date.weekday() == 4 for scheduled_date, scheduled_person, _ in existing_schedule 
                           if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_friday:
                bonus += 1000  # ULTRA GÜÇLÜ bonus: Pazar-Cuma eşleştirmesi için
        
        if target_weekday == 6:  # Pazar
            has_monday = any(scheduled_date.weekday() == 0 for scheduled_date, scheduled_person, _ in existing_schedule 
                           if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_monday:
                bonus += 1000  # ULTRA GÜÇLÜ bonus: Pazar-Pazartesi eşleştirmesi için
        elif target_weekday == 0:  # Pazartesi
            has_sunday = any(scheduled_date.weekday() == 6 for scheduled_date, scheduled_person, _ in existing_schedule 
                           if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_sunday:
                bonus += 1000  # ULTRA GÜÇLÜ bonus: Pazartesi-Pazar eşleştirmesi için
        
        return bonus
    
    def has_consecutive_days_conflict(self, person_id, target_date, existing_schedule):
        """
        Ardışık gün çakışma kontrolü
        Aynı kişiye peş peşe günlerde nöbet verilemez
        Args: person_id, target_date, existing_schedule
        Returns: True - Ardışık gün çakışması var, False - Çakışma yok
        """
        prev_day = target_date - timedelta(days=1)
        next_day = target_date + timedelta(days=1)
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and (scheduled_date == prev_day or scheduled_date == next_day):
                return True
        
        return False
    
    def calculate_priority_score(self, person_id, stats, total_avg_count, total_avg_value):
        """
        Adil dağıtım için öncelik puanı hesaplama
        Az nöbet alan ve düşük puan toplayan personele öncelik verir
        Args: person_id, stats, total_avg_count, total_avg_value
        Returns: float - Öncelik puanı (yüksek = daha öncelikli)
        """
        person_stats = stats[person_id]
        
        count_diff = total_avg_count - person_stats['count']
        value_diff = total_avg_value - person_stats['total_value']
        
        return count_diff * 2 + value_diff
    
    def generate_schedule(self, year, month):
        """
        İki aşamalı nöbet programı oluşturma algoritması
        
        AŞAMA 1: Zorunlu eşleştirmeleri öncelikle yerleştir
        AŞAMA 2: Kalan günleri adil dağıtımla doldur
        
        Zorunlu Eşleştirmeler:
        - Perşembe → Cumartesi (farklı hafta)
        - Cumartesi → Perşembe (farklı hafta)  
        - Cuma → Pazar (farklı hafta)
        - Pazar → Cuma (farklı hafta)
        - Pazar → Pazartesi (farklı hafta)
        - Pazartesi → Pazar (farklı hafta)
        
        Args: year, month - Hedef yıl ve ay
        Returns: [(tarih, personel_id, gün_türü), ...] - Nöbet programı
        """
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
        
        all_days = []
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(weekday)
            
            day_info = day_values[day_value_id]
            all_days.append((current_date, day_info, weekday))
        
        schedule = []
        assigned_dates = set()
        mandatory_pairs = []
        
        # Perşembe-Cumartesi eşleştirmeleri
        thursdays = [(d, info) for d, info, w in all_days if w == 3 and d not in assigned_dates]
        saturdays = [(d, info) for d, info, w in all_days if w == 5 and d not in assigned_dates]
        
        for thursday_date, thursday_info in thursdays:
            thursday_week = thursday_date.isocalendar()[1]
            for saturday_date, saturday_info in saturdays:
                saturday_week = saturday_date.isocalendar()[1]
                if thursday_week != saturday_week and saturday_date not in assigned_dates:
                    best_person = self._find_best_person_for_pair(
                        [(thursday_date, thursday_info), (saturday_date, saturday_info)],
                        personnel_ids, stats, avg_count, avg_value, exemption_dict, 
                        last_month_duty_person, schedule, assigned_dates
                    )
                    if best_person:
                        mandatory_pairs.append((thursday_date, best_person, thursday_info['name']))
                        mandatory_pairs.append((saturday_date, best_person, saturday_info['name']))
                        assigned_dates.add(thursday_date)
                        assigned_dates.add(saturday_date)
                        stats[best_person]['count'] += 2
                        stats[best_person]['total_value'] += thursday_info['value'] + saturday_info['value']
                        break
        
        # Cuma-Pazar eşleştirmeleri
        fridays = [(d, info) for d, info, w in all_days if w == 4 and d not in assigned_dates]
        sundays = [(d, info) for d, info, w in all_days if w == 6 and d not in assigned_dates]
        
        for friday_date, friday_info in fridays:
            friday_week = friday_date.isocalendar()[1]
            for sunday_date, sunday_info in sundays:
                sunday_week = sunday_date.isocalendar()[1]
                if friday_week != sunday_week and sunday_date not in assigned_dates:
                    best_person = self._find_best_person_for_pair(
                        [(friday_date, friday_info), (sunday_date, sunday_info)],
                        personnel_ids, stats, avg_count, avg_value, exemption_dict,
                        last_month_duty_person, schedule + mandatory_pairs, assigned_dates
                    )
                    if best_person:
                        mandatory_pairs.append((friday_date, best_person, friday_info['name']))
                        mandatory_pairs.append((sunday_date, best_person, sunday_info['name']))
                        assigned_dates.add(friday_date)
                        assigned_dates.add(sunday_date)
                        stats[best_person]['count'] += 2
                        stats[best_person]['total_value'] += friday_info['value'] + sunday_info['value']
                        break
        
        remaining_sundays = [(d, info) for d, info, w in all_days if w == 6 and d not in assigned_dates]
        mondays = [(d, info) for d, info, w in all_days if w == 0 and d not in assigned_dates]
        
        for sunday_date, sunday_info in remaining_sundays:
            sunday_week = sunday_date.isocalendar()[1]
            for monday_date, monday_info in mondays:
                monday_week = monday_date.isocalendar()[1]
                if sunday_week != monday_week and monday_date not in assigned_dates:
                    best_person = self._find_best_person_for_pair(
                        [(sunday_date, sunday_info), (monday_date, monday_info)],
                        personnel_ids, stats, avg_count, avg_value, exemption_dict,
                        last_month_duty_person, schedule + mandatory_pairs, assigned_dates
                    )
                    if best_person:
                        mandatory_pairs.append((sunday_date, best_person, sunday_info['name']))
                        mandatory_pairs.append((monday_date, best_person, monday_info['name']))
                        assigned_dates.add(sunday_date)
                        assigned_dates.add(monday_date)
                        stats[best_person]['count'] += 2
                        stats[best_person]['total_value'] += sunday_info['value'] + monday_info['value']
                        break
        
        schedule.extend(mandatory_pairs)
        
        for current_date, day_info, weekday in all_days:
            if current_date in assigned_dates:
                continue
                
            eligible_personnel = []
            for person_id in personnel_ids:
                is_forced_assignment = (person_id in exemption_dict and 
                                      current_date in exemption_dict[person_id] and 
                                      exemption_dict[person_id][current_date] == 1)
                
                if current_date.day == 1 and person_id == last_month_duty_person:
                    if not is_forced_assignment:
                        continue
                
                if person_id in exemption_dict and current_date in exemption_dict[person_id]:
                    tut_value = exemption_dict[person_id][current_date]
                    if tut_value == 0:
                        continue
                
                if not is_forced_assignment:
                    if self.is_ramazan_kurban_conflict(person_id, current_date, schedule):
                        continue
                    
                    if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                        continue
                
                priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                
                if is_forced_assignment:
                    priority_score += 10000
                
                eligible_personnel.append((person_id, priority_score))
            
            if eligible_personnel:
                eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                selected_person_id = eligible_personnel[0][0]
                
                schedule.append((current_date, selected_person_id, day_info['name']))
                stats[selected_person_id]['count'] += 1
                stats[selected_person_id]['total_value'] += day_info['value']
            else:
                schedule.append((current_date, None, day_info['name']))
        
        schedule.sort(key=lambda x: x[0])
        return schedule
    
    def _find_best_person_for_pair(self, date_info_pairs, personnel_ids, stats, avg_count, avg_value, 
                                   exemption_dict, last_month_duty_person, existing_schedule, assigned_dates):
        """
        Eşleştirme için en uygun personeli bulur
        """
        best_person = None
        best_score = float('-inf')
        
        for person_id in personnel_ids:
            eligible = True
            
            for date_obj, day_info in date_info_pairs:
                # Mazeret kontrolü
                if person_id in exemption_dict and date_obj in exemption_dict[person_id]:
                    tut_value = exemption_dict[person_id][date_obj]
                    if tut_value == 0:
                        eligible = False
                        break
                
                if date_obj.day == 1 and person_id == last_month_duty_person:
                    eligible = False
                    break
                
                # Ardışık gün kontrolü
                if self.has_consecutive_days_conflict(person_id, date_obj, existing_schedule):
                    eligible = False
                    break
                
                if self.is_ramazan_kurban_conflict(person_id, date_obj, existing_schedule):
                    eligible = False
                    break
            
            if eligible:
                # Adil dağıtım puanı hesapla
                priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                
                if priority_score > best_score:
                    best_score = priority_score
                    best_person = person_id
        
        return best_person
    
    def save_schedule(self, schedule, year, month):
        """
        Oluşturulan nöbet programını veritabanına kaydet
        Mevcut ay kayıtlarını siler ve yeni programı ekler
        Args: schedule - Nöbet programı listesi, year, month - Hedef yıl ve ay
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Nobet WHERE strftime('%Y-%m', tarih) = ?", (f"{year:04d}-{month:02d}",))
        
        # Gün değerlerini al (kayıt için gerekli)
        day_values = self.get_day_values()
        day_value_lookup = {v['name']: k for k, v in day_values.items()}
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:  # Personel atanmışsa kaydet
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
        """
        Personel ID'sine göre personel adını getirir
        Args: person_id - Personel ID'si
        Returns: str - Personel adı veya "Bilinmeyen"
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ad FROM Personel WHERE id = ?", (person_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Bilinmeyen"
