import sqlite3
import calendar
from datetime import datetime, date, timedelta
from collections import defaultdict
import random
from typing import List, Tuple, Dict, Set

class DutyScheduler:
    def __init__(self, database):
        self.db = database
        self.critical_days = {4, 5, 6}  # Cuma, Cumartesi, Pazar
        self.pairing_rules = {
            3: 5,   # Perşembe -> Cumartesi
            5: 3,   # Cumartesi -> Perşembe
            6: 0,   # Pazar -> Pazartesi
            0: 6    # Pazartesi -> Pazar
        }
        self.day_avoidance_rates = {
            3: 0.8,   # Perşembe %80
            4: 0.8,   # Cuma %80
            5: 0.94,  # Cumartesi %94
            6: 0.9    # Pazar %90
        }
        
    def get_active_personnel(self) -> List[Tuple[int, str, str]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, statu FROM Personel WHERE Aktif = 1 ORDER BY id")
        personnel = cursor.fetchall()
        conn.close()
        return personnel
    
    def get_day_values(self) -> Dict[int, Dict[str, float]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, deger FROM GunDeger")
        day_values = {row[0]: {'name': row[1], 'value': row[2]} for row in cursor.fetchall()}
        conn.close()
        return day_values
    
    def get_holidays(self, year: int, month: int) -> List[Tuple[int, str, str]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gunDegerId, ad, tarih FROM Tatil 
            WHERE strftime('%Y-%m', tarih) = ?
        """, (f"{year:04d}-{month:02d}",))
        holidays = cursor.fetchall()
        conn.close()
        return holidays
    
    def get_exemptions(self, year: int, month: int) -> List[Tuple[int, str, bool]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT personelId, tarih, tut FROM Mazeret 
            WHERE strftime('%Y-%m', tarih) = ?
        """, (f"{year:04d}-{month:02d}",))
        exemptions = cursor.fetchall()
        conn.close()
        return exemptions
    
    def get_personnel_duty_stats(self, personnel_ids: List[int]) -> Dict[int, Dict[str, float]]:
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
    
    def get_last_month_last_duty(self, year: int, month: int) -> int:
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
    
    def get_weekday_id(self, weekday: int) -> int:
        return weekday + 1 if weekday != 6 else 7
    
    def is_ramazan_kurban_conflict(self, person_id: int, target_date: date) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT ad FROM Tatil WHERE tarih = ?", (target_date,))
        target_holiday = cursor.fetchone()
        
        if not target_holiday:
            conn.close()
            return False
        
        target_holiday_name = target_holiday[0]
        target_year = target_date.year
        
        cursor.execute("""
            SELECT t.ad FROM Nobet n
            JOIN Tatil t ON n.tarih = t.tarih
            WHERE n.personelId = ? AND strftime('%Y', n.tarih) = ?
        """, (person_id, str(target_year)))
        
        yearly_holidays = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT tut FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                     (person_id, target_date))
        mazeret_result = cursor.fetchone()
        if mazeret_result and mazeret_result[0] == 1:
            conn.close()
            return False
        
        if 'Ramazan' in target_holiday_name and any('Kurban' in h for h in yearly_holidays):
            conn.close()
            return True
            
        if 'Kurban' in target_holiday_name and any('Ramazan' in h for h in yearly_holidays):
            conn.close()
            return True
        
        conn.close()
        return False
    
    def check_pairing_requirements(self, person_id: int, target_date: date, 
                                 schedule: List[Tuple[date, int, str]], year: int, month: int) -> bool:
        target_weekday = target_date.weekday()
        
        if target_weekday not in self.pairing_rules:
            return False
        
        paired_day = self.pairing_rules[target_weekday]
        
        for scheduled_date, scheduled_person, _ in schedule:
            if (scheduled_person == person_id and scheduled_date.year == year and 
                scheduled_date.month == month and scheduled_date.weekday() == paired_day):
                return False
        
        return True
    
    def has_critical_day_conflict(self, person_id: int, target_date: date, 
                                schedule: List[Tuple[date, int, str]]) -> bool:
        target_weekday = target_date.weekday()
        
        if target_weekday not in self.critical_days:
            return False
        
        for scheduled_date, scheduled_person, _ in schedule:
            if scheduled_person == person_id and scheduled_date.weekday() in self.critical_days:
                return True
        
        return False
    
    def has_consecutive_days(self, person_id: int, target_date: date, 
                           schedule: List[Tuple[date, int, str]]) -> bool:
        prev_day = target_date - timedelta(days=1)
        next_day = target_date + timedelta(days=1)
        
        for scheduled_date, scheduled_person, _ in schedule:
            if scheduled_person == person_id and (scheduled_date == prev_day or scheduled_date == next_day):
                return True
        
        return False
    
    def has_weekly_limit(self, person_id: int, target_date: date, 
                        schedule: List[Tuple[date, int, str]]) -> bool:
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        for scheduled_date, scheduled_person, _ in schedule:
            if scheduled_person == person_id and week_start <= scheduled_date <= week_end:
                return True
        
        return False
    
    def should_avoid_day_type(self, person_id: int, target_weekday: int, 
                            schedule: List[Tuple[date, int, str]], year: int, month: int) -> bool:
        if target_weekday not in self.day_avoidance_rates:
            return False
        
        for scheduled_date, scheduled_person, _ in schedule:
            if (scheduled_person == person_id and scheduled_date.year == year and 
                scheduled_date.month == month and scheduled_date.weekday() == target_weekday):
                return random.random() < self.day_avoidance_rates[target_weekday]
        
        return False
    
    def calculate_fairness_adjustment(self, person_id: int, stats: Dict[int, Dict[str, float]], 
                                    avg_count: float, avg_value: float) -> float:
        """Nöbet sayısı ve puan eşitliği için ayar faktörü hesaplar"""
        person_stats = stats[person_id]
        count_diff = avg_count - person_stats['count']
        value_diff = avg_value - person_stats['total_value']
        
        # Daha fazla nöbet/puan açığı olanlara öncelik ver
        return (count_diff * 2) + (value_diff * 1.5)
    
    def calculate_pairing_bonus(self, person_id: int, target_date: date, 
                              schedule: List[Tuple[date, int, str]], year: int, month: int) -> float:
        """Eşleştirme bonusu hesaplama"""
        bonus = 0
        target_weekday = target_date.weekday()
        
        if target_weekday in self.pairing_rules:
            paired_day = self.pairing_rules[target_weekday]
            has_pair = False
            
            for scheduled_date, scheduled_person, _ in schedule:
                if (scheduled_person == person_id and scheduled_date.year == year and 
                    scheduled_date.month == month and scheduled_date.weekday() == paired_day):
                    has_pair = True
                    break
            
            if not has_pair:
                bonus += 200  # Güçlü eşleştirme bonusu
        
        return bonus
    
    def calculate_priority_score(self, person_id: int, stats: Dict[int, Dict[str, float]], 
                               avg_count: float, avg_value: float, 
                               target_date: date, schedule: List[Tuple[date, int, str]], 
                               year: int, month: int) -> float:
        base_score = self.calculate_fairness_adjustment(person_id, stats, avg_count, avg_value)
        
        target_weekday = target_date.weekday()
        
        # Eşleştirme bonusu
        pairing_bonus = self.calculate_pairing_bonus(person_id, target_date, schedule, year, month)
        base_score += pairing_bonus
        
        # Gün tipinden kaçınma
        if self.should_avoid_day_type(person_id, target_weekday, schedule, year, month):
            base_score *= 0.3  # Büyük ceza
        
        # Kritik günlerde çeşitlilik
        if target_weekday in self.critical_days:
            if self.has_critical_day_conflict(person_id, target_date, schedule):
                base_score = 0  # Kesin engelleme
        
        return base_score
    
    def fill_empty_days(self, schedule: List[Tuple[date, int, str]], year: int, month: int,
                       personnel: List[Tuple[int, str, str]], day_values: Dict[int, Dict[str, float]],
                       stats: Dict[int, Dict[str, float]], avg_count: float, avg_value: float,
                       exemption_dict: Dict[int, Dict[date, bool]], last_month_duty_person: int) -> List[Tuple[date, int, str]]:
        """Boş kalan günleri doldur"""
        personnel_ids = [p[0] for p in personnel]
        critical_day_assignees = set()
        
        for i, (current_date, person_id, day_type) in enumerate(schedule):
            if person_id is None:
                weekday = current_date.weekday()
                
                if current_date in exemption_dict:
                    day_value_id = exemption_dict[current_date]
                else:
                    day_value_id = self.get_weekday_id(weekday)
                
                day_info = day_values[day_value_id]
                
                if weekday == 0:  # Pazartesi başında temizle
                    critical_day_assignees.clear()
                
                eligible_personnel = []
                for person_id in personnel_ids:
                    is_forced = (person_id in exemption_dict and 
                                current_date in exemption_dict[person_id] and 
                                exemption_dict[person_id][current_date] == 1)
                    is_exempt = (person_id in exemption_dict and 
                               current_date in exemption_dict[person_id] and 
                               exemption_dict[person_id][current_date] == 0)
                    
                    if is_exempt and not is_forced:
                        continue
                    
                    if current_date.day == 1 and person_id == last_month_duty_person and not is_forced:
                        continue
                    
                    if not is_forced:
                        if self.is_ramazan_kurban_conflict(person_id, current_date):
                            continue
                        if self.has_consecutive_days(person_id, current_date, schedule):
                            continue
                        if self.has_weekly_limit(person_id, current_date, schedule):
                            continue
                        if weekday in self.critical_days and person_id in critical_day_assignees:
                            continue
                        if self.check_pairing_requirements(person_id, current_date, schedule, year, month):
                            continue
                        if self.has_critical_day_conflict(person_id, current_date, schedule):
                            continue
                    
                    score = self.calculate_priority_score(person_id, stats, avg_count, avg_value, 
                                                         current_date, schedule, year, month)
                    if is_forced:
                        score += 1000
                    eligible_personnel.append((person_id, score))
                
                if eligible_personnel:
                    eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                    selected_person_id = eligible_personnel[0][0]
                    
                    if weekday in self.critical_days:
                        critical_day_assignees.add(selected_person_id)
                    
                    schedule[i] = (current_date, selected_person_id, day_info['name'])
                    stats[selected_person_id]['count'] += 1
                    stats[selected_person_id]['total_value'] += day_info['value']
        
        return schedule
    
    def generate_schedule(self, year: int, month: int) -> List[Tuple[date, int, str]]:
        personnel = self.get_active_personnel()
        day_values = self.get_day_values()
        holidays = self.get_holidays(year, month)
        exemptions = self.get_exemptions(year, month)
        
        personnel_ids = [p[0] for p in personnel]
        stats = self.get_personnel_duty_stats(personnel_ids)
        
        if personnel_ids:
            total_count = sum(s['count'] for s in stats.values())
            total_value = sum(s['total_value'] for s in stats.values())
            avg_count = total_count / len(personnel_ids)
            avg_value = total_value / len(personnel_ids)
            
            for person_id in personnel_ids:
                if person_id not in stats:
                    stats[person_id] = {'count': avg_count, 'total_value': avg_value}
        
        last_month_duty_person = self.get_last_month_last_duty(year, month)
        
        holiday_dict = {date.fromisoformat(h[2]): h[0] for h in holidays}
        exemption_dict = defaultdict(dict)
        for e in exemptions:
            exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]
        
        days_in_month = calendar.monthrange(year, month)[1]
        schedule = []
        
        # İlk geçiş: Tüm günleri boş olarak başlat
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(current_date.weekday())
            day_info = day_values[day_value_id]
            schedule.append((current_date, None, day_info['name']))
        
        # İkinci geçiş: Zorunlu atamaları yap
        for i, (current_date, person_id, day_type) in enumerate(schedule):
            for person_id in personnel_ids:
                if (person_id in exemption_dict and 
                    current_date in exemption_dict[person_id] and 
                    exemption_dict[person_id][current_date] == 1):
                    
                    if current_date in holiday_dict:
                        day_value_id = holiday_dict[current_date]
                    else:
                        day_value_id = self.get_weekday_id(current_date.weekday())
                    day_info = day_values[day_value_id]
                    
                    schedule[i] = (current_date, person_id, day_info['name'])
                    stats[person_id]['count'] += 1
                    stats[person_id]['total_value'] += day_info['value']
                    break
        
        # Üçüncü geçiş: Perşembeleri doldur
        for i, (current_date, person_id, day_type) in enumerate(schedule):
            if person_id is None and current_date.weekday() == 3:  # Perşembe
                eligible_personnel = []
                for person_id in personnel_ids:
                    if (person_id in exemption_dict and 
                        current_date in exemption_dict[person_id] and 
                        exemption_dict[person_id][current_date] == 0):
                        continue
                    
                    if self.is_ramazan_kurban_conflict(person_id, current_date):
                        continue
                    if self.has_consecutive_days(person_id, current_date, schedule):
                        continue
                    if self.has_weekly_limit(person_id, current_date, schedule):
                        continue
                    if self.has_critical_day_conflict(person_id, current_date, schedule):
                        continue
                    
                    score = self.calculate_priority_score(person_id, stats, avg_count, avg_value, 
                                                         current_date, schedule, year, month)
                    eligible_personnel.append((person_id, score))
                
                if eligible_personnel:
                    eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                    selected_person_id = eligible_personnel[0][0]
                    
                    if current_date in holiday_dict:
                        day_value_id = holiday_dict[current_date]
                    else:
                        day_value_id = self.get_weekday_id(current_date.weekday())
                    day_info = day_values[day_value_id]
                    
                    schedule[i] = (current_date, selected_person_id, day_info['name'])
                    stats[selected_person_id]['count'] += 1
                    stats[selected_person_id]['total_value'] += day_info['value']
        
        # Dördüncü geçiş: Diğer günleri doldur
        schedule = self.fill_empty_days(schedule, year, month, personnel, day_values, 
                                       stats, avg_count, avg_value, exemption_dict, last_month_duty_person)
        
        # Beşinci geçiş: Hala boş gün varsa, kuralları esneterek doldur
        for i, (current_date, person_id, day_type) in enumerate(schedule):
            if person_id is None:
                weekday = current_date.weekday()
                
                if current_date in holiday_dict:
                    day_value_id = holiday_dict[current_date]
                else:
                    day_value_id = self.get_weekday_id(weekday)
                
                day_info = day_values[day_value_id]
                
                eligible_personnel = []
                for person_id in personnel_ids:
                    if (person_id in exemption_dict and 
                        current_date in exemption_dict[person_id] and 
                        exemption_dict[person_id][current_date] == 0):
                        continue
                    
                    # Kritik kuralları esnetme (sadece ardışık gün kontrolü)
                    if self.has_consecutive_days(person_id, current_date, schedule):
                        continue
                    
                    score = self.calculate_fairness_adjustment(person_id, stats, avg_count, avg_value)
                    eligible_personnel.append((person_id, score))
                
                if eligible_personnel:
                    eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                    selected_person_id = eligible_personnel[0][0]
                    
                    schedule[i] = (current_date, selected_person_id, day_info['name'])
                    stats[selected_person_id]['count'] += 1
                    stats[selected_person_id]['total_value'] += day_info['value']
        
        return schedule
    
    def save_schedule(self, schedule: List[Tuple[date, int, str]], year: int, month: int):
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
    
    def get_person_name(self, person_id: int) -> str:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ad FROM Personel WHERE id = ?", (person_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Bilinmeyen"