import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import calendar
from database import Database
from scheduler import DutyScheduler
from excel_exporter import ExcelExporter

class DutySchedulerGUI:
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
        month_combo['values'] = [f"{i} - {calendar.month_name[i]}" for i in range(1, 13)]
        month_combo.grid(row=0, column=3, padx=(0, 20))
        month_combo.bind('<<ComboboxSelected>>', self.on_date_change)
        
        ttk.Button(control_frame, text="Nöbet Hazırla", command=self.generate_schedule).grid(row=0, column=4, padx=(0, 10))
        ttk.Button(control_frame, text="Excel'e Aktar", command=self.export_to_excel).grid(row=0, column=5, padx=(0, 10))
        ttk.Button(control_frame, text="Kaydet", command=self.save_schedule).grid(row=0, column=6, padx=(0, 10))
        ttk.Button(control_frame, text="Personel Ekle", command=self.open_personnel_window).grid(row=0, column=7, padx=(0, 10))
        ttk.Button(control_frame, text="Mazeret Girişi", command=self.open_mazeret_window).grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
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
    
    def get_day_color(self, date_obj, day_type):
        weekday = date_obj.weekday()
        
        if 'Tatil' in day_type or 'Resmi Tatil' in day_type:
            return '#FFE4B5'
        elif weekday in [5, 6]:
            return '#E6F3FF'
        else:
            return '#F8F8F8'
    
    def create_day_cell(self, parent, row, col, day_num, person_name, day_type, date_obj):
        cell_color = self.get_day_color(date_obj, day_type)
        
        cell_frame = tk.Frame(parent, bg=cell_color, relief='solid', bd=1, width=100, height=80)
        cell_frame.grid(row=row, column=col, padx=1, pady=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        cell_frame.grid_propagate(False)
        
        day_label = tk.Label(cell_frame, text=str(day_num), font=('Arial', 12, 'bold'), 
                           bg=cell_color, fg='black')
        day_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        if person_name and person_name != "ATANMADI":
            person_label = tk.Label(cell_frame, text=person_name, font=('Arial', 9), 
                                  bg=cell_color, fg='darkblue', wraplength=90)
            person_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        if 'Tatil' in day_type or day_type not in ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']:
            type_label = tk.Label(cell_frame, text=day_type, font=('Arial', 8), 
                                bg=cell_color, fg='darkred', wraplength=90)
            type_label.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
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
                    
                    messagebox.showinfo("Başarılı", f"Nöbet değiştirildi!\n{current_person} → {new_personel_name}")
                    
                    self.load_existing_schedule()
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
                        
                        messagebox.showinfo("Başarılı", f"Nöbet değiştirildi!\n{current_person} → {new_personel_name}\n(Değişiklikleri kaydetmeyi unutmayın!)")
                        change_window.destroy()
                    else:
                        messagebox.showerror("Hata", "Önce nöbet programını hazırlayın!")
                
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
            self.current_schedule = self.scheduler.generate_schedule(self.selected_year, self.selected_month)
            
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
            messagebox.showinfo("Başarılı", f"{self.selected_year}/{self.selected_month} ayı için nöbet programı hazırlandı!")
            
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
    
    def save_schedule(self):
        if not self.current_schedule:
            messagebox.showwarning("Uyarı", "Önce nöbet programını hazırlayın!")
            return
        
        try:
            self.scheduler.save_schedule(self.current_schedule, self.selected_year, self.selected_month)
            self.update_stats()
            messagebox.showinfo("Başarılı", "Nöbet programı kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme sırasında hata oluştu: {str(e)}")
    
    def export_to_excel(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"nobet_programi_{self.selected_year}_{self.selected_month:02d}.xlsx"
            )
            
            if filename:
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
        status_combo['values'] = ('Doktor', 'Hemşire', 'Uzman', 'Teknisyen', 'Diğer')
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
            
            cell = self.create_day_cell(self.calendar_frame, current_row, current_col, 
                                      day, person_name, day_type, date_obj)
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
        tarih_entry = ttk.Entry(form_frame, textvariable=tarih_var, width=30)
        tarih_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        tarih_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        tut_var = tk.BooleanVar(value=False)
        tut_check = ttk.Checkbutton(form_frame, text="Tutulacak (Bu tarihe nöbet yazılsın)", variable=tut_var)
        tut_check.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        form_frame.columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        def add_mazeret():
            personel_text = personel_var.get().strip()
            tarih = tarih_var.get().strip()
            tut = 1 if tut_var.get() else 0
            
            if not personel_text or not tarih:
                messagebox.showerror("Hata", "Personel ve Tarih alanları zorunludur!")
                return
            
            try:
                personel_id = int(personel_text.split(' - ')[0])
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM Mazeret WHERE personelId = ? AND tarih = ?", 
                             (personel_id, tarih))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Hata", "Bu personel için bu tarihte zaten mazeret kaydı var!")
                    conn.close()
                    return
                
                cursor.execute("INSERT INTO Mazeret (personelId, tarih, tut) VALUES (?, ?, ?)", 
                             (personel_id, tarih, tut))
                conn.commit()
                conn.close()
                
                tut_text = "tutulacak" if tut else "tutulmayacak"
                messagebox.showinfo("Başarılı", f"Mazeret kaydı eklendi! ({tut_text})")
                
                personel_var.set('')
                tarih_var.set(datetime.now().strftime('%Y-%m-%d'))
                tut_var.set(False)
                
                refresh_mazeret_list()
                
            except Exception as e:
                messagebox.showerror("Hata", f"Mazeret eklenirken hata oluştu: {str(e)}")
        
        def clear_form():
            personel_var.set('')
            tarih_var.set(datetime.now().strftime('%Y-%m-%d'))
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
                    durum_text = "Tutulacak" if mazeret[3] else "Tutulmayacak"
                    mazeret_tree.insert('', tk.END, values=(mazeret[0], mazeret[1], mazeret[2], durum_text))
                    
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

def main():
    root = tk.Tk()
    app = DutySchedulerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
