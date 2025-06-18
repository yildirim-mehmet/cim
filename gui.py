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
        schedule_frame.rowconfigure(0, weight=1)
        
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=('Tarih', 'Personel', 'Gün Türü', 'Puan'), show='headings')
        self.schedule_tree.heading('Tarih', text='Tarih')
        self.schedule_tree.heading('Personel', text='Personel')
        self.schedule_tree.heading('Gün Türü', text='Gün Türü')
        self.schedule_tree.heading('Puan', text='Puan')
        
        self.schedule_tree.column('Tarih', width=100)
        self.schedule_tree.column('Personel', width=120)
        self.schedule_tree.column('Gün Türü', width=120)
        self.schedule_tree.column('Puan', width=80)
        
        schedule_scroll = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=schedule_scroll.set)
        
        self.schedule_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        schedule_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
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
    
    def load_initial_data(self):
        self.db.populate_sample_data()
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
        except ValueError:
            pass
    
    def load_existing_schedule(self):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
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
        
        for row in schedule_data:
            self.schedule_tree.insert('', 'end', values=row)
    
    def generate_schedule(self):
        try:
            self.current_schedule = self.scheduler.generate_schedule(self.selected_year, self.selected_month)
            
            for item in self.schedule_tree.get_children():
                self.schedule_tree.delete(item)
            
            day_values = self.scheduler.get_day_values()
            day_value_lookup = {v['name']: v['value'] for v in day_values.values()}
            
            for scheduled_date, person_id, day_type in self.current_schedule:
                if person_id:
                    person_name = self.scheduler.get_person_name(person_id)
                    day_value = day_value_lookup.get(day_type, 0)
                    self.schedule_tree.insert('', 'end', values=(
                        scheduled_date.strftime('%Y-%m-%d'),
                        person_name,
                        day_type,
                        f"{day_value:.1f}"
                    ))
                else:
                    self.schedule_tree.insert('', 'end', values=(
                        scheduled_date.strftime('%Y-%m-%d'),
                        "ATANMADI",
                        day_type,
                        "0.0"
                    ))
            
            messagebox.showinfo("Başarılı", f"{self.selected_year}/{self.selected_month} ayı için nöbet programı hazırlandı!")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Nöbet programı hazırlanırken hata oluştu: {str(e)}")
    
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
                initialname=f"nobet_programi_{self.selected_year}_{self.selected_month:02d}.xlsx"
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

def main():
    root = tk.Tk()
    app = DutySchedulerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
