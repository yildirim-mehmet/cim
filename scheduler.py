import sqlite3
import calendar
from datetime import date, datetime, timedelta
from collections import defaultdict

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
    
    def calculate_priority_score(self, person_id, stats, avg_count, avg_value):
        """Adil dağıtım için öncelik puanı hesaplama"""
        person_stats = stats[person_id]
        count_diff = avg_count - person_stats['count']
        value_diff = avg_value - person_stats['total_value']
        return count_diff * 2 + value_diff
    
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
    
    def generate_schedule_with_global_optimization(self, year, month):
        """
        GLOBAL EŞLEŞTİRME OPTİMİZASYONU - TÜM ÇIFTLER BİRLİKTE
        Tüm zorunlu eşleştirmeleri aynı anda değerlendirerek ≥85% başarı oranı hedefler
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
        
        holiday_dict = {date.fromisoformat(h[3]): h[1] for h in holidays}
        exemption_dict = defaultdict(dict)
        for e in exemptions:
            exemption_dict[e[0]][date.fromisoformat(e[1])] = e[2]
        
        days_in_month = calendar.monthrange(year, month)[1]
        
        weeks = {}
        all_days = []
        
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()
            week_number = current_date.isocalendar()[1]
            
            if current_date in holiday_dict:
                day_value_id = holiday_dict[current_date]
            else:
                day_value_id = self.get_weekday_id(weekday)
            
            day_info = day_values[day_value_id]
            day_data = (current_date, day_info['name'], week_number, day_info)
            
            all_days.append(day_data)
            
            if week_number not in weeks:
                weeks[week_number] = []
            weeks[week_number].append(day_data)
        
        thursdays = [(d, w) for d, w in [(day_data, day_data[2]) for day_data in all_days] if d[1] == 'Perşembe']
        fridays = [(d, w) for d, w in [(day_data, day_data[2]) for day_data in all_days] if d[1] == 'Cuma']
        saturdays = [(d, w) for d, w in [(day_data, day_data[2]) for day_data in all_days] if d[1] == 'Cumartesi']
        sundays = [(d, w) for d, w in [(day_data, day_data[2]) for day_data in all_days] if d[1] == 'Pazar']
        mondays = [(d, w) for d, w in [(day_data, day_data[2]) for day_data in all_days] if d[1] == 'Pazartesi']
        
        reserved_assignments = {}
        
        all_possible_pairs = []
        
        for thursday_data, thursday_week in thursdays:
            thursday_date, thursday_name, _, thursday_info = thursday_data
            
            for person_id in personnel_ids:
                if not self.is_person_eligible_for_pairing(
                    person_id, thursday_date, thursday_name, exemption_dict, 
                    last_month_duty_person, reserved_assignments
                ):
                    continue
                
                for saturday_data, saturday_week in saturdays:
                    if saturday_week != thursday_week:  # Farklı hafta
                        saturday_date, saturday_name, _, saturday_info = saturday_data
                        
                        if not self.is_person_eligible_for_pairing(
                            person_id, saturday_date, saturday_name, exemption_dict, 
                            last_month_duty_person, reserved_assignments
                        ):
                            continue
                        
                        priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                        all_possible_pairs.append({
                            'type': 'thursday_saturday',
                            'priority': priority_score + 2000,  # En yüksek öncelik
                            'person_id': person_id,
                            'first_date': thursday_date,
                            'first_name': thursday_name,
                            'first_week': thursday_week,
                            'second_date': saturday_date,
                            'second_name': saturday_name,
                            'second_week': saturday_week
                        })
                        break  # İlk uygun Cumartesi'yi al
        
        for friday_data, friday_week in fridays:
            friday_date, friday_name, _, friday_info = friday_data
            
            for person_id in personnel_ids:
                if not self.is_person_eligible_for_pairing(
                    person_id, friday_date, friday_name, exemption_dict, 
                    last_month_duty_person, reserved_assignments
                ):
                    continue
                
                for sunday_data, sunday_week in sundays:
                    if sunday_week != friday_week:  # Farklı hafta
                        sunday_date, sunday_name, _, sunday_info = sunday_data
                        
                        if not self.is_person_eligible_for_pairing(
                            person_id, sunday_date, sunday_name, exemption_dict, 
                            last_month_duty_person, reserved_assignments
                        ):
                            continue
                        
                        priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                        all_possible_pairs.append({
                            'type': 'friday_sunday',
                            'priority': priority_score + 1500,  # Yüksek öncelik
                            'person_id': person_id,
                            'first_date': friday_date,
                            'first_name': friday_name,
                            'first_week': friday_week,
                            'second_date': sunday_date,
                            'second_name': sunday_name,
                            'second_week': sunday_week
                        })
                        break  # İlk uygun Pazar'ı al
        
        for sunday_data, sunday_week in sundays:
            sunday_date, sunday_name, _, sunday_info = sunday_data
            
            for person_id in personnel_ids:
                if not self.is_person_eligible_for_pairing(
                    person_id, sunday_date, sunday_name, exemption_dict, 
                    last_month_duty_person, reserved_assignments
                ):
                    continue
                
                for monday_data, monday_week in mondays:
                    if monday_week != sunday_week:  # Farklı hafta
                        monday_date, monday_name, _, monday_info = monday_data
                        
                        if not self.is_person_eligible_for_pairing(
                            person_id, monday_date, monday_name, exemption_dict, 
                            last_month_duty_person, reserved_assignments
                        ):
                            continue
                        
                        priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                        all_possible_pairs.append({
                            'type': 'sunday_monday',
                            'priority': priority_score + 1000,  # Orta öncelik
                            'person_id': person_id,
                            'first_date': sunday_date,
                            'first_name': sunday_name,
                            'first_week': sunday_week,
                            'second_date': monday_date,
                            'second_name': monday_name,
                            'second_week': monday_week
                        })
                        break  # İlk uygun Pazartesi'yi al
        
        all_possible_pairs.sort(key=lambda x: x['priority'], reverse=True)
        
        used_dates = set()
        used_persons_for_pairs = set()
        person_critical_count = {pid: 0 for pid in personnel_ids}
        
        for pair in all_possible_pairs:
            person_id = pair['person_id']
            first_date = pair['first_date']
            second_date = pair['second_date']
            
            if (first_date not in used_dates and 
                second_date not in used_dates and
                person_id not in used_persons_for_pairs and
                person_critical_count[person_id] <= 1):
                
                reserved_assignments[first_date] = (first_date, person_id, pair['first_name'])
                reserved_assignments[second_date] = (second_date, person_id, pair['second_name'])
                
                used_dates.add(first_date)
                used_dates.add(second_date)
                used_persons_for_pairs.add(person_id)
                
                person_critical_count[person_id] += 2
        
        remaining_critical_days = []
        for day_data in all_days:
            current_date, day_name, week_number, day_info = day_data
            if (day_name in ['Perşembe', 'Cuma', 'Cumartesi', 'Pazar', 'Pazartesi'] and 
                current_date not in reserved_assignments):
                remaining_critical_days.append(day_data)
        
        for day_data in remaining_critical_days:
            current_date, day_name, week_number, day_info = day_data
            
            eligible_personnel = []
            for person_id in personnel_ids:
                if person_critical_count[person_id] >= 3:
                    continue
                
                if not self.is_person_eligible_for_pairing(
                    person_id, current_date, day_name, exemption_dict, 
                    last_month_duty_person, reserved_assignments
                ):
                    continue
                
                week_conflict = False
                if week_number in weeks:
                    for check_day_data in weeks[week_number]:
                        check_date = check_day_data[0]
                        if check_date in reserved_assignments:
                            if reserved_assignments[check_date][1] == person_id:
                                week_conflict = True
                                break
                
                if week_conflict:
                    continue
                
                priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                eligible_personnel.append((person_id, priority_score))
            
            if eligible_personnel:
                eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                best_person = eligible_personnel[0][0]
                
                reserved_assignments[current_date] = (current_date, best_person, day_name)
                person_critical_count[best_person] += 1
        
        schedule = []
        
        for day_data in all_days:
            current_date, day_name, week_number, day_info = day_data
            
            if current_date in reserved_assignments:
                _, person_id, _ = reserved_assignments[current_date]
                schedule.append((current_date, person_id, day_name))
            else:
                eligible_personnel = []
                for person_id in personnel_ids:
                    if (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                        exemption_dict[person_id][current_date] == 0):
                        continue
                    
                    if current_date.day == 1 and person_id == last_month_duty_person:
                        if not (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                               exemption_dict[person_id][current_date] == 1):
                            continue
                    
                    if self.has_consecutive_days_conflict(person_id, current_date, schedule):
                        continue
                    
                    priority_score = self.calculate_priority_score(person_id, stats, avg_count, avg_value)
                    
                    if (person_id in exemption_dict and current_date in exemption_dict[person_id] and 
                        exemption_dict[person_id][current_date] == 1):
                        priority_score += 1000
                    
                    eligible_personnel.append((person_id, priority_score))
                
                if eligible_personnel:
                    eligible_personnel.sort(key=lambda x: x[1], reverse=True)
                    selected_person_id = eligible_personnel[0][0]
                    
                    schedule.append((current_date, selected_person_id, day_name))
                    
                    stats[selected_person_id]['count'] += 1
                    stats[selected_person_id]['total_value'] += day_info['value']
                else:
                    schedule.append((current_date, None, day_name))
        
        return schedule
    
    def generate_schedule(self, year, month):
        """Ana nöbet programı oluşturma metodu"""
        return self.generate_schedule_with_global_optimization(year, month)
    
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
        """
        from collections import defaultdict
        import calendar
        
        personnel_counts = defaultdict(int)
        personnel_names = {}
        
        personnel = self.get_active_personnel()
        for person_id, name, status in personnel:
            personnel_names[person_id] = name
            personnel_counts[person_id] = 0  # Başlangıçta 0
        
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
