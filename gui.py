import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import calendar
from database import Database
from scheduler import DutyScheduler
from excel_exporter import ExcelExporter

class DutySchedulerGUI:
    TURKISH_MONTHS = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
        7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Nöbet Programı Yönetim Sistemi")
        self.root.geometry("1200x800")
        
        self.db = Database()
        self.scheduler = DutyScheduler(self.db)
        self.exporter = ExcelExporter(self.db)
        
        self.current_schedule = []
        self.selected_year = datetime.now().year
        self.selected_month = datetime.now().month
        self.day_cells = {}
        
        self.min_nob_var = None
        self.max_nob_var = None
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        control_frame = ttk.LabelFrame(main_frame, text="Kontrol Paneli", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Yıl:").grid(row=0, column=0, padx=(0, 5))
        self.year_var = tk.StringVar(value=str(self.selected_year))
        year_combo = ttk.Combobox(control_frame, textvariable=self.year_var, width=10)
        year_combo['values'] = [str(y) for y in range(2020, 2030)]
        year_combo.grid(row=0, column=1, padx=(0, 20))
        year_combo.bind('<<ComboboxSelected>>', self.on_date_change)
        
        ttk.Label(control_frame, text="Ay:").grid(row=0, column=2, padx=(0, 5))
        self.month_var = tk.StringVar(value=str(self.selected_month))
        month_combo = ttk.Combobox(control_frame, textvariable=self.month_var, width=10)
        month_combo['values'] = [f"{i} - {self.TURKISH_MONTHS[i]}" for i in range(1, 13)]
        month_combo.grid(row=0, column=3, padx=(0, 20))
        month_combo.bind('<<ComboboxSelected>>', self.on_date_change)
        
        ttk.Label(control_frame, text="Min Nöbet:").grid(row=0, column=4, padx=(0, 5))
        self.min_nob_var = tk.StringVar(value="3")
        min_nob_entry = ttk.Entry(control_frame, textvariable=self.min_nob_var, width=5)
        min_nob_entry.grid(row=0, column=5, padx=(0, 10))
        
        ttk.Label(control_frame, text="Max Nöbet:").grid(row=0, column=6, padx=(0, 5))
        self.max_nob_var = tk.StringVar(value="4")
        max_nob_entry = ttk.Entry(control_frame, textvariable=self.max_nob_var, width=5)
        max_nob_entry.grid(row=0, column=7, padx=(0, 20))
        
        ttk.Button(control_frame, text="Nöbet Hazırla", command=self.generate_schedule).grid(row=0, column=8, padx=(0, 10))
        ttk.Button(control_frame, text="Excel'e Aktar", command=self.export_to_excel).grid(row=0, column=9, padx=(0, 10))
        ttk.Button(control_frame, text="Kaydet", command=self.save_schedule).grid(row=0, column=10, padx=(0, 10))
        ttk.Button(control_frame, text="Personel Ekle", command=self.open_personnel_window).grid(row=0, column=11, padx=(0, 10))
        ttk.Button(control_frame, text="Mazeret Girişi", command=self.open_mazeret_window).grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(control_frame, text="Eski Nöbetler", command=self.open_old_duties_window).grid(row=1, column=2, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(control_frame, text="Gün Değerleri", command=self.open_gun_deger_window).grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(control_frame, text="Tatil Yönetimi", command=self.open_tatil_window).grid(row=2, column=2, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(control_frame, text="Bilgi", command=self.open_info_window).grid(row=2, column=4, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        info_frame = ttk.LabelFrame(main_frame, text="Personel Bilgileri", padding="10")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        self.personnel_tree = ttk.Treeview(info_frame, columns=('ID', 'Ad', 'Statü', 'Aktif'), show='headings', height=8)
        self.personnel_tree.heading('ID', text='ID')
        self.personnel_tree.heading('Ad', text='Ad')
        self.personnel_tree.heading('Statü', text='Statü')
        self.personnel_tree.heading('Aktif', text='Aktif')
        
        self.personnel_tree.column('ID', width=50)
        self.personnel_tree.column('Ad', width=100)
        self.personnel_tree.column('Statü', width=100)
        self.personnel_tree.column('Aktif', width=60)
        
        personnel_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.personnel_tree.yview)
        self.personnel_tree.configure(yscrollcommand=personnel_scroll.set)
        
        self.personnel_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        personnel_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        schedule_frame = ttk.LabelFrame(main_frame, text="Nöbet Programı", padding="10")
        schedule_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        schedule_frame.columnconfigure(0, weight=1)
        schedule_frame.rowconfigure(1, weight=1)
        
        self.setup_calendar_view(schedule_frame)
        
        stats_frame = ttk.LabelFrame(main_frame, text="İstatistikler", padding="10")
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
        
        self.stats_tree = ttk.Treeview(stats_frame, columns=('Personel', 'Nöbet Sayısı', 'Toplam Puan'), show='headings', height=8)
        self.stats_tree.heading('Personel', text='Personel')
        self.stats_tree.heading('Nöbet Sayısı', text='Nöbet Sayısı')
        self.stats_tree.heading('Toplam Puan', text='Toplam Puan')
        
        self.stats_tree.column('Personel', width=120)
        self.stats_tree.column('Nöbet Sayısı', width=100)
        self.stats_tree.column('Toplam Puan', width=100)
        
        stats_scroll = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scroll.set)
        
        self.stats_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def setup_calendar_view(self, parent_frame):
        header_frame = ttk.Frame(parent_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=1)
        header_frame.columnconfigure(3, weight=1)
        header_frame.columnconfigure(4, weight=1)
        header_frame.columnconfigure(5, weight=1)
        header_frame.columnconfigure(6, weight=1)
        
        weekdays = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        for i, day_name in enumerate(weekdays):
            header_label = ttk.Label(header_frame, text=day_name, font=('Arial', 10, 'bold'))
            header_label.grid(row=0, column=i, padx=1, pady=2, sticky=(tk.W, tk.E))
        
        calendar_container = ttk.Frame(parent_frame)
        calendar_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        canvas = tk.Canvas(calendar_container, bg='white')
        scrollbar = ttk.Scrollbar(calendar_container, orient="vertical", command=canvas.yview)
        self.calendar_frame = ttk.Frame(canvas)
        
        self.calendar_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.calendar_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        calendar_container.columnconfigure(0, weight=1)
        calendar_container.rowconfigure(0, weight=1)
        
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
    
    def get_day_color(self, date_obj, day_type, is_consecutive=False):
        weekday = date_obj.weekday()
        
        if is_consecutive:
            return '#FFB6C1'
        elif 'Tatil' in day_type or 'Resmi Tatil' in day_type:
            return '#FFE4B5'
        elif weekday in [5, 6]:
            return '#E6F3FF'
        else:
            return '#F8F8F8'
    
    def create_day_cell(self, parent, row, col, day_num, person_name, day_type, date_obj, is_consecutive=False):
        cell_color = self.get_day_color(date_obj, day_type, is_consecutive)
        
        cell_frame = tk.Frame(parent, bg=cell_color, relief='solid', bd=1, width=100, height=80)
        cell_frame.grid(row=row, column=col, padx=1, pady=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        cell_frame.grid_propagate(False)
        
        day_label = tk.Label(cell_frame, text=str(day_num), font=('Arial', 12, 'bold'), 
                           bg=cell_color, fg='black')
        day_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        if person_name and person_name != "ATANMADI":
            text_color = 'darkred' if is_consecutive else 'darkblue'
            person_label = tk.Label(cell_frame, text=person_name, font=('Arial', 9), 
                                  bg=cell_color, fg=text_color, wraplength=90)
            person_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        if 'Tatil' in day_type or day_type not in ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']:
            type_label = tk.Label(cell_frame, text=day_type, font=('Arial', 8), 
                                bg=cell_color, fg='darkred', wraplength=90)
            type_label.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        if is_consecutive:
            warning_label = tk.Label(cell_frame, text="⚠️", font=('Arial', 8), 
                                   bg=cell_color, fg='red')
            warning_label.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        cell_frame.columnconfigure(0, weight=1)
        
        right_click_handler = lambda e: self.show_duty_change_menu(e, date_obj, person_name)
        cell_frame.bind("<Button-3>", right_click_handler)
        day_label.bind("<Button-3>", right_click_handler)
        if person_name and person_name != "ATANMADI":
            person_label.bind("<Button-3>", right_click_handler)
        if 'Tatil' in day_type or day_type not in ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']:
            type_label.bind("<Button-3>", right_click_handler)
        
        return cell_frame
    
    def show_duty_change_menu(self, event, date_obj, current_person):
        """Nöbet değiştirme menüsünü gösterir"""
        if not current_person or current_person == "ATANMADI":
            messagebox.showinfo("Bilgi", "Bu günde atanmış personel yok!")
            return
        
        date_str = date_obj.strftime('%Y-%m-%d')
        
        change_window = tk.Toplevel(self.root)
        change_window.title(f"Nöbet Değiştir - {date_str}")
        change_window.geometry("400x300")
        change_window.resizable(False, False)
        
        main_frame = ttk.Frame(change_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        change_window.columnconfigure(0, weight=1)
        change_window.rowconfigure(0, weight=1)
        
        ttk.Label(main_frame, text=f"Tarih: {date_str}", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(main_frame, text=f"Mevcut Personel: {current_person}", font=('Arial', 10)).grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Label(main_frame, text="Yeni Personel:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        new_personel_var = tk.StringVar()
        new_personel_combo = ttk.Combobox(main_frame, textvariable=new_personel_var, width=25, state="readonly")
        new_personel_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad FROM Personel WHERE Aktif = 1 ORDER BY ad")
        personnel_list = cursor.fetchall()
        conn.close()
        
        new_personel_combo['values'] = [f"{p[0]} - {p[1]}" for p in personnel_list]
        
        main_frame.columnconfigure(1, weight=1)
        
        def change_duty():
            new_personel_text = new_personel_var.get().strip()
            
            if not new_personel_text:
                messagebox.showerror("Hata", "Lütfen yeni personel seçin!")
                return
            
            try:
                new_personel_id = int(new_personel_text.split(' - ')[0])
                new_personel_name = new_personel_text.split(' - ')[1]
                
                if new_personel_name == current_person:
                    messagebox.showwarning("Uyarı", "Aynı personel seçildi!")
                    return
                
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                day_name = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'][target_date.weekday()]
                
                is_mazeret, tut_value = self.scheduler.is_mazeret_entry(new_personel_id, target_date, self.selected_year, self.selected_month)
                
                if not is_mazeret:
                    warning_result = messagebox.askyesno(
                        "Mazeret Dışı Değişiklik Uyarısı",
                        f"⚠️ UYARI: MAZERET GİRİŞLERİ DIŞINDA BİR DEĞİŞİKLİK YAPILIYOR!\n\n"
                        f"Tarih: {date_str}\n"
                        f"Yeni Personel: {new_personel_name}\n\n"
                        f"Bu değişiklik Mazeret tablosunda kayıtlı değildir.\n"
                        f"Devam etmek istiyor musunuz?"
                    )
                    
                    if not warning_result:
                        return
                
                current_schedule = getattr(self, 'current_schedule', [])
                violations = self.scheduler.check_duty_change_constraints(
                    new_personel_id, target_date, day_name, current_schedule, 
                    self.selected_year, self.selected_month
                )
                
                if violations:
                    if not self.show_constraint_override_dialog(violations, new_personel_name, date_str):
                        return
                
                self.execute_duty_change(new_personel_id, new_personel_name, date_str, change_window, current_person)
                
            except Exception as e:
                messagebox.showerror("Hata", f"Nöbet değiştirme sırasında hata: {str(e)}")
        
        def cancel_change():
            change_window.destroy()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Değiştir", command=change_duty).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="İptal", command=cancel_change).grid(row=0, column=1, padx=5)
        
        change_window.transient(self.root)
        change_window.grab_set()
        
        new_personel_combo.focus()
    
    def show_constraint_override_dialog(self, violations, person_name, date_str):
        """Kısıtlama ihlali uyarısı ve geçersiz kılma seçenekleri"""
        override_window = tk.Toplevel(self.root)
        override_window.title("Kısıtlama İhlali Uyarısı")
        override_window.geometry("600x500")
        override_window.resizable(True, True)
        override_window.grab_set()
        
        main_frame = ttk.Frame(override_window, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        override_window.columnconfigure(0, weight=1)
        override_window.rowconfigure(0, weight=1)
        
        header_label = ttk.Label(main_frame, text="⚠️ OLASILIKSIZ BİR GİRİŞ TESPİT EDİLDİ!", 
                               font=('Arial', 14, 'bold'), foreground='red')
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        details_text = f"Personel: {person_name}\nTarih: {date_str}\n\n"
        details_label = ttk.Label(main_frame, text=details_text, font=('Arial', 10))
        details_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        violations_label = ttk.Label(main_frame, text="İhlal Edilen Kısıtlamalar:", 
                                   font=('Arial', 12, 'bold'))
        violations_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        violations_frame = ttk.Frame(main_frame)
        violations_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        violations_text = tk.Text(violations_frame, height=8, width=70, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(violations_frame, orient=tk.VERTICAL, command=violations_text.yview)
        violations_text.configure(yscrollcommand=scrollbar.set)
        
        violations_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        violations_frame.columnconfigure(0, weight=1)
        violations_frame.rowconfigure(0, weight=1)
        
        for i, violation in enumerate(violations, 1):
            violations_text.insert(tk.END, f"{i}. {violation}\n\n")
        violations_text.config(state=tk.DISABLED)
        
        override_label = ttk.Label(main_frame, text="Geçersiz Kılma Seçenekleri:", 
                                 font=('Arial', 12, 'bold'))
        override_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        result = {'continue': False}
        
        def override_day_pairing():
            result['continue'] = messagebox.askyesno(
                "Gün Eşleştirme Kuralını Geçersiz Kıl",
                "⚠️ GÜN EŞLEŞTIRME KURALI DEVRE DIŞI BIRAKILACAK!\n\n"
                "Bu işlem Perşembe↔Cumartesi ve Pazar↔Cuma eşleştirme kurallarını "
                "bu atama için geçersiz kılacaktır.\n\n"
                "Devam etmek istiyor musunuz?"
            )
            if result['continue']:
                override_window.destroy()
        
        def override_year_points():
            result['continue'] = messagebox.askyesno(
                "Yıllık Puan Durumunu Geçersiz Kıl",
                "⚠️ YILLIK PUAN DURUMU DEVRE DIŞI BIRAKILACAK!\n\n"
                "Bu işlem yıllık puan adaleti ve dağıtım kurallarını "
                "bu atama için geçersiz kılacaktır.\n\n"
                "UYARI: Bu işlem sistem dengesini bozabilir!\n\n"
                "Devam etmek istiyor musunuz?"
            )
            if result['continue']:
                override_window.destroy()
        
        def cancel_change():
            result['continue'] = False
            override_window.destroy()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))
        
        ttk.Button(button_frame, text="Gün Eşleştirme Kuralını Geçersiz Kıl", 
                 command=override_day_pairing).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Yıllık Puan Durumunu Geçersiz Kıl", 
                 command=override_year_points).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="İptal", command=cancel_change).grid(row=0, column=2)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        override_window.wait_window()
        return result['continue']
    
    def execute_duty_change(self, new_personel_id, new_personel_name, date_str, change_window=None, current_person=None):
        """Nöbet değişikliğini gerçekleştirir"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, personelId, gunDegerId, ad, deger, esTarih, yenTarih
            FROM Nobet 
            WHERE tarih = ?
        """, (date_str,))
        
        nobet_record = cursor.fetchone()
        
        if nobet_record:
            cursor.execute("""
                UPDATE Nobet 
                SET personelId = ?, degisiklik = 1, esTarih = ?, yenTarih = ?
                WHERE id = ?
            """, (new_personel_id, date_str, date_str, nobet_record[0]))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Başarılı", f"Nöbet değiştirildi!\n{self.scheduler.get_person_name(nobet_record[1])} → {new_personel_name}")
            
            self.load_existing_schedule()
            if change_window:
                change_window.destroy()
        else:
            conn.close()
            
            if hasattr(self, 'current_schedule') and self.current_schedule:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                for i, (scheduled_date, person_id, day_type) in enumerate(self.current_schedule):
                    if scheduled_date == target_date:
                        self.current_schedule[i] = (scheduled_date, new_personel_id, day_type)
                        break
                
                self.generate_schedule_display()
                
                messagebox.showinfo("Başarılı", f"Nöbet değiştirildi!\n{current_person or 'Önceki'} → {new_personel_name}\n(Değişiklikleri kaydetmeyi unutmayın!)")
                if change_window:
                    change_window.destroy()
            else:
                messagebox.showerror("Hata", "Önce nöbet programını hazırlayın!")
    
    def load_initial_data(self):
        self.db.check_and_populate_sample_data()
        self.load_personnel()
        self.load_existing_schedule()
        self.update_stats()
    
    def load_personnel(self):
        for item in self.personnel_tree.get_children():
            self.personnel_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad, statu, Aktif FROM Personel ORDER BY ad")
        personnel = cursor.fetchall()
        conn.close()
        
        for person in personnel:
            aktif_text = "Evet" if person[3] else "Hayır"
            self.personnel_tree.insert('', 'end', values=(person[0], person[1], person[2], aktif_text))
    
    def on_date_change(self, event=None):
        try:
            self.selected_year = int(self.year_var.get())
            month_text = self.month_var.get()
            if ' - ' in month_text:
                self.selected_month = int(month_text.split(' - ')[0])
            else:
                self.selected_month = int(month_text)
            
            self.load_existing_schedule()
            self.update_stats()
        except Exception as e:
            print(f"Date change error: {e}")
            self.populate_calendar()
    
    def load_existing_schedule(self):
        for cell in self.day_cells.values():
            cell.destroy()
        self.day_cells.clear()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT n.tarih, p.ad, gd.ad, n.deger
            FROM Nobet n
            JOIN Personel p ON n.personelId = p.id
            JOIN GunDeger gd ON n.gunDegerId = gd.id
            WHERE strftime('%Y-%m', n.tarih) = ?
            ORDER BY n.tarih
        """, (f"{self.selected_year:04d}-{self.selected_month:02d}",))
        
        schedule_data = cursor.fetchall()
        conn.close()
        
        schedule_dict = {}
        for row in schedule_data:
            date_str = row[0]
            schedule_dict[date_str] = {
                'person': row[1],
                'day_type': row[2],
                'value': row[3]
            }
        
        self.populate_calendar(schedule_dict)
    
    def generate_schedule(self):
        try:
            try:
                min_nob = int(self.min_nob_var.get())
                max_nob = int(self.max_nob_var.get())
                
                if min_nob < 0:
                    messagebox.showerror("Hata", "Minimum nöbet sayısı 0'dan küçük olamaz!")
                    return
                if max_nob < min_nob:
                    messagebox.showerror("Hata", "Maximum nöbet sayısı minimum nöbet sayısından küçük olamaz!")
                    return
                if max_nob > 31:
                    messagebox.showerror("Hata", "Maximum nöbet sayısı 31'den büyük olamaz!")
                    return
                    
            except ValueError:
                messagebox.showerror("Hata", "Min/Max nöbet değerleri geçerli sayılar olmalıdır!")
                return
            
            self.current_schedule = self.scheduler.generate_schedule(self.selected_year, self.selected_month, min_nob, max_nob)
            
            for cell in self.day_cells.values():
                cell.destroy()
            self.day_cells.clear()
            
            schedule_dict = {}
            for scheduled_date, person_id, day_type in self.current_schedule:
                date_str = scheduled_date.strftime('%Y-%m-%d')
                if person_id:
                    person_name = self.scheduler.get_person_name(person_id)
                else:
                    person_name = "ATANMADI"
                
                schedule_dict[date_str] = {
                    'person': person_name,
                    'day_type': day_type,
                    'value': 0
                }
            
            self.populate_calendar(schedule_dict)
            
            schedule_display = self.scheduler.display_schedule(self.current_schedule, self.selected_year, self.selected_month)
            
            consecutive_assignments = self.scheduler.detect_consecutive_assignments(self.current_schedule)
            if consecutive_assignments:
                messagebox.showwarning("Ardışık Nöbet Uyarısı", 
                                     "⚠️ UYARI: Nöbet programında ardışık nöbet atamaları tespit edildi!\n\n" +
                                     "Kırmızı renkle işaretlenmiş günleri kontrol edin.\n" +
                                     "Detaylar için nöbet listesini inceleyin.")
            
            detail_window = tk.Toplevel(self.root)
            detail_window.title("Nöbet Programı Hazırlandı")
            detail_window.geometry("600x700")
            detail_window.resizable(True, True)
            
            main_label = ttk.Label(detail_window, text=f"{self.selected_year}/{self.selected_month} ayı için nöbet programı hazırlandı!", 
                                 font=("Arial", 12, "bold"))
            main_label.pack(pady=10)
            
            if consecutive_assignments:
                warning_label = ttk.Label(detail_window, 
                                        text="⚠️ UYARI: Ardışık nöbet atamaları tespit edildi!", 
                                        font=("Arial", 10, "bold"), 
                                        foreground="red")
                warning_label.pack(pady=5)
            
            frame = ttk.Frame(detail_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10))
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            lines = schedule_display.split('\n')
            for line in lines:
                if "⚠️ ARDIŞIK NÖBET" in line:
                    text_widget.insert(tk.END, line + '\n', 'consecutive')
                else:
                    text_widget.insert(tk.END, line + '\n')
            
            text_widget.tag_configure('consecutive', foreground='red', font=('Courier', 10, 'bold'))
            text_widget.config(state=tk.DISABLED)
            
            close_button = ttk.Button(detail_window, text="Kapat", command=detail_window.destroy)
            close_button.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Nöbet programı hazırlanırken hata oluştu: {str(e)}")
    
    def generate_schedule_display(self):
        """Refresh calendar display from current_schedule without regenerating"""
        if not self.current_schedule:
            return
            
        for cell in self.day_cells.values():
            cell.destroy()
        self.day_cells.clear()
        
        schedule_dict = {}
        for scheduled_date, person_id, day_type in self.current_schedule:
            date_str = scheduled_date.strftime('%Y-%m-%d')
            if person_id:
                person_name = self.scheduler.get_person_name(person_id)
            else:
                person_name = "ATANMADI"
            
            schedule_dict[date_str] = {
                'person': person_name,
                'day_type': day_type,
                'value': 0
            }
        
        self.populate_calendar(schedule_dict)
    
    def check_consecutive_assignments(self):
        """Ardışık nöbet atamalarını kontrol eder ve uyarı verir"""
        if not hasattr(self, 'current_schedule') or not self.current_schedule:
            return True
        
        consecutive_assignments = self.scheduler.detect_consecutive_assignments(self.current_schedule)
        if consecutive_assignments:
            consecutive_persons = {}
            for date, person in consecutive_assignments:
                if person not in consecutive_persons:
                    consecutive_persons[person] = []
                consecutive_persons[person].append(date)
            
            warning_msg = "⚠️ UYARI: ARDIŞIK NÖBET ATAMALARI TESPİT EDİLDİ!\n\n"
            warning_msg += "Aşağıdaki personel ardışık günlerde nöbet almaktadır:\n\n"
            
            for person_id, dates in consecutive_persons.items():
                person_name = self.scheduler.get_person_name(person_id)
                date_strs = [d.strftime("%d.%m.%Y") for d in sorted(set(dates))]
                warning_msg += f"• {person_name}: {', '.join(date_strs)}\n"
            
            warning_msg += "\nBu durumda devam etmek istiyor musunuz?"
            
            result = messagebox.askyesno("Ardışık Nöbet Uyarısı", warning_msg)
            return result
        
        return True

    def save_schedule(self):
        if not self.current_schedule:
            messagebox.showwarning("Uyarı", "Önce nöbet programını hazırlayın!")
            return
        
        if not self.check_consecutive_assignments():
            return
        
        try:
            self.scheduler.save_schedule(self.current_schedule, self.selected_year, self.selected_month)
            self.update_stats()
            messagebox.showinfo("Başarılı", "Nöbet programı kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme sırasında hata oluştu: {str(e)}")
    
    def export_to_excel(self):
        try:
            if not self.check_consecutive_assignments():
                return
                
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"nobet_programi_{self.selected_year}_{self.selected_month:02d}.xlsx"
            )
            
            if filename:
                if hasattr(self, 'current_schedule') and self.current_schedule:
                    self.exporter.export_in_memory_schedule(self.current_schedule, self.selected_year, self.selected_month, filename)
                    messagebox.showinfo("Başarılı", f"Excel dosyası kaydedildi: {filename}\n(Hafızadaki programdan oluşturuldu)")
                else:
                    self.exporter.export_monthly_schedule(self.selected_year, self.selected_month, filename)
                    messagebox.showinfo("Başarılı", f"Excel dosyası kaydedildi: {filename}")
        except Exception as e:
            messagebox.showerror("Hata", f"Excel export sırasında hata oluştu: {str(e)}")
    
    def update_stats(self):
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.ad,
                COUNT(n.id) as nobet_sayisi,
                COALESCE(SUM(n.deger), 0) as toplam_puan
            FROM Personel p
            LEFT JOIN Nobet n ON p.id = n.personelId
            WHERE p.Aktif = 1
            GROUP BY p.id, p.ad
            ORDER BY p.ad
        """)
        
        stats_data = cursor.fetchall()
        conn.close()
        
        for row in stats_data:
            self.stats_tree.insert('', 'end', values=(row[0], row[1], f"{row[2]:.1f}"))
    
    def open_personnel_window(self):
        """Personel ekleme penceresini açar"""
        personnel_window = tk.Toplevel(self.root)
        personnel_window.title("Personel Yönetimi")
        personnel_window.geometry("600x500")
        personnel_window.resizable(True, True)
        
        main_frame = ttk.Frame(personnel_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        personnel_window.columnconfigure(0, weight=1)
        personnel_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        form_frame = ttk.LabelFrame(main_frame, text="Yeni Personel Ekle", padding="10")
        form_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(form_frame, text="Ad:").grid(row=0, column=0, sticky=tk.W, pady=2)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        ttk.Label(form_frame, text="Statü:").grid(row=1, column=0, sticky=tk.W, pady=2)
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(form_frame, textvariable=status_var, width=27)
        status_combo['values'] = ('KD.BÇVŞ.', 'BÇVŞ.', 'KD.ÜÇVŞ.', 'ÜÇVŞ.', 'KD.ÇVŞ.')
        status_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        aktif_var = tk.BooleanVar(value=True)
        aktif_check = ttk.Checkbutton(form_frame, text="Aktif", variable=aktif_var)
        aktif_check.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        form_frame.columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        def add_personnel():
            name = name_entry.get().strip()
            status = status_var.get().strip()
            aktif = 1 if aktif_var.get() else 0
            
            if not name or not status:
                messagebox.showerror("Hata", "Ad ve Statü alanları zorunludur!")
                return
            
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("INSERT INTO Personel (ad, statu, Aktif) VALUES (?, ?, ?)", 
                             (name, status, aktif))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Başarılı", f"{name} başarıyla eklendi!")
                
                name_entry.delete(0, tk.END)
                status_var.set('')
                aktif_var.set(True)
                
                refresh_personnel_list()
                self.load_personnel()  # Ana penceredeki listeyi de güncelle
                
            except Exception as e:
                messagebox.showerror("Hata", f"Personel eklenirken hata oluştu: {str(e)}")
        
        def clear_form():
            name_entry.delete(0, tk.END)
            status_var.set('')
            aktif_var.set(True)
        
        ttk.Button(btn_frame, text="Ekle", command=add_personnel).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Temizle", command=clear_form).grid(row=0, column=1, padx=5)
        
        def delete_personnel():
            selection = personnel_tree.selection()
            if not selection:
                messagebox.showwarning("Uyarı", "Lütfen silinecek personeli seçin!")
                return
            
            item = personnel_tree.item(selection[0])
            person_id = item['values'][0]
            person_name = item['values'][1]
            
            if messagebox.askyesno("Onay", f"{person_name} personelini silmek istediğinizden emin misiniz?"):
                try:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Personel WHERE id = ?", (person_id,))
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Başarılı", f"{person_name} personeli başarıyla silindi!")
                    refresh_personnel_list()
                    self.load_personnel()
                except Exception as e:
                    messagebox.showerror("Hata", f"Personel silinirken hata oluştu: {str(e)}")
        
        ttk.Button(btn_frame, text="Sil", command=delete_personnel).grid(row=0, column=2, padx=5)
        
        list_frame = ttk.LabelFrame(main_frame, text="Mevcut Personeller", padding="10")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        main_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        columns = ('ID', 'Ad', 'Statü', 'Aktif')
        personnel_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        personnel_tree.heading('ID', text='ID')
        personnel_tree.heading('Ad', text='Ad')
        personnel_tree.heading('Statü', text='Statü')
        personnel_tree.heading('Aktif', text='Aktif')
        
        personnel_tree.column('ID', width=50)
        personnel_tree.column('Ad', width=150)
        personnel_tree.column('Statü', width=100)
        personnel_tree.column('Aktif', width=80)
        
        personnel_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=personnel_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        personnel_tree.configure(yscrollcommand=scrollbar.set)
        
        def refresh_personnel_list():
            for item in personnel_tree.get_children():
                personnel_tree.delete(item)
            
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, ad, statu, Aktif FROM Personel ORDER BY id")
                personnel_data = cursor.fetchall()
                conn.close()
                
                for person in personnel_data:
                    aktif_text = "Evet" if person[3] else "Hayır"
                    personnel_tree.insert('', tk.END, values=(person[0], person[1], person[2], aktif_text))
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Personel listesi yüklenirken hata: {str(e)}")
        
        def toggle_active():
            selected = personnel_tree.selection()
            if not selected:
                messagebox.showwarning("Uyarı", "Lütfen bir personel seçin!")
                return
            
            item = personnel_tree.item(selected[0])
            person_id = item['values'][0]
            current_status = item['values'][3] == "Evet"
            new_status = not current_status
            
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE Personel SET Aktif = ? WHERE id = ?", 
                             (1 if new_status else 0, person_id))
                conn.commit()
                conn.close()
                
                refresh_personnel_list()
                self.load_personnel()  # Ana penceredeki listeyi de güncelle
                
                status_text = "aktif" if new_status else "pasif"
                messagebox.showinfo("Başarılı", f"Personel durumu {status_text} olarak güncellendi!")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Personel durumu güncellenirken hata: {str(e)}")
        
        bottom_btn_frame = ttk.Frame(list_frame)
        bottom_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(bottom_btn_frame, text="Yenile", command=refresh_personnel_list).grid(row=0, column=0, padx=5)
        ttk.Button(bottom_btn_frame, text="Aktif/Pasif Değiştir", command=toggle_active).grid(row=0, column=1, padx=5)
        
        refresh_personnel_list()
        
        personnel_window.transient(self.root)
        personnel_window.grab_set()
        
        name_entry.focus()
    
    def populate_calendar(self, schedule_dict=None):
        if schedule_dict is None:
            schedule_dict = {}
        
        for cell in self.day_cells.values():
            cell.destroy()
        self.day_cells.clear()
        
        consecutive_dates = set()
        if hasattr(self, 'current_schedule') and self.current_schedule:
            consecutive_assignments = self.scheduler.detect_consecutive_assignments(self.current_schedule)
            consecutive_dates = set(date for date, person in consecutive_assignments)
        
        days_in_month = calendar.monthrange(self.selected_year, self.selected_month)[1]
        first_weekday = calendar.monthrange(self.selected_year, self.selected_month)[0]
        
        current_row = 0
        current_col = first_weekday
        
        for day in range(1, days_in_month + 1):
            date_obj = date(self.selected_year, self.selected_month, day)
            date_str = date_obj.strftime('%Y-%m-%d')
            
            if date_str in schedule_dict:
                person_name = schedule_dict[date_str]['person']
                day_type = schedule_dict[date_str]['day_type']
            else:
                person_name = ""
                weekday = date_obj.weekday()
                weekday_names = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
                day_type = weekday_names[weekday]
            
            is_consecutive = date_obj in consecutive_dates
            
            cell = self.create_day_cell(self.calendar_frame, current_row, current_col, 
                                      day, person_name, day_type, date_obj, is_consecutive)
            self.day_cells[date_str] = cell
            
            current_col += 1
            if current_col > 6:
                current_col = 0
                current_row += 1
    
    def open_mazeret_window(self):
        """Mazeret girişi penceresini açar"""
        mazeret_window = tk.Toplevel(self.root)
        mazeret_window.title("Mazeret Girişi")
        mazeret_window.geometry("700x600")
        mazeret_window.resizable(True, True)
        
        main_frame = ttk.Frame(mazeret_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        mazeret_window.columnconfigure(0, weight=1)
        mazeret_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        form_frame = ttk.LabelFrame(main_frame, text="Yeni Mazeret Girişi", padding="10")
        form_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(form_frame, text="Personel:").grid(row=0, column=0, sticky=tk.W, pady=2)
        personel_var = tk.StringVar()
        personel_combo = ttk.Combobox(form_frame, textvariable=personel_var, width=30, state="readonly")
        personel_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, ad FROM Personel WHERE Aktif = 1 ORDER BY ad")
        personnel_list = cursor.fetchall()
        conn.close()
        
        personel_combo['values'] = [f"{p[0]} - {p[1]}" for p in personnel_list]
        
        ttk.Label(form_frame, text="Tarih:").grid(row=1, column=0, sticky=tk.W, pady=2)
        tarih_var = tk.StringVar()
        mazeret_date_frame = self.create_date_picker(form_frame, tarih_var, "")
        mazeret_date_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        tarih_var.set(datetime.now().strftime('%d.%m.%Y'))
        
        ttk.Label(form_frame, text="Ek Gün Sayısı:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ek_gun_var = tk.StringVar(value="0")
        ek_gun_entry = ttk.Entry(form_frame, textvariable=ek_gun_var, width=10)
        ek_gun_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        tut_var = tk.BooleanVar(value=False)
        tut_check = ttk.Checkbutton(form_frame, text="Tutulacak (Bu tarihe nöbet yazılsın)", variable=tut_var)
        tut_check.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        form_frame.columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        def add_mazeret():
            personel_text = personel_var.get().strip()
            tarih_str = tarih_var.get().strip()
            ek_gun_str = ek_gun_var.get().strip()
            tut = 1 if tut_var.get() else 0
            
            if not personel_text or not tarih_str:
                messagebox.showerror("Hata", "Personel ve Tarih alanları zorunludur!")
                return
            
            try:
                personel_id = int(personel_text.split(' - ')[0])
                
                try:
                    ek_gun_sayisi = int(ek_gun_str) if ek_gun_str else 0
                    if ek_gun_sayisi < 0:
                        messagebox.showerror("Hata", "Ek gün sayısı negatif olamaz!")
                        return
                except ValueError:
                    messagebox.showerror("Hata", "Ek gün sayısı geçerli bir sayı olmalıdır!")
                    return
                
                from datetime import datetime, timedelta
                try:
                    tarih_obj = datetime.strptime(tarih_str, '%d.%m.%Y')
                    tarih_db = tarih_obj.strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        tarih_obj = datetime.strptime(tarih_str, '%Y-%m-%d')
                        tarih_db = tarih_str
                        tarih_obj = datetime.strptime(tarih_str, '%Y-%m-%d')
                    except ValueError:
                        messagebox.showerror("Hata", "Geçersiz tarih formatı! (GG.AA.YYYY formatında girin)")
                        return
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                eklenen_tarihler = []
                atlanan_tarihler = []
                
                for i in range(ek_gun_sayisi + 1):  # +1 çünkü başlangıç tarihi de dahil
                    hedef_tarih = tarih_obj + timedelta(days=i)
                    hedef_tarih_db = hedef_tarih.strftime('%Y-%m-%d')
                    
                    cursor.execute("SELECT COUNT(*) FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                                 (personel_id, hedef_tarih_db))
                    if cursor.fetchone()[0] > 0:
                        atlanan_tarihler.append(hedef_tarih.strftime('%d.%m.%Y'))
                        continue
                    
                    cursor.execute("INSERT INTO Mazeret (personelId, tarih, tut) VALUES (?, ?, ?)", 
                                 (personel_id, hedef_tarih_db, tut))
                    eklenen_tarihler.append(hedef_tarih.strftime('%d.%m.%Y'))
                
                conn.commit()
                conn.close()
                
                tut_text = "tutulacak" if tut else "tutulmayacak"
                mesaj = f"Mazeret kayıtları eklendi! ({tut_text})\n\n"
                
                if eklenen_tarihler:
                    mesaj += f"Eklenen tarihler ({len(eklenen_tarihler)} adet):\n"
                    mesaj += ", ".join(eklenen_tarihler)
                
                if atlanan_tarihler:
                    mesaj += f"\n\nAtlanan tarihler (zaten mevcut - {len(atlanan_tarihler)} adet):\n"
                    mesaj += ", ".join(atlanan_tarihler)
                
                messagebox.showinfo("Başarılı", mesaj)
                
                personel_var.set('')
                tarih_var.set(datetime.now().strftime('%d.%m.%Y'))
                ek_gun_var.set("0")
                tut_var.set(False)
                
                refresh_mazeret_list()
                
            except Exception as e:
                messagebox.showerror("Hata", f"Mazeret eklenirken hata oluştu: {str(e)}")
        
        def clear_form():
            personel_var.set('')
            tarih_var.set(datetime.now().strftime('%d.%m.%Y'))
            ek_gun_var.set("0")
            tut_var.set(False)
        
        ttk.Button(btn_frame, text="Ekle", command=add_mazeret).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Temizle", command=clear_form).grid(row=0, column=1, padx=5)
        
        list_frame = ttk.LabelFrame(main_frame, text="Mevcut Mazeret Kayıtları", padding="10")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        main_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        columns = ('ID', 'Personel', 'Tarih', 'Durum')
        mazeret_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        mazeret_tree.heading('ID', text='ID')
        mazeret_tree.heading('Personel', text='Personel')
        mazeret_tree.heading('Tarih', text='Tarih')
        mazeret_tree.heading('Durum', text='Durum')
        
        mazeret_tree.column('ID', width=50)
        mazeret_tree.column('Personel', width=150)
        mazeret_tree.column('Tarih', width=100)
        mazeret_tree.column('Durum', width=120)
        
        mazeret_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=mazeret_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        mazeret_tree.configure(yscrollcommand=scrollbar.set)
        
        def refresh_mazeret_list():
            for item in mazeret_tree.get_children():
                mazeret_tree.delete(item)
            
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.id, p.ad, m.tarih, m.tut
                    FROM Mazeret m
                    JOIN Personel p ON m.personelId = p.id
                    ORDER BY m.tarih DESC, p.ad
                """)
                mazeret_data = cursor.fetchall()
                conn.close()
                
                for mazeret in mazeret_data:
                    from datetime import datetime
                    try:
                        tarih_obj = datetime.strptime(mazeret[2], '%Y-%m-%d')
                        tarih_tr = tarih_obj.strftime('%d.%m.%Y')
                    except:
                        tarih_tr = mazeret[2]
                    
                    durum_text = "Tutulacak" if mazeret[3] else "Tutulmayacak"
                    mazeret_tree.insert('', tk.END, values=(mazeret[0], mazeret[1], tarih_tr, durum_text))
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Mazeret listesi yüklenirken hata: {str(e)}")
        
        def delete_mazeret():
            selected = mazeret_tree.selection()
            if not selected:
                messagebox.showwarning("Uyarı", "Lütfen silinecek mazeret kaydını seçin!")
                return
            
            item = mazeret_tree.item(selected[0])
            mazeret_id = item['values'][0]
            
            result = messagebox.askyesno("Onay", "Seçili mazeret kaydını silmek istediğinizden emin misiniz?")
            if not result:
                return
            
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Mazeret WHERE id = ?", (mazeret_id,))
                conn.commit()
                conn.close()
                
                refresh_mazeret_list()
                messagebox.showinfo("Başarılı", "Mazeret kaydı silindi!")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Mazeret silinirken hata: {str(e)}")
        
        bottom_btn_frame = ttk.Frame(list_frame)
        bottom_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(bottom_btn_frame, text="Yenile", command=refresh_mazeret_list).grid(row=0, column=0, padx=5)
        ttk.Button(bottom_btn_frame, text="Sil", command=delete_mazeret).grid(row=0, column=1, padx=5)
        
        refresh_mazeret_list()
        
        mazeret_window.transient(self.root)
        mazeret_window.grab_set()
        
        personel_combo.focus()
    

    
    def open_old_duties_window(self):
        old_duties_window = tk.Toplevel(self.root)
        old_duties_window.title("Eski Nöbetler")
        old_duties_window.geometry("800x600")
        old_duties_window.transient(self.root)
        old_duties_window.grab_set()
        
        main_frame = ttk.Frame(old_duties_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        date_frame = ttk.LabelFrame(main_frame, text="Tarih Seçimi", padding="10")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="Yıl:").grid(row=0, column=0, padx=(0, 5))
        old_year_var = tk.StringVar(value=str(self.selected_year))
        old_year_combo = ttk.Combobox(date_frame, textvariable=old_year_var, width=10)
        old_year_combo['values'] = [str(y) for y in range(2020, 2030)]
        old_year_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(date_frame, text="Ay:").grid(row=0, column=2, padx=(0, 5))
        old_month_var = tk.StringVar(value=str(self.selected_month))
        old_month_combo = ttk.Combobox(date_frame, textvariable=old_month_var, width=15)
        old_month_combo['values'] = [f"{i} - {self.TURKISH_MONTHS[i]}" for i in range(1, 13)]
        old_month_combo.grid(row=0, column=3, padx=(0, 20))
        
        def refresh_old_duties():
            try:
                year = int(old_year_var.get())
                month_text = old_month_var.get()
                if ' - ' in month_text:
                    month = int(month_text.split(' - ')[0])
                else:
                    month = int(month_text)
                
                for item in old_duties_tree.get_children():
                    old_duties_tree.delete(item)
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT n.tarih, p.ad, p.statu, n.deger, n.degisiklik
                    FROM Nobet n
                    JOIN Personel p ON n.personelId = p.id
                    WHERE strftime('%Y-%m', n.tarih) = ?
                    ORDER BY n.tarih
                """, (f"{year:04d}-{month:02d}",))
                
                duties = cursor.fetchall()
                conn.close()
                
                for duty in duties:
                    date_str = duty[0]
                    person_name = duty[1]
                    person_status = duty[2]
                    duty_value = duty[3]
                    is_changed = "Evet" if duty[4] else "Hayır"
                    
                    old_duties_tree.insert('', 'end', values=(date_str, person_name, person_status, duty_value, is_changed))
                
                status_label.config(text=f"Toplam {len(duties)} nöbet kaydı bulundu.")
                
            except Exception as e:
                messagebox.showerror("Hata", f"Nöbet kayıtları yüklenirken hata oluştu: {str(e)}")
        
        ttk.Button(date_frame, text="Listele", command=refresh_old_duties).grid(row=0, column=4, padx=(10, 0))
        
        list_frame = ttk.LabelFrame(main_frame, text="Nöbet Kayıtları", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        old_duties_tree = ttk.Treeview(list_frame, columns=('Tarih', 'Personel', 'Statü', 'Puan', 'Değiştirildi'), show='headings')
        old_duties_tree.heading('Tarih', text='Tarih')
        old_duties_tree.heading('Personel', text='Personel')
        old_duties_tree.heading('Statü', text='Statü')
        old_duties_tree.heading('Puan', text='Puan')
        old_duties_tree.heading('Değiştirildi', text='Değiştirildi')
        
        old_duties_tree.column('Tarih', width=100)
        old_duties_tree.column('Personel', width=120)
        old_duties_tree.column('Statü', width=100)
        old_duties_tree.column('Puan', width=80)
        old_duties_tree.column('Değiştirildi', width=100)
        
        old_duties_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=old_duties_tree.yview)
        old_duties_tree.configure(yscrollcommand=old_duties_scroll.set)
        
        old_duties_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        old_duties_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        status_label = ttk.Label(bottom_frame, text="Tarih seçip 'Listele' butonuna basın.")
        status_label.pack(side=tk.LEFT)
        
        def delete_month_duties():
            try:
                year = int(old_year_var.get())
                month_text = old_month_var.get()
                if ' - ' in month_text:
                    month = int(month_text.split(' - ')[0])
                else:
                    month = int(month_text)
                
                result = messagebox.askyesno("Onay", 
                    f"{year}/{month:02d} ayına ait tüm nöbet kayıtları silinecek.\nEmin misiniz?")
                
                if result:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Nobet WHERE strftime('%Y-%m', tarih) = ?", 
                                 (f"{year:04d}-{month:02d}",))
                    deleted_count = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Başarılı", f"{deleted_count} nöbet kaydı silindi.")
                    refresh_old_duties()
                    
                    if year == self.selected_year and month == self.selected_month:
                        self.load_existing_schedule()
                        self.update_stats()
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Silme işlemi sırasında hata oluştu: {str(e)}")
        
        ttk.Button(bottom_frame, text="Seçili Ayı Sil", command=delete_month_duties).pack(side=tk.RIGHT)
        
        refresh_old_duties()
    
    def open_gun_deger_window(self):
        gun_deger_window = tk.Toplevel(self.root)
        gun_deger_window.title("Gün Değerleri Yönetimi")
        gun_deger_window.geometry("600x500")
        gun_deger_window.transient(self.root)
        gun_deger_window.grab_set()
        
        main_frame = ttk.Frame(gun_deger_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        form_frame = ttk.LabelFrame(main_frame, text="Gün Değeri Ekle/Düzenle", padding="10")
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(form_frame, text="Ad:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        ad_var = tk.StringVar()
        ad_entry = ttk.Entry(form_frame, textvariable=ad_var, width=30)
        ad_entry.grid(row=0, column=1, padx=(0, 20), sticky=(tk.W, tk.E))
        
        ttk.Label(form_frame, text="Değer:").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        deger_var = tk.StringVar()
        deger_entry = ttk.Entry(form_frame, textvariable=deger_var, width=15)
        deger_entry.grid(row=0, column=3, padx=(0, 10), sticky=(tk.W, tk.E))
        
        form_frame.columnconfigure(1, weight=1)
        
        selected_gun_deger_id = tk.StringVar()
        
        def add_gun_deger():
            try:
                ad = ad_var.get().strip()
                deger = float(deger_var.get().strip())
                
                if not ad:
                    messagebox.showwarning("Uyarı", "Ad alanı boş olamaz!")
                    return
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                if selected_gun_deger_id.get():
                    cursor.execute("UPDATE GunDeger SET ad = ?, deger = ? WHERE id = ?", 
                                 (ad, deger, int(selected_gun_deger_id.get())))
                    messagebox.showinfo("Başarılı", "Gün değeri güncellendi!")
                else:
                    cursor.execute("INSERT INTO GunDeger (ad, deger) VALUES (?, ?)", (ad, deger))
                    messagebox.showinfo("Başarılı", "Gün değeri eklendi!")
                
                conn.commit()
                conn.close()
                
                clear_form()
                refresh_gun_deger_list()
                
            except ValueError:
                messagebox.showerror("Hata", "Değer sayısal olmalıdır!")
            except Exception as e:
                messagebox.showerror("Hata", f"Gün değeri eklenirken hata oluştu: {str(e)}")
        
        def clear_form():
            ad_var.set("")
            deger_var.set("")
            selected_gun_deger_id.set("")
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(button_frame, text="Ekle/Güncelle", command=add_gun_deger).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Temizle", command=clear_form).grid(row=0, column=1, padx=5)
        
        list_frame = ttk.LabelFrame(main_frame, text="Gün Değerleri", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        gun_deger_tree = ttk.Treeview(list_frame, columns=('ID', 'Ad', 'Değer'), show='headings')
        gun_deger_tree.heading('ID', text='ID')
        gun_deger_tree.heading('Ad', text='Ad')
        gun_deger_tree.heading('Değer', text='Değer')
        
        gun_deger_tree.column('ID', width=50)
        gun_deger_tree.column('Ad', width=200)
        gun_deger_tree.column('Değer', width=100)
        
        gun_deger_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=gun_deger_tree.yview)
        gun_deger_tree.configure(yscrollcommand=gun_deger_scroll.set)
        
        gun_deger_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gun_deger_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_gun_deger_list():
            try:
                for item in gun_deger_tree.get_children():
                    gun_deger_tree.delete(item)
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, ad, deger FROM GunDeger ORDER BY id")
                gun_degerleri = cursor.fetchall()
                conn.close()
                
                for gun_deger in gun_degerleri:
                    gun_deger_tree.insert('', 'end', values=gun_deger)
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Gün değerleri yüklenirken hata oluştu: {str(e)}")
        
        def on_gun_deger_select(event):
            selection = gun_deger_tree.selection()
            if selection:
                item = gun_deger_tree.item(selection[0])
                values = item['values']
                selected_gun_deger_id.set(str(values[0]))
                ad_var.set(values[1])
                deger_var.set(str(values[2]))
        
        gun_deger_tree.bind('<<TreeviewSelect>>', on_gun_deger_select)
        
        def delete_gun_deger():
            selection = gun_deger_tree.selection()
            if not selection:
                messagebox.showwarning("Uyarı", "Silinecek gün değerini seçin!")
                return
            
            try:
                item = gun_deger_tree.item(selection[0])
                gun_deger_id = item['values'][0]
                gun_deger_ad = item['values'][1]
                
                result = messagebox.askyesno("Onay", f"'{gun_deger_ad}' gün değeri silinecek. Emin misiniz?")
                if result:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM GunDeger WHERE id = ?", (gun_deger_id,))
                    conn.commit()
                    conn.close()
                    
                    clear_form()
                    refresh_gun_deger_list()
                    messagebox.showinfo("Başarılı", "Gün değeri silindi!")
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Gün değeri silinirken hata oluştu: {str(e)}")
        
        bottom_btn_frame = ttk.Frame(list_frame)
        bottom_btn_frame.pack(pady=(10, 0))
        
        ttk.Button(bottom_btn_frame, text="Yenile", command=refresh_gun_deger_list).grid(row=0, column=0, padx=5)
        ttk.Button(bottom_btn_frame, text="Sil", command=delete_gun_deger).grid(row=0, column=1, padx=5)
        
        refresh_gun_deger_list()
        ad_entry.focus()
    
    def open_tatil_window(self):
        tatil_window = tk.Toplevel(self.root)
        tatil_window.title("Tatil Yönetimi")
        tatil_window.geometry("700x600")
        tatil_window.transient(self.root)
        tatil_window.grab_set()
        
        main_frame = ttk.Frame(tatil_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        form_frame = ttk.LabelFrame(main_frame, text="Tatil Ekle/Düzenle", padding="10")
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(form_frame, text="Gün Değeri:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        gun_deger_var = tk.StringVar()
        gun_deger_combo = ttk.Combobox(form_frame, textvariable=gun_deger_var, width=20, state="readonly")
        gun_deger_combo.grid(row=0, column=1, padx=(0, 20), sticky=(tk.W, tk.E))
        
        ttk.Label(form_frame, text="Ad:").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        tatil_ad_var = tk.StringVar()
        tatil_ad_entry = ttk.Entry(form_frame, textvariable=tatil_ad_var, width=25)
        tatil_ad_entry.grid(row=0, column=3, padx=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(form_frame, text="Tarih:").grid(row=1, column=0, padx=(0, 5), sticky=tk.W)
        tarih_var = tk.StringVar()
        tatil_date_frame = self.create_date_picker(form_frame, tarih_var, "")
        tatil_date_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        
        selected_tatil_id = tk.StringVar()
        
        def load_gun_degerleri():
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, ad, deger FROM GunDeger ORDER BY ad")
                gun_degerleri = cursor.fetchall()
                conn.close()
                
                gun_deger_values = [f"{gd[1]} ({gd[2]} puan)" for gd in gun_degerleri]
                gun_deger_combo['values'] = gun_deger_values
                
                if not hasattr(self, '_gun_deger_map'):
                    self._gun_deger_map = {}
                
                for gd in gun_degerleri:
                    self._gun_deger_map[f"{gd[1]} ({gd[2]} puan)"] = gd[0]
                
            except Exception as e:
                messagebox.showerror("Hata", f"Gün değerleri yüklenirken hata oluştu: {str(e)}")
        
        def add_tatil():
            try:
                gun_deger_text = gun_deger_var.get()
                if not gun_deger_text or ' (' not in gun_deger_text:
                    messagebox.showwarning("Uyarı", "Gün değeri seçin!")
                    return
                
                gun_deger_id = self._gun_deger_map.get(gun_deger_text)
                if not gun_deger_id:
                    messagebox.showerror("Hata", "Geçersiz gün değeri seçimi!")
                    return
                tatil_ad = tatil_ad_var.get().strip()
                tarih_str = tarih_var.get().strip()
                
                if not tatil_ad:
                    messagebox.showwarning("Uyarı", "Tatil adı boş olamaz!")
                    return
                
                if not tarih_str:
                    messagebox.showwarning("Uyarı", "Tarih seçin!")
                    return
                
                from datetime import datetime
                try:
                    tarih_obj = datetime.strptime(tarih_str, '%d.%m.%Y')
                    tarih = tarih_obj.strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        tarih_obj = datetime.strptime(tarih_str, '%Y-%m-%d')
                        tarih = tarih_str
                    except ValueError:
                        messagebox.showerror("Hata", "Geçersiz tarih formatı! (GG.AA.YYYY formatında girin)")
                        return
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                if selected_tatil_id.get():
                    cursor.execute("UPDATE Tatil SET gunDegerId = ?, ad = ?, tarih = ? WHERE id = ?", 
                                 (gun_deger_id, tatil_ad, tarih, int(selected_tatil_id.get())))
                    messagebox.showinfo("Başarılı", "Tatil güncellendi!")
                else:
                    cursor.execute("INSERT INTO Tatil (gunDegerId, ad, tarih) VALUES (?, ?, ?)", 
                                 (gun_deger_id, tatil_ad, tarih))
                    messagebox.showinfo("Başarılı", "Tatil eklendi!")
                
                conn.commit()
                conn.close()
                
                clear_tatil_form()
                refresh_tatil_list()
                
            except Exception as e:
                messagebox.showerror("Hata", f"Tatil eklenirken hata oluştu: {str(e)}")
        
        def clear_tatil_form():
            gun_deger_var.set("")
            tatil_ad_var.set("")
            tarih_var.set("")
            selected_tatil_id.set("")
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(button_frame, text="Ekle/Güncelle", command=add_tatil).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Temizle", command=clear_tatil_form).grid(row=0, column=1, padx=5)
        
        list_frame = ttk.LabelFrame(main_frame, text="Tatiller", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        tatil_tree = ttk.Treeview(list_frame, columns=('ID', 'Gün Değeri', 'Ad', 'Tarih'), show='headings')
        tatil_tree.heading('ID', text='ID')
        tatil_tree.heading('Gün Değeri', text='Gün Değeri')
        tatil_tree.heading('Ad', text='Ad')
        tatil_tree.heading('Tarih', text='Tarih')
        
        tatil_tree.column('ID', width=50)
        tatil_tree.column('Gün Değeri', width=150)
        tatil_tree.column('Ad', width=200)
        tatil_tree.column('Tarih', width=100)
        
        tatil_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tatil_tree.yview)
        tatil_tree.configure(yscrollcommand=tatil_scroll.set)
        
        tatil_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tatil_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_tatil_list():
            try:
                for item in tatil_tree.get_children():
                    tatil_tree.delete(item)
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.id, g.ad, t.ad, t.tarih, t.gunDegerId
                    FROM Tatil t
                    JOIN GunDeger g ON t.gunDegerId = g.id
                    ORDER BY t.tarih
                """)
                tatiller = cursor.fetchall()
                conn.close()
                
                for tatil in tatiller:
                    from datetime import datetime
                    try:
                        tarih_obj = datetime.strptime(tatil[3], '%Y-%m-%d')
                        tarih_tr = tarih_obj.strftime('%d.%m.%Y')
                    except:
                        tarih_tr = tatil[3]
                    
                    tatil_tree.insert('', 'end', values=(tatil[0], tatil[1], tatil[2], tarih_tr))
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Tatiller yüklenirken hata oluştu: {str(e)}")
        
        def on_tatil_select(event):
            selection = tatil_tree.selection()
            if selection:
                item = tatil_tree.item(selection[0])
                values = item['values']
                selected_tatil_id.set(str(values[0]))
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT gunDegerId, ad, tarih FROM Tatil WHERE id = ?", (values[0],))
                tatil_data = cursor.fetchone()
                conn.close()
                
                if tatil_data:
                    gun_deger_id = tatil_data[0]
                    cursor = self.db.get_connection().cursor()
                    cursor.execute("SELECT ad, deger FROM GunDeger WHERE id = ?", (gun_deger_id,))
                    gun_deger_info = cursor.fetchone()
                    cursor.connection.close()
                    
                    if gun_deger_info:
                        gun_deger_var.set(f"{gun_deger_info[0]} ({gun_deger_info[1]} puan)")
                    
                    tatil_ad_var.set(tatil_data[1])
                    
                    from datetime import datetime
                    try:
                        tarih_obj = datetime.strptime(tatil_data[2], '%Y-%m-%d')
                        tarih_var.set(tarih_obj.strftime('%d.%m.%Y'))
                    except:
                        tarih_var.set(tatil_data[2])
        
        tatil_tree.bind('<<TreeviewSelect>>', on_tatil_select)
        
        def delete_tatil():
            selection = tatil_tree.selection()
            if not selection:
                messagebox.showwarning("Uyarı", "Silinecek tatili seçin!")
                return
            
            try:
                item = tatil_tree.item(selection[0])
                tatil_id = item['values'][0]
                tatil_ad = item['values'][2]
                
                result = messagebox.askyesno("Onay", f"'{tatil_ad}' tatili silinecek. Emin misiniz?")
                if result:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Tatil WHERE id = ?", (tatil_id,))
                    conn.commit()
                    conn.close()
                    
                    clear_tatil_form()
                    refresh_tatil_list()
                    messagebox.showinfo("Başarılı", "Tatil silindi!")
                    
            except Exception as e:
                messagebox.showerror("Hata", f"Tatil silinirken hata oluştu: {str(e)}")
        
        bottom_btn_frame = ttk.Frame(list_frame)
        bottom_btn_frame.pack(pady=(10, 0))
        
        ttk.Button(bottom_btn_frame, text="Yenile", command=refresh_tatil_list).grid(row=0, column=0, padx=5)
        ttk.Button(bottom_btn_frame, text="Sil", command=delete_tatil).grid(row=0, column=1, padx=5)
        
        load_gun_degerleri()
        refresh_tatil_list()
        gun_deger_combo.focus()
    
    def create_date_picker(self, parent, date_var, label_text):
        frame = ttk.Frame(parent)
        if label_text:
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=(0, 5))
        
        date_entry = ttk.Entry(frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        def open_calendar():
            cal_window = tk.Toplevel(parent)
            cal_window.title("Tarih Seç")
            cal_window.geometry("300x250")
            cal_window.transient(parent.winfo_toplevel())
            cal_window.grab_set()
            
            import calendar
            from datetime import datetime, date
            
            current_date = datetime.now()
            try:
                if date_var.get():
                    current_date = datetime.strptime(date_var.get(), '%d.%m.%Y')
            except:
                pass
            
            year_var = tk.IntVar(value=current_date.year)
            month_var = tk.IntVar(value=current_date.month)
            
            top_frame = ttk.Frame(cal_window)
            top_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(top_frame, text="<", width=3, 
                      command=lambda: change_month(-1)).pack(side=tk.LEFT)
            
            month_label = ttk.Label(top_frame, text="", font=('TkDefaultFont', 12, 'bold'))
            month_label.pack(side=tk.LEFT, expand=True)
            
            ttk.Button(top_frame, text=">", width=3,
                      command=lambda: change_month(1)).pack(side=tk.RIGHT)
            
            cal_frame = ttk.Frame(cal_window)
            cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            def change_month(delta):
                new_month = month_var.get() + delta
                new_year = year_var.get()
                
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                elif new_month < 1:
                    new_month = 12
                    new_year -= 1
                
                month_var.set(new_month)
                year_var.set(new_year)
                update_calendar()
            
            def update_calendar():
                for widget in cal_frame.winfo_children():
                    widget.destroy()
                
                month_names = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
                month_label.config(text=f"{month_names[month_var.get()]} {year_var.get()}")
                
                days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
                for i, day in enumerate(days):
                    ttk.Label(cal_frame, text=day, font=('TkDefaultFont', 9, 'bold')).grid(
                        row=0, column=i, padx=1, pady=1)
                
                cal = calendar.monthcalendar(year_var.get(), month_var.get())
                
                for week_num, week in enumerate(cal, 1):
                    for day_num, day in enumerate(week):
                        if day == 0:
                            continue
                        
                        def select_date(d=day):
                            selected_date = date(year_var.get(), month_var.get(), d)
                            date_var.set(selected_date.strftime('%d.%m.%Y'))
                            cal_window.destroy()
                        
                        btn = ttk.Button(cal_frame, text=str(day), width=3,
                                       command=select_date)
                        btn.grid(row=week_num, column=day_num, padx=1, pady=1)
            
            update_calendar()
        
        ttk.Button(frame, text="📅", width=3, command=open_calendar).pack(side=tk.LEFT)
        
        return frame

    def open_info_window(self):
        info_window = tk.Toplevel(self.root)
        info_window.title("Nöbet Programı - Bilgi")
        info_window.geometry("900x700")
        info_window.resizable(True, True)
        info_window.grab_set()
        
        info_window.transient(self.root)
        info_window.update_idletasks()
        x = (info_window.winfo_screenwidth() // 2) - (450)
        y = (info_window.winfo_screenheight() // 2) - (350)
        info_window.geometry(f"900x700+{x}+{y}")
        
        main_frame = tk.Frame(info_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text="Nöbet Programı Yönetim Sistemi", 
                              font=("Arial", 16, "bold"), fg="#2c3e50")
        title_label.pack(pady=(0, 20))
        
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                             font=("Arial", 11), bg="#f8f9fa", relief=tk.FLAT, padx=15, pady=15)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        info_content = """
NÖBET PROGRAMI YÖNETİM SİSTEMİ
MEBS personeli için gelişmiş nöbet programı yönetim sistemi
Max-Min Nöebt değeri kişinin gün/puan değerlerine göre farklılık gösterebilir, 
Ardışık gün nöbeti eski girilen koşullara göre devredışı kaldığı durumlar olabilir,
Hazırlanan Nöbetleri tekrar KONTROL EDİN ❗
🎯 TEMEL ÖZELLİKLER:

📋 Nöbet Programı Oluşturma:
• "Nöbet Hazırla" butonu ile otomatik nöbet dağıtımı
• Adil dağıtım algoritması ile eşit nöbet yükü
• Önizleme ve manuel düzenleme imkanı
• "Kaydet" butonu ile programı veritabanına kaydetme

👥 Personel Yönetimi:
• Personel ekleme, düzenleme ve silme
• Aktif/pasif durum yönetimi
• Statü bilgileri (Rütbe dağılım etkisi yoktur.)

😷 Mazeret Yönetimi:
• Personel mazeret kayıtları
• Zorunlu atama (tut=1) ve hariç tutma (tut=0) seçenekleri
• Takvim ile tarih seçimi
• Çoklu gün mazeret girişi (ek gün sayısı ile ardışık günler)

📊 Eski Nöbetler:
• Geçmiş nöbet kayıtlarını görüntüleme
• Yıl/ay bazında filtreleme
• Aylık nöbet kayıtlarını toplu silme

⚙️ Sistem Ayarları:
• Gün değerleri ve puanlama sistemi
• Tatil günleri yönetimi
• Dini ve resmi tatil tanımlamaları

📈 Excel Raporlama:
• Aylık nöbet programlarını Excel'e aktarma
• 7 sütunlu takvim formatında görüntüleme
• Personel özet raporları

🔧 NÖBET DAĞITIM KURALLARI:

⚖️ Adil Dağıtım:
• Toplam nöbet sayısı ve puan değerleri eşitlenir
• Geçmiş nöbet geçmişi dikkate alınır
• Yeni personel için ortalama değer hesaplanır

🔗 Zorunlu Eşleştirmeler:
• Perşembe-Cumartesi eşleştirmesi: %85-90 başarı oranı
• Cuma-Pazar eşleştirmesi: %85-90 başarı oranı
• Aynı ay içinde farklı haftalarda gerçekleştirilir
• Puan değerleri göz önüne alınarak optimize edilir

🚫 Kısıtlamalar:
• Ardışık günlerde aynı kişiye nöbet verilmez
• Perşembe yazılana aynı ay farklı haftada Cumartesi yazılmaya zorlanır
• Cumartesi yazılana aynı ay farklı haftada Perşembe yazılmaya zorlanır
• Cuma yazılana aynı ay farklı haftada Pazar yazılmaya zorlanır
• Pazar yazılana aynı ay farklı haftada Cuma yazılmaya zorlanır
• Ramazan ve Kurban bayramlarında çapraz atama yapılmaz (aynı yıl kapsamında)
• Geçmişte tatil nöbeti olan personele yeni tatil nöbeti verilemez
• Mazeret tut=1 ile tatil çakışma kuralları geçersiz kılınabilir
• Önceki ayın son günü nöbetçi olan, sonraki ayın ilk günü nöbetçi olmaz

🎯 Öncelik Sistemi:
• Mazeret tut=1 tüm kısıtlamaları geçersiz kılar (tatil çakışmaları dahil)
• Mazeret tut=0 kesinlikle hariç tutar
• Aktif olmayan personele nöbet verilmez

🏥 TATİL ÇAKIŞMA KURALLARI:

Ramazan-Kurban Çapraz Atama:
• Aynı yıl içinde Ramazan nöbeti olan personele Kurban nöbeti verilemez
• Aynı yıl içinde Kurban nöbeti olan personele Ramazan nöbeti verilemez
• Bu kural yıllık kapsamda uygulanır (aylık değil)

Genel Tatil Çakışma Önleme:
• Geçmişte herhangi bir tatil nöbeti olan personele yeni tatil nöbeti verilemez
• Bu kural tüm tatil türleri için geçerlidir (Ramazan, Kurban, Resmi Tatil)
• Mazeret tut=1 ile bu kural geçersiz kılınabilir

📅 GÜN DEĞERLERİ:

Hafta İçi Günler:
• Perşembe: 0.9 (En düşük)
• Salı/Çarşamba: 1.1
• Pazartesi: 1.2
• Cuma: 1.4 (Hafta içi en yüksek)

Hafta Sonu:
• Pazar: 1.6
• Cumartesi: 2.0 (Referans)

Özel Günler:
• Resmi Tatil: 2.2
• Dini Tatil 1,6: 2.4
• Dini Tatil 2,3,5: 2.9
• Dini Tatil 4: 3.0 (En yüksek)

🖥️ KULLANIM KILAVUZU:

⚠ Başlangıç:
• Yıl ve ay seçin
• "Nöbet Hazırla" butonuna tıklayın

⚠ Düzenleme:
• Takvim hücrelerine sağ tıklayarak nöbet değiştirin
• Değişiklikleri önizleyin

⚠ Kaydetme:
• "Kaydet" butonu ile programı kalıcı hale getirin
• "Excel'e Aktar" ile rapor alın

⚠ Yönetim:
• Personel, mazeret ve sistem ayarlarını güncelleyin
• Eski nöbetleri görüntüleyin ve yönetin

💡 İPUÇLARI:
• Mazeret girişlerini nöbet hazırlamadan önce yapın
• Tatil günlerini önceden tanımlayın
• Personel durumlarını güncel tutun
• Düzenli olarak Excel raporları alın

📝 ÇOKLU GÜN MAZERET GİRİŞİ:
• Mazeret ekranında "Ek Gün Sayısı" alanı bulunur (varsayılan: 0)
• Değer 0 ise sadece seçilen tarihe mazeret eklenir
• Değer 0'dan büyükse seçilen tarih + ek gün sayısı kadar ardışık güne mazeret eklenir
• Örnek: Tarih 15.06.2025, Ek Gün Sayısı 3 → 15, 16, 17, 18 Haziran'a mazeret eklenir
• Zaten mevcut olan tarihler atlanır ve rapor edilir
• Tüm eklenen günler aynı tut değerini (0 veya 1) alır

🔄 GÜNCELLEME NOTLARI:
• Ana ekran otomatik yenilenir
• Türkçe ay isimleri kullanılır
• Gelişmiş takvim seçici
• Sağ tık menüleri ile hızlı düzenleme

Bu sistem, MEBS personelinin nöbet programlarını adil, verimli ve kolay bir şekilde yönetmek için tasarlanmıştır. Tüm işlemler kullanıcı dostu arayüz ile gerçekleştirilir.

Mu.Mrk.Ks.
"""
        
        text_widget.insert(tk.END, info_content)
        text_widget.config(state=tk.DISABLED)
        
        close_btn = tk.Button(main_frame, text="Kapat", command=info_window.destroy, 
                             bg="#dc3545", fg="white", font=("Arial", 12, "bold"))
        close_btn.pack(pady=(20, 0))

def main():
    root = tk.Tk()
    app = DutySchedulerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
