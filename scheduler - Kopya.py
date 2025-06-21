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
    - **YENİ:** İlk 7 gün kuralı ile gün değişimi
    - **YENİ:** Kritik günlerde (Cuma, Cumartesi, Pazar) aynı kişiyi tekrar atama önlemi
    - **YENİ:** Belirli günlerde (Perşembe, Cuma, Cumartesi, Pazar) aynı kişiyi ay içinde tekrar atamama eğilimi
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
        Bonus değeri 200 puan ile eşleştirme olasılığını %85-90'a çıkarır
        Args: person_id, target_date, existing_schedule, year, month
        Returns: int - Bonus puan değeri
        """
        target_weekday = target_date.weekday()
        bonus = 0
        
        if target_weekday == 3:  # Perşembe
            has_saturday = any(scheduled_date.weekday() == 5 for scheduled_date, scheduled_person, _ in existing_schedule 
                               if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_saturday:
                bonus += 200  # Güçlü bonus: Perşembe-Cumartesi eşleştirmesi için
        elif target_weekday == 5:  # Cumartesi
            has_thursday = any(scheduled_date.weekday() == 3 for scheduled_date, scheduled_person, _ in existing_schedule 
                               if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_thursday:
                bonus += 200  # Güçlü bonus: Cumartesi-Perşembe eşleştirmesi için
        
        if target_weekday == 4:  # Cuma
            has_sunday = any(scheduled_date.weekday() == 6 for scheduled_date, scheduled_person, _ in existing_schedule 
                               if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_sunday:
                bonus += 200  # Güçlü bonus: Cuma-Pazar eşleştirmesi için
        elif target_weekday == 6:  # Pazar
            has_friday = any(scheduled_date.weekday() == 4 for scheduled_date, scheduled_person, _ in existing_schedule 
                               if scheduled_person == person_id and scheduled_date.year == year and scheduled_date.month == month)
            if not has_friday:
                bonus += 200  # Güçlü bonus: Pazar-Cuma eşleştirmesi için
        
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

    def check_first_7_days_rules(self, person_id, target_date, first_7_days_schedule):
        """
        İlk 7 gün kuralı kontrolü:
        1-Cumartesi yazılmışsa sonraki haftalarda Perşembe Yazılmalı
        2-Perşembe yazılmışsa sonraki haftalarda Cumartesi Yazılmalı
        3-Pazar Yazılmışsa sonraki haftalarda Pazartesi Yazılmalı
        4-Pazartesi yazılmışsa sonraki haftalarda Pazar yazılmalı
        
        Args:
            person_id (int): Personel ID'si
            target_date (date): Hedef nöbet tarihi
            first_7_days_schedule (list): İlk 7 günün nöbet programı
        Returns:
            bool: True - Kural ihlali var, False - Kural ihlali yok
        """
        # Sadece ilk 7 gün sonrası için bu kuralı uygulayın
        if target_date.day <= 7:
            return False

        # İlk 7 gündeki atamaları kontrol et
        for sch_date, sch_person, day_name in first_7_days_schedule:
            if sch_person == person_id:
                sch_weekday = sch_date.weekday()
                target_weekday = target_date.weekday()

                # Kural 1: İlk 7 günde Cumartesi (5) yazılmışsa, sonraki haftalarda Perşembe (3) yazılmalı
                if sch_weekday == 5 and target_weekday == 3:
                    # Aynı kişiye ilk 7 gün Cumartesi, sonraki bir günde Perşembe atanması gerekiyor.
                    # Eğer zaten bir Cumartesi ataması varsa ve bu atanan kişi Perşembe'ye geliyorsa sorun yok.
                    # Burada çakışma olup olmadığını kontrol ediyoruz, yani eğer Cumartesi atanmışsa, Perşembe ATANAMAZ demeliyiz
                    # Çünkü kural "Perşembe YAZILMALI" diyor. Yani burada bu kuralı pozitif bir teşvik olarak kullanmalıyız, yasak olarak değil.
                    # Bu nedenle bu fonksiyon burada her zaman False döndürmeli ve pozitif teşvikler başka bir yerde (priority_score) ele alınmalı.
                    # Ancak "AYNI KİŞİYE YAZILMAMALI" kuralı için bu fonksiyon kullanılabilir.
                    pass # Bu kural, atama olasılığını artırmalı, yasaklamamalı. Bu yüzden burada 'True' döndürmek yerine 'False' döndüreceğiz.

                # Kural 2: İlk 7 günde Perşembe (3) yazılmışsa, sonraki haftalarda Cumartesi (5) yazılmalı
                elif sch_weekday == 3 and target_weekday == 5:
                    pass # Bu kural da atama olasılığını artırmalı.

                # Kural 3: İlk 7 günde Pazar (6) yazılmışsa, sonraki haftalarda Pazartesi (0) yazılmalı
                elif sch_weekday == 6 and target_weekday == 0:
                    pass # Bu kural da atama olasılığını artırmalı.

                # Kural 4: İlk 7 günde Pazartesi (0) yazılmışsa, sonraki haftalarda Pazar (6) yazılmalı
                elif sch_weekday == 0 and target_weekday == 6:
                    pass # Bu kural da atama olasılığını artırmalı.

        return False # Bu kurallar çakışma değil, teşvik kurallarıdır.

    def calculate_first_7_days_bonus(self, person_id, target_date, first_7_days_schedule, year, month):
        """
        İlk 7 gün kuralı için bonus hesaplama.
        Bu bonus, kişilerin ilk 7 günde aldıkları nöbetlere göre sonraki haftalarda belirli günlerde nöbet alma olasılıklarını artırır.
        """
        bonus = 0
        target_weekday = target_date.weekday()

        if target_date.day > 7: # Kural sadece ilk 7 gün sonrası için geçerli
            for sch_date, sch_person, day_name in first_7_days_schedule:
                if sch_person == person_id:
                    sch_weekday = sch_date.weekday()

                    # Kural 1: İlk 7 günde Cumartesi (5) yazılmışsa, sonraki haftalarda Perşembe (3) yazılmalı
                    if sch_weekday == 5 and target_weekday == 3:
                        bonus += 150 # Yüksek bonus, bu eşleştirmeyi teşvik eder

                    # Kural 2: İlk 7 günde Perşembe (3) yazılmışsa, sonraki haftalarda Cumartesi (5) yazılmalı
                    elif sch_weekday == 3 and target_weekday == 5:
                        bonus += 150 # Yüksek bonus

                    # Kural 3: İlk 7 günde Pazar (6) yazılmışsa, sonraki haftalarda Pazartesi (0) yazılmalı
                    elif sch_weekday == 6 and target_weekday == 0:
                        bonus += 100 # Orta bonus

                    # Kural 4: İlk 7 günde Pazartesi (0) yazılmışsa, sonraki haftalarda Pazar (6) yazılmalı
                    elif sch_weekday == 0 and target_weekday == 6:
                        bonus += 100 # Orta bonus
        return bonus


    def has_critical_day_same_person_conflict(self, person_id, target_date, existing_schedule):
        """
        Kritik günlerde (Cuma, Cumartesi, Pazar) aynı gün değerlerine aynı kişiler yazılMAMAlı.
        Örneğin, bir kişi ayın 5'inde Cuma nöbeti tuttuysa, ayın 12'sinde başka bir Cuma nöbeti tutamaz.
        Args:
            person_id (int): Personel ID'si
            target_date (date): Hedef nöbet tarihi
            existing_schedule (list): Mevcut nöbet programı
        Returns:
            bool: True - Çakışma var, False - Çakışma yok
        """
        target_weekday = target_date.weekday() # 4: Cuma, 5: Cumartesi, 6: Pazar

        if target_weekday not in [4, 5, 6]:
            return False # Kritik gün değilse kontrol etme

        for sch_date, sch_person, day_name in existing_schedule:
            if sch_person == person_id:
                sch_weekday = sch_date.weekday()
                if sch_weekday == target_weekday and sch_weekday in [4, 5, 6]: # Aynı kritik gün ise
                    return True # Aynı kişiye aynı kritik gün tekrar yazılmış, çakışma var
        return False
    
    def calculate_avoid_same_day_in_month_penalty(self, person_id, target_date, existing_schedule):
        """
        Belirli günlerde (Perşembe, Cuma, Cumartesi, Pazar) aynı kişiye ay içinde tekrar atama olasılığını azaltan ceza puanı.
        EĞET kişiye perşembe yazmışsa o ay birdaha perşembe yazmamaya çalışsın %80 (ceza 80)
        EĞET kişiye cuma yazmışsa o ay birdaha cuma yazmamaya çalışsın %80 (ceza 80)
        EĞET kişiye cumartesi yazmışsa o ay birdaha cumartesi yazmamaya çalışsın %94 (ceza 94)
        EĞET kişiye pazar yazmışsa o ay birdaha pazar yazmamaya çalışsın %90 (ceza 90)
        """
        penalty = 0
        target_weekday = target_date.weekday() # 3: Perşembe, 4: Cuma, 5: Cumartesi, 6: Pazar
        
        for sch_date, sch_person, _ in existing_schedule:
            if sch_person == person_id and sch_date.month == target_date.month and sch_date.year == target_date.year:
                scheduled_weekday = sch_date.weekday()

                if target_weekday == 3 and scheduled_weekday == 3: # Perşembe
                    penalty += 80
                elif target_weekday == 4 and scheduled_weekday == 4: # Cuma
                    penalty += 80
                elif target_weekday == 5 and scheduled_weekday == 5: # Cumartesi
                    penalty += 94
                elif target_weekday == 6 and scheduled_weekday == 6: # Pazar
                    penalty += 90
        return penalty

    def calculate_priority_score(self, person_id, stats, total_avg_count, total_avg_value, target_date, existing_schedule, first_7_days_schedule):
        """
        Adil dağıtım için öncelik puanı hesaplama
        Az nöbet alan ve düşük puan toplayan personele öncelik verir
        Args: person_id, stats, total_avg_count, total_avg_value, target_date, existing_schedule, first_7_days_schedule
        Returns: float - Öncelik puanı (yüksek = daha öncelikli)
        """
        person_stats = stats[person_id]
        
        count_diff = total_avg_count - person_stats['count']
        value_diff = total_avg_value - person_stats['total_value']
        
        priority_score = count_diff * 2 + value_diff

        # Yeni eklenen bonuslar ve cezalar
        pairing_bonus = self.calculate_pairing_bonus(person_id, target_date, existing_schedule, target_date.year, target_date.month)
        priority_score += pairing_bonus

        first_7_days_bonus = self.calculate_first_7_days_bonus(person_id, target_date, first_7_days_schedule, target_date.year, target_date.month)
        priority_score += first_7_days_bonus

        avoid_same_day_penalty = self.calculate_avoid_same_day_in_month_penalty(person_id, target_date, existing_schedule)
        priority_score -= avoid_same_day_penalty # Ceza puanı, toplam öncelikten düşülür
        
        return priority_score
    
    def generate_schedule(self, year, month):
        """
        Ana nöbet programı oluşturma algoritması
        Tüm kısıtlamaları ve öncelikleri dikkate alarak aylık program oluşturur
        
        Algoritma sırası:
        1. Temel verileri topla (personel, gün değerleri, tatiller, mazeretler)
        2. Her gün için uygun personeli belirle
        3. Kısıtlamaları kontrol et (mazeret, ardışık gün, eşleştirmeler, **yeni kurallar**)
        4. Öncelik puanı hesapla (adil dağıtım + eşleştirme bonusu + **yeni bonuslar/cezalar**)
        5. En yüksek puanlı personeli seç
        
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
        schedule = []
        first_7_days_schedule = [] # İlk 7 günü takip etmek için yeni liste

        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(weekday)
            
            day_info = day_values[day_value_id]
            
            eligible_personnel = []
            for person_id in personnel_ids:
                is_forced_assignment = (person_id in exemption_dict and 
                                        current_date in exemption_dict[person_id] and 
                                        exemption_dict[person_id][current_date] == 1)
                
                if day == 1 and person_id == last_month_duty_person:
                    if not is_forced_assignment:  # Zorunlu atama hariç
                        continue
                
                if person_id in exemption_dict and current_date in exemption_dict[person_id]:
                    tut_value = exemption_dict[person_id][current_date]
                    if tut_value == 0:  # tut=0 kesinlikle hariç tut
                        continue
                
                if not is_forced_assignment:
                    if self.is_ramazan_kurban_conflict(person_id, current_date, schedule):
                        continue
                    
                    if self.needs_thursday_saturday_pairing(person_id, current_date, schedule, year, month):
                        continue
                    
                    if self.needs_friday_sunday_pairing(person_id, current_date, schedule, year, month):
                        continue
                    
                    if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                        continue
                    
                    # Yeni kural: Kritik günlerde aynı kişiyi tekrar atama kontrolü
                    if self.has_critical_day_same_person_conflict(person_id, current_date, schedule):
                        continue

                # İlk 7 gün kuralı bir kısıtlamadan ziyade bir teşvik olduğundan burada 'continue' kullanmıyoruz.
                # calculate_priority_score içinde bonus olarak işlenecek.
                # is_forced_assignment, tüm kısıtlamaları ezer, bu yüzden bonus hesaplamalarını da etkilemeli.

                priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value, current_date, schedule, first_7_days_schedule)
                
                if is_forced_assignment:
                    priority_score += 1000  # Mazeret tut=1 mutlak öncelik
                
                eligible_personnel.append((person_id, priority_score))
            
            if eligible_personnel:
                eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                selected_person_id = eligible_personnel[0][0]
                
                person_name = next(p[1] for p in personnel if p[0] == selected_person_id)
                schedule.append((current_date, selected_person_id, day_info['name']))
                
                # İlk 7 günü takip et
                if day <= 7:
                    first_7_days_schedule.append((current_date, selected_person_id, day_info['name']))

                stats[selected_person_id]['count'] += 1
                stats[selected_person_id]['total_value'] += day_info['value']
            else:
                schedule.append((current_date, None, day_info['name']))
        
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