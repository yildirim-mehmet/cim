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
        Zorunlu eşleştirme bonusu hesaplama - STANDART
        İki aşamalı algoritma kullanıldığı için bonus sistemi basitleştirildi
        Args: person_id, target_date, existing_schedule, year, month
        Returns: int - Bonus puan değeri
        """
        return 0
    
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
    
    def get_monthly_duty_stats(self, personnel_ids, year, month):
        """
        Aylık nöbet istatistiklerini getirir
        Args: personnel_ids, year, month
        Returns: {person_id: {day_type: count, ...}, ...}
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        monthly_stats = {}
        for person_id in personnel_ids:
            monthly_stats[person_id] = {}
        
        cursor.execute("""
            SELECT personelId, ad, COUNT(*) as count
            FROM Nobet 
            WHERE strftime('%Y-%m', tarih) = ?
            GROUP BY personelId, ad
        """, (f"{year:04d}-{month:02d}",))
        
        results = cursor.fetchall()
        for person_id, day_type, count in results:
            if person_id in monthly_stats:
                monthly_stats[person_id][day_type] = count
        
        conn.close()
        return monthly_stats
    
    def get_current_schedule_monthly_stats(self, schedule, initial_stats):
        """
        Mevcut program için aylık istatistikleri günceller
        Args: schedule - [(date, person_id, day_type), ...], initial_stats
        Returns: Updated monthly stats
        """
        updated_stats = {}
        for person_id, stats in initial_stats.items():
            updated_stats[person_id] = stats.copy()
        
        for scheduled_date, person_id, day_type in schedule:
            if person_id:
                if person_id not in updated_stats:
                    updated_stats[person_id] = {}
                if day_type not in updated_stats[person_id]:
                    updated_stats[person_id][day_type] = 0
                updated_stats[person_id][day_type] += 1
        
        return updated_stats
    
    def has_same_day_distribution_conflict(self, person_id, target_date, day_type, monthly_stats):
        """
        Kritik gün dağıtım çakışması kontrolü - DENGELI
        Kritik günlerde adil dağıtım sağlar
        Args: person_id, target_date, day_type, monthly_stats
        Returns: True - Çakışma var, False - Çakışma yok
        """
        if person_id not in monthly_stats:
            return False
        
        person_monthly = monthly_stats[person_id]
        
        critical_days = ['Cuma', 'Cumartesi', 'Pazar']
        if day_type in critical_days:
            critical_count = sum(person_monthly.get(cd, 0) for cd in critical_days)
            if critical_count >= 3:
                return True
        
        return False
    
    def needs_sunday_monday_pairing(self, person_id, target_date, existing_schedule, year, month):
        """
        Pazar-Pazartesi zorunlu eşleştirme kontrolü
        Pazar yazılana aynı ay farklı haftada Pazartesi yazılması zorunludur
        Pazartesi yazılana aynı ay farklı haftada Pazar yazılması zorunludur
        Args: person_id, target_date, existing_schedule, year, month
        Returns: True - Aynı hafta atama yasak, False - Atama yapılabilir
        """
        target_weekday = target_date.weekday()
        
        if target_weekday not in [0, 6]:
            return False
        
        has_sunday = False
        has_monday = False
        sunday_weeks = set()
        monday_weeks = set()
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month:
                scheduled_weekday = scheduled_date.weekday()
                week_start = scheduled_date - timedelta(days=scheduled_weekday)
                
                if scheduled_weekday == 6:
                    has_sunday = True
                    sunday_weeks.add(week_start)
                elif scheduled_weekday == 0:
                    has_monday = True
                    monday_weeks.add(week_start)
        
        target_week_start = target_date - timedelta(days=target_weekday)
        
        if target_weekday == 6 and has_monday:
            if target_week_start in monday_weeks:
                return True
        
        elif target_weekday == 0 and has_sunday:
            if target_week_start in sunday_weeks:
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
        1. Aşama: Zorunlu eşleştirmeleri öncelikle yerleştir
        2. Aşama: Kalan günleri adil dağıtımla doldur
        
        Args: year, month - Hedef yıl ve ay
        Returns: [(tarih, personel_id, gün_türü), ...] - Nöbet programı
        """
        personnel = self.get_active_personnel()
        day_values = self.get_day_values()
        holidays = self.get_holidays(year, month)
        exemptions = self.get_exemptions(year, month)
        
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
        
        critical_days = []
        regular_days = []
        
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(weekday)
            
            day_info = day_values[day_value_id]
            
            if weekday in [0, 3, 4, 5, 6]:
                critical_days.append((current_date, day_info, weekday))
            else:
                regular_days.append((current_date, day_info, weekday))
        
        schedule = []
        assigned_dates = set()
        
        thursdays = [(d, info, wd) for d, info, wd in critical_days if wd == 3]
        fridays = [(d, info, wd) for d, info, wd in critical_days if wd == 4]
        saturdays = [(d, info, wd) for d, info, wd in critical_days if wd == 5]
        sundays = [(d, info, wd) for d, info, wd in critical_days if wd == 6]
        mondays = [(d, info, wd) for d, info, wd in critical_days if wd == 0]
        
        mandatory_pairs = []
        
        all_possible_pairs = []
        
        for thursday_date, thursday_info, _ in thursdays:
            thursday_week = thursday_date.isocalendar()[1]
            for saturday_date, saturday_info, _ in saturdays:
                saturday_week = saturday_date.isocalendar()[1]
                if thursday_week != saturday_week:
                    all_possible_pairs.append(('thursday_saturday', thursday_date, saturday_date, thursday_info, saturday_info))
        
        for friday_date, friday_info, _ in fridays:
            friday_week = friday_date.isocalendar()[1]
            for sunday_date, sunday_info, _ in sundays:
                sunday_week = sunday_date.isocalendar()[1]
                if friday_week != sunday_week:
                    all_possible_pairs.append(('friday_sunday', friday_date, sunday_date, friday_info, sunday_info))
        
        for sunday_date, sunday_info, _ in sundays:
            sunday_week = sunday_date.isocalendar()[1]
            for monday_date, monday_info, _ in mondays:
                monday_week = monday_date.isocalendar()[1]
                if sunday_week != monday_week:
                    all_possible_pairs.append(('sunday_monday', sunday_date, monday_date, sunday_info, monday_info))
        
        all_possible_pairs.sort(key=lambda x: (x[1], x[2]))
        
        used_dates = set()
        
        for pair_type, date1, date2, info1, info2 in all_possible_pairs:
            if date1 not in used_dates and date2 not in used_dates:
                best_person = None
                best_priority = float('-inf')
                
                for person_id in personnel_ids:
                    if (self._can_assign_person(person_id, date1, schedule, exemption_dict, last_month_duty_person, year, month) and
                        self._can_assign_person(person_id, date2, schedule, exemption_dict, last_month_duty_person, year, month)):
                        priority = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                        if priority > best_priority:
                            best_priority = priority
                            best_person = person_id
                
                if best_person:
                    person_name = next(p[1] for p in personnel if p[0] == best_person)
                    schedule.append((date1, best_person, info1['name']))
                    schedule.append((date2, best_person, info2['name']))
                    used_dates.add(date1)
                    used_dates.add(date2)
                    assigned_dates.add(date1)
                    assigned_dates.add(date2)
                    
                    stats[best_person]['count'] += 2
                    stats[best_person]['total_value'] += info1['value'] + info2['value']
        
        remaining_days = []
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            if current_date not in assigned_dates:
                weekday = current_date.weekday()
                
                if current_date in holiday_dict:
                    day_value_id = holiday_dict[current_date]
                else:
                    day_value_id = self.get_weekday_id(weekday)
                
                day_info = day_values[day_value_id]
                remaining_days.append((current_date, day_info))
        
        for current_date, day_info in remaining_days:
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
                    priority_score += 1000
                
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
        
        schedule.sort(key=lambda x: x[0])
        return schedule
    
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
    
    def _can_assign_person(self, person_id, target_date, existing_schedule, exemption_dict, last_month_duty_person, year, month):
        """
        Kişinin belirli bir tarihe atanıp atanamayacağını kontrol eder
        Args: person_id, target_date, existing_schedule, exemption_dict, last_month_duty_person, year, month
        Returns: True - Atanabilir, False - Atanamaz
        """
        is_forced_assignment = (person_id in exemption_dict and 
                              target_date in exemption_dict[person_id] and 
                              exemption_dict[person_id][target_date] == 1)
        
        if target_date.day == 1 and person_id == last_month_duty_person:
            if not is_forced_assignment:
                return False
        
        if person_id in exemption_dict and target_date in exemption_dict[person_id]:
            tut_value = exemption_dict[person_id][target_date]
            if tut_value == 0:
                return False
        
        if not is_forced_assignment:
            if self.is_ramazan_kurban_conflict(person_id, target_date, existing_schedule):
                return False
            
            if self.has_consecutive_days_conflict(person_id, target_date, existing_schedule):
                return False
        
        return True
    
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
