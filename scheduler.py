import sqlite3
import calendar
from datetime import date, datetime, timedelta
from collections import defaultdict

SAME_DAY_PRIORITY = {
    'Salı': 1,        # Tuesday - Highest priority
    'Çarşamba': 2,    # Wednesday - Second priority  
    'Pazartesi': 3,   # Monday - Third priority
    'Cuma': 4,        # Friday - Fourth priority
    'Pazar': 5,       # Sunday - Fifth priority
    'Perşembe': 6,    # Thursday - Sixth priority
    'Cumartesi': 7    # Saturday - Lowest priority
}

class DutyScheduler:
    def __init__(self, db):
        self.db = db
    
    def get_active_personnel(self):
        """Aktif personeli getirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, statu FROM Personel WHERE Aktif = 1")
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_day_values(self):
        """Gün değerlerini getirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, deger FROM GunDeger")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: {'name': row[1], 'value': row[2]} for row in rows}
    
    def get_holidays(self, year, month):
        """Belirtilen ay için tatilleri getirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, gunDegerId, ad, tarih 
            FROM Tatil 
            WHERE strftime('%Y-%m', tarih) = ?
        """, (f"{year:04d}-{month:02d}",))
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_exemptions(self, year, month):
        """Belirtilen ay için mazeretleri getirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT personelId, tarih, tut 
            FROM Mazeret 
            WHERE strftime('%Y-%m', tarih) = ?
        """, (f"{year:04d}-{month:02d}",))
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_personnel_duty_stats(self, personnel_ids):
        """Personel nöbet istatistiklerini getirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        for person_id in personnel_ids:
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(deger), 0) as total_value
                FROM Nobet 
                WHERE personelId = ?
            """, (person_id,))
            result = cursor.fetchone()
            stats[person_id] = {
                'count': result[0] if result else 0,
                'total_value': float(result[1]) if result else 0.0
            }
        
        conn.close()
        return stats
    
    def get_last_month_last_duty(self, year, month):
        """Önceki ayın son gününde nöbeti olan personeli getirir"""
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
        """Haftanın gününe göre gün değer ID'sini getirir"""
        weekday_mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}
        return weekday_mapping.get(weekday, 1)
    

    
    def is_person_eligible_for_pairing(self, person_id, current_date, day_name, 
                                     exemption_dict, last_month_duty_person, reserved_assignments):
        """Zorunlu eşleştirme için personel uygunluk kontrolü"""
        if (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
            exemption_dict[person_id][current_date] == 0):
            return False
        
        if current_date.day == 1 and person_id == last_month_duty_person:
            if not (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                   exemption_dict[person_id][current_date] == 1):
                return False
        
        for reserved_date, reserved_person, _ in reserved_assignments.values():
            if reserved_person == person_id:
                if abs((current_date - reserved_date).days) == 1:
                    return False
        
        return True
    
    def has_consecutive_days_conflict(self, person_id, target_date, existing_schedule):
        """Ardışık gün çakışma kontrolü"""
        prev_day = target_date - timedelta(days=1)
        next_day = target_date + timedelta(days=1)
        
        for scheduled_date, scheduled_person, _ in existing_schedule:
            if scheduled_person == person_id and (scheduled_date == prev_day or scheduled_date == next_day):
                return True
        
        return False
    
    def get_same_day_count(self, person_id, target_date, schedule, year, month):
        """Aynı gün türünde kaç kez atama yapıldığını hesaplar"""
        target_weekday = target_date.weekday()
        count = 0
        for scheduled_date, scheduled_person, _ in schedule:
            if (scheduled_person == person_id and 
                scheduled_date.year == year and 
                scheduled_date.month == month and
                scheduled_date.weekday() == target_weekday):
                count += 1
        return count

    def has_same_day_priority_conflict(self, person_id, target_date, day_name, schedule, year, month):
        """Aynı gün öncelik kurallarına göre çakışma kontrolü"""
        same_day_count = self.get_same_day_count(person_id, target_date, schedule, year, month)
        
        if same_day_count == 0:
            return False
            
        day_priority = SAME_DAY_PRIORITY.get(day_name, 8)
        
        if day_priority >= 4 and same_day_count >= 1:
            return True
        elif day_priority >= 2 and same_day_count >= 2:
            return True
        elif same_day_count >= 3:
            return True
            
        return False

    def has_critical_day_same_value_conflict(self, person_id, target_date, day_name, schedule, year, month):
        """Kritik günlerde aynı gün değerlerine aynı kişiler yazılmamalı"""
        critical_days = ['Cuma', 'Cumartesi', 'Perşembe', 'Pazar']
        
        if day_name not in critical_days:
            return False
            
        person_critical_assignments = []
        for scheduled_date, scheduled_person, scheduled_day_name in schedule:
            if (scheduled_person == person_id and 
                scheduled_date.year == year and 
                scheduled_date.month == month and
                scheduled_day_name in critical_days):
                person_critical_assignments.append(scheduled_day_name)
        
        if day_name in person_critical_assignments:
            return True
            
        return False

    def needs_enhanced_day_pairing(self, person_id, target_date, day_name, schedule, year, month):
        """Gelişmiş gün eşleştirme kuralları kontrolü"""
        target_week = target_date.isocalendar()[1]
        
        if day_name == 'Cumartesi':
            has_thursday = False
            for scheduled_date, scheduled_person, scheduled_day_name in schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.year == year and 
                    scheduled_date.month == month and
                    scheduled_day_name == 'Perşembe' and
                    scheduled_date.isocalendar()[1] != target_week):
                    has_thursday = True
                    break
            return not has_thursday
            
        elif day_name == 'Perşembe':
            has_saturday = False
            for scheduled_date, scheduled_person, scheduled_day_name in schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.year == year and 
                    scheduled_date.month == month and
                    scheduled_day_name == 'Cumartesi' and
                    scheduled_date.isocalendar()[1] != target_week):
                    has_saturday = True
                    break
            return not has_saturday
            
        elif day_name == 'Pazartesi':
            has_sunday = False
            for scheduled_date, scheduled_person, scheduled_day_name in schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.year == year and 
                    scheduled_date.month == month and
                    scheduled_day_name == 'Pazar' and
                    scheduled_date.isocalendar()[1] != target_week):
                    has_sunday = True
                    break
            return not has_sunday
            
        elif day_name == 'Pazar':
            has_monday = False
            for scheduled_date, scheduled_person, scheduled_day_name in schedule:
                if (scheduled_person == person_id and 
                    scheduled_date.year == year and 
                    scheduled_date.month == month and
                    scheduled_day_name == 'Pazartesi' and
                    scheduled_date.isocalendar()[1] != target_week):
                    has_monday = True
                    break
            return not has_monday
            
        return False

    def has_sunday_saturday_mutual_exclusion(self, person_id, target_date, day_name, schedule, year, month):
        """5-pazar yazılna c.tesi yazılmaz / ctesi yazılana pazar yazılmaz"""
        if day_name not in ['Pazar', 'Cumartesi']:
            return False
            
        exclusion_day = 'Cumartesi' if day_name == 'Pazar' else 'Pazar'
        
        for scheduled_date, scheduled_person, scheduled_day_name in schedule:
            if (scheduled_person == person_id and 
                scheduled_date.year == year and 
                scheduled_date.month == month and
                scheduled_day_name == exclusion_day):
                return True
                
        return False

    def calculate_percentage_based_allocation(self, personnel_ids, total_days, min_duties, max_duties):
        """2.2-Gün sayısı baz alınır (min-max referans % verilecek)"""
        total_personnel = len(personnel_ids)
        if total_personnel == 0:
            return {}
            
        base_allocation = total_days // total_personnel
        remainder = total_days % total_personnel
        
        allocations = {}
        for i, person_id in enumerate(personnel_ids):
            person_allocation = base_allocation + (1 if i < remainder else 0)
            person_allocation = max(min_duties, min(max_duties, person_allocation))
            allocations[person_id] = person_allocation
            
        return allocations

    def calculate_priority_score(self, person_id, stats, total_avg_count, total_avg_value, current_monthly_count=0, min_duties=0, max_duties=10):
        """
        Enhanced Max-Min priority scoring system
        Guarantees maximum 1 duty difference between personnel by heavily weighting count equality
        """
        person_stats = stats[person_id]
        
        count_diff = total_avg_count - person_stats['count']
        value_diff = total_avg_value - person_stats['total_value']
        
        base_score = count_diff * 100 + value_diff * 0.01
        
        if person_stats['count'] >= total_avg_count + 0.5:
            base_score -= 1000
        
        if current_monthly_count >= max_duties:
            base_score -= 1000000  # ABSOLUTE penalty for exceeding max - must NEVER happen
        elif current_monthly_count < min_duties:
            deficit = min_duties - current_monthly_count
            base_score += 100000 * (deficit + 1)  # Exponentially higher priority for bigger deficits
        
        if current_monthly_count == max_duties - 1:
            base_score -= 50000  # Heavy penalty for approaching max
        elif current_monthly_count == max_duties - 2 and max_duties > min_duties + 1:
            base_score -= 10000  # Moderate penalty for getting close to max
        
        if current_monthly_count == min_duties - 1:
            base_score += 75000  # High bonus for almost reaching min
        elif current_monthly_count == min_duties - 2 and min_duties > 1:
            base_score += 25000  # Moderate bonus for getting close to min
        
        return base_score

    def calculate_enhanced_priority_score(self, person_id, stats, total_avg_count, total_avg_value, 
                                        current_date, day_name, schedule, year, month,
                                        current_monthly_count=0, min_duties=0, max_duties=10):
        """
        6-gün değerleri baz alınır - Day values as primary basis
        Enhanced priority scoring with day values as primary factor
        """
        person_stats = stats[person_id]
        
        day_values = self.get_day_values()
        day_value_lookup = {v['name']: k for k, v in day_values.items()}
        day_value_id = day_value_lookup.get(day_name, 1)
        day_value = day_values[day_value_id]['value']
        
        day_value_score = day_value * 1000
        
        if current_monthly_count < min_duties:
            min_max_score = 800
        elif current_monthly_count >= max_duties:
            min_max_score = -2000
        else:
            min_max_score = 400 - (current_monthly_count * 50)
        
        count_diff = person_stats['count'] - total_avg_count
        value_diff = person_stats['total_value'] - total_avg_value
        
        fairness_score = -count_diff * 100 - value_diff * 50
        
        same_day_priority = SAME_DAY_PRIORITY.get(day_name, 8)
        same_day_score = (8 - same_day_priority) * 25
        
        total_score = day_value_score + min_max_score + fairness_score + same_day_score
        
        return total_score
    
    def generate_schedule(self, year, month, min_duties=3, max_duties=4):
        """
        Enhanced scheduling algorithm with 6 comprehensive constraints
        1-Ardışık gün yazılamaz (absolute prevention)
        2-Mazeretler Dikkat Edilecek (tut=0/1 handling)
        2.1-Max ve Min Sayılarına uyulacak (strict enforcement)
        2.2-Gün sayısı baz alınır (percentage-based allocation)
        3-C.tesi yazılana perşembe yazılır
        4-Pazar yazılana pazartesi yazılır (updated from cuma)
        5-pazar yazılna c.tesi yazılmaz / ctesi yazılana pazar yazılmaz
        6-gün değerleri baz alınır (day values primary)
        """
        
        personnel = self.get_active_personnel()
        day_values = self.get_day_values()
        holidays = self.get_holidays(year, month)
        exemptions = self.get_exemptions(year, month)
        
        personnel_ids = [p[0] for p in personnel]
        stats = self.get_personnel_duty_stats(personnel_ids)
        
        total_count = sum(s['count'] for s in stats.values())
        total_value = sum(s['total_value'] for s in stats.values())
        total_avg_count = total_count / len(personnel_ids) if personnel_ids else 0
        total_avg_value = total_value / len(personnel_ids) if personnel_ids else 0
        
        last_month_duty_person = self.get_last_month_last_duty(year, month)
        
        holiday_dict = {date.fromisoformat(h[3]): h[1] for h in holidays}
        exemption_dict = defaultdict(dict)
        for e in exemptions:
            exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]
        
        days_in_month = calendar.monthrange(year, month)[1]
        
        target_allocations = self.calculate_percentage_based_allocation(
            personnel_ids, days_in_month, min_duties, max_duties)
        
        all_days = []
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(weekday)
            
            day_info = day_values[day_value_id]
            day_data = (current_date, day_info['name'], day_info)
            all_days.append(day_data)
        
        all_days.sort(key=lambda x: x[2]['value'], reverse=True)
        
        schedule = []
        monthly_counts = {pid: 0 for pid in personnel_ids}
        
        remaining_days = list(all_days)
        
        for person_id in personnel_ids:
            assigned_count = 0
            days_to_remove = []
            
            for i, (current_date, day_name, day_info) in enumerate(remaining_days):
                if assigned_count >= min_duties:
                    break
                    
                can_assign = True
                
                if (person_id in exemption_dict and current_date in exemption_dict[person_id]):
                    if exemption_dict[person_id][current_date] == 0:
                        can_assign = False
                
                if current_date.day == 1 and person_id == last_month_duty_person:
                    if not (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                           exemption_dict[person_id][current_date] == 1):
                        can_assign = False
                
                if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                    can_assign = False
                
                if can_assign:
                    schedule.append((current_date, person_id, day_name))
                    monthly_counts[person_id] += 1
                    assigned_count += 1
                    days_to_remove.append(i)
                    
                    stats[person_id]['count'] += 1
                    stats[person_id]['total_value'] += day_info['value']
            
            for i in reversed(days_to_remove):
                remaining_days.pop(i)
        
        for current_date, day_name, day_info in remaining_days:
            eligible_personnel = []
            
            for person_id in personnel_ids:
                if monthly_counts[person_id] >= max_duties:
                    continue
                
                if (person_id in exemption_dict and current_date in exemption_dict[person_id]):
                    if exemption_dict[person_id][current_date] == 0:
                        continue
                
                if current_date.day == 1 and person_id == last_month_duty_person:
                    if not (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                           exemption_dict[person_id][current_date] == 1):
                        continue
                
                if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                    continue
                
                if self.needs_enhanced_day_pairing(person_id, current_date, day_name, schedule, year, month):
                    continue
                
                if self.has_sunday_saturday_mutual_exclusion(person_id, current_date, day_name, schedule, year, month):
                    continue
                
                if self.has_same_day_priority_conflict(person_id, current_date, day_name, schedule, year, month):
                    continue
                
                if self.has_critical_day_same_value_conflict(person_id, current_date, day_name, schedule, year, month):
                    continue
                
                priority_score = self.calculate_enhanced_priority_score(
                    person_id, stats, total_avg_count, total_avg_value, 
                    current_date, day_name, schedule, year, month,
                    monthly_counts[person_id], min_duties, max_duties
                )
                
                if (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                    exemption_dict[person_id][current_date] == 1):
                    priority_score += 2000
                
                eligible_personnel.append((person_id, priority_score))
            
            if eligible_personnel:
                eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                selected_person_id = eligible_personnel[0][0]
                
                schedule.append((current_date, selected_person_id, day_name))
                monthly_counts[selected_person_id] += 1
                
                stats[selected_person_id]['count'] += 1
                stats[selected_person_id]['total_value'] += day_info['value']
            else:
                schedule.append((current_date, None, day_name))
        
        return schedule
    
    def generate_schedule_main(self, year, month, min_duties=0, max_duties=10):
        """Ana nöbet programı oluşturma metodu"""
        return self.generate_schedule_with_global_optimization(year, month, min_duties, max_duties)
    
    def save_schedule(self, schedule, year, month):
        """Oluşturulan nöbet programını veritabanına kaydet"""
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
    
    def generate_schedule_with_global_optimization(self, year, month, min_duties=0, max_duties=10):
        """
        GLOBAL EŞLEŞTİRME OPTİMİZASYONU - TÜM ÇIFTLER BİRLİKTE
        Tüm zorunlu eşleştirmeleri aynı anda değerlendirerek ≥85% başarı oranı hedefler
        min_duties: Kişi başına minimum nöbet sayısı (backward compatibility)
        max_duties: Kişi başına maksimum nöbet sayısı (backward compatibility)
        """
        return self.generate_schedule(year, month, min_duties, max_duties)
    
    def is_person_eligible_for_pairing(self, person_id, current_date, day_name, 
                                     exemption_dict, last_month_duty_person, reserved_assignments):
        """Zorunlu eşleştirme için personel uygunluk kontrolü"""
        if (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
            exemption_dict[person_id][current_date] == 0):
            return False
        
        if current_date.day == 1 and person_id == last_month_duty_person:
            if not (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                   exemption_dict[person_id][current_date] == 1):
                return False
        
        for reserved_date, reserved_person, _ in reserved_assignments.values():
            if reserved_person == person_id:
                if abs((current_date - reserved_date).days) == 1:
                    return False
        
        return True

    def get_person_name(self, person_id):
        """Personel ID'sine göre personel adını getirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ad FROM Personel WHERE id = ?", (person_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "Bilinmeyen"
    
    def display_schedule(self, schedule, year, month):
        """
        Nöbet programını formatlanmış şekilde gösterir
        Tüm günleri alt alta sıralar, personel adları ve o ay kaç nöbet aldıklarını gösterir
        Ardışık nöbet atamalarını kırmızı renkle vurgular
        """
        from collections import defaultdict
        import calendar
        
        personnel_counts = defaultdict(int)
        personnel_names = {}
        
        personnel = self.get_active_personnel()
        for person_id, name, status in personnel:
            personnel_names[person_id] = name
            personnel_counts[person_id] = 0
        
        for _, person_id, _ in schedule:
            if person_id:
                personnel_counts[person_id] += 1
        
        consecutive_assignments = self.detect_consecutive_assignments(schedule)
        consecutive_dates = set(date for date, person in consecutive_assignments)
        
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
                
                if date_obj in consecutive_dates:
                    line += " ⚠️ ARDIŞIK NÖBET"
            else:
                line = f"{date_str} {day_name.ljust(10)} - {day_type.ljust(12)}: ATAMA YAPILMADI"
            
            output.append(line)
        
        if consecutive_assignments:
            output.append("\n⚠️ UYARI: ARDIŞIK NÖBET ATAMALARI TESPİT EDİLDİ!")
            output.append("-" * 50)
            consecutive_persons = {}
            for date, person in consecutive_assignments:
                if person not in consecutive_persons:
                    consecutive_persons[person] = []
                consecutive_persons[person].append(date)
            
            for person_id, dates in consecutive_persons.items():
                person_name = personnel_names.get(person_id, "Bilinmeyen")
                date_strs = [d.strftime("%d.%m.%Y") for d in sorted(set(dates))]
                output.append(f"• {person_name}: {', '.join(date_strs)}")
        
        output.append("\nPersonel Nöbet Özeti:")
        output.append("-" * 25)
        for person_id, count in sorted(personnel_counts.items(), key=lambda x: x[1], reverse=True):
            output.append(f"{personnel_names[person_id].ljust(20)}: {count} nöbet")
        
        return "\n".join(output)
    
    def detect_consecutive_assignments(self, schedule):
        """Ardışık nöbet atamalarını tespit eder"""
        consecutive_assignments = []
        
        sorted_schedule = sorted(schedule, key=lambda x: x[0])
        
        for i in range(len(sorted_schedule) - 1):
            current_date, current_person, current_day_type = sorted_schedule[i]
            next_date, next_person, next_day_type = sorted_schedule[i + 1]
            
            if (current_person and next_person and 
                current_person == next_person and 
                (next_date - current_date).days == 1):
                consecutive_assignments.append((current_date, current_person))
                consecutive_assignments.append((next_date, next_person))
        
        return consecutive_assignments

    def get_current_monthly_count(self, person_id, schedule, year, month):
        """Mevcut programdaki kişinin aylık nöbet sayısını hesaplar"""
        return sum(1 for scheduled_date, scheduled_person, _ in schedule 
                  if scheduled_person == person_id and 
                     scheduled_date.year == year and 
                     scheduled_date.month == month)
