#!/usr/bin/env python3
"""
Console-based version of the duty scheduling application
Fallback for when GUI is not available
"""

import sys
from datetime import datetime
from database import Database
from scheduler import DutyScheduler
from excel_exporter import ExcelExporter

class ConsoleApp:
    def __init__(self):
        self.db = Database()
        self.scheduler = DutyScheduler(self.db)
        self.exporter = ExcelExporter(self.db)
        
    def show_menu(self):
        print("\n" + "="*50)
        print("    NÖBET PROGRAMI YÖNETİM SİSTEMİ")
        print("="*50)
        print("1. Nöbet Programı Hazırla")
        print("2. Excel'e Aktar")
        print("3. Personel Listesi Görüntüle")
        print("4. Mevcut Nöbet Programını Görüntüle")
        print("5. Çıkış")
        print("-"*50)
        
    def show_personnel(self):
        personnel = self.scheduler.get_active_personnel()
        print("\n📋 AKTİF PERSONEL LİSTESİ:")
        print("-"*40)
        for person in personnel:
            print(f"ID: {person[0]:2d} | {person[1]:15s} | {person[2]}")
        
    def generate_schedule_menu(self):
        print("\n📅 NÖBET PROGRAMI HAZIRLA")
        print("-"*30)
        
        try:
            year = int(input("Yıl girin (örn: 2025): "))
            month = int(input("Ay girin (1-12): "))
            
            if month < 1 or month > 12:
                print("❌ Geçersiz ay! 1-12 arası değer girin.")
                return
                
            print(f"\n⏳ {year}/{month} ayı için nöbet programı hazırlanıyor...")
            schedule = self.scheduler.generate_schedule(year, month)
            
            print(f"\n✅ Nöbet programı hazırlandı! ({len(schedule)} gün)")
            
            print("\n📋 İLK 10 GÜN ÖNİZLEME:")
            print("-"*50)
            for i, (date, person_id, day_type) in enumerate(schedule[:10]):
                person_name = self.scheduler.get_person_name(person_id) if person_id else "ATANMADI"
                print(f"{date} | {person_name:15s} | {day_type}")
            
            if len(schedule) > 10:
                print("...")
                
            save = input("\n💾 Bu programı kaydetmek istiyor musunuz? (e/h): ").lower()
            if save == 'e':
                self.scheduler.save_schedule(schedule, year, month)
                print("✅ Nöbet programı kaydedildi!")
                
        except ValueError:
            print("❌ Geçersiz değer girdiniz!")
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
    
    def export_excel_menu(self):
        print("\n📊 EXCEL'E AKTAR")
        print("-"*20)
        
        try:
            year = int(input("Yıl girin (örn: 2025): "))
            month = int(input("Ay girin (1-12): "))
            
            if month < 1 or month > 12:
                print("❌ Geçersiz ay! 1-12 arası değer girin.")
                return
            
            filename = f"nobet_programi_{year}_{month:02d}.xlsx"
            print(f"\n⏳ Excel dosyası oluşturuluyor: {filename}")
            
            result_file = self.exporter.export_monthly_schedule(year, month, filename)
            print(f"✅ Excel dosyası oluşturuldu: {result_file}")
            
            summary_file = self.exporter.export_personnel_summary(year, month, 
                                                                f"personel_ozet_{year}_{month:02d}.xlsx")
            print(f"✅ Personel özet dosyası oluşturuldu: {summary_file}")
            
        except ValueError:
            print("❌ Geçersiz değer girdiniz!")
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
    
    def show_current_schedule(self):
        print("\n📋 MEVCUT NÖBET PROGRAMI")
        print("-"*30)
        
        try:
            year = int(input("Yıl girin (örn: 2025): "))
            month = int(input("Ay girin (1-12): "))
            
            if month < 1 or month > 12:
                print("❌ Geçersiz ay! 1-12 arası değer girin.")
                return
            
            schedule_data = self.exporter.get_monthly_schedule(year, month)
            
            if not schedule_data:
                print(f"❌ {year}/{month} ayı için kayıtlı nöbet programı bulunamadı.")
                return
            
            print(f"\n📅 {year}/{month} AYI NÖBET PROGRAMI:")
            print("-"*50)
            
            for date, info in sorted(schedule_data.items()):
                print(f"{date} | {info['name']:15s} | {info['status']}")
                
        except ValueError:
            print("❌ Geçersiz değer girdiniz!")
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
    
    def run(self):
        print("🏥 Nöbet Programı Yönetim Sistemi başlatılıyor...")
        
        self.db.populate_sample_data()
        print("✅ Veritabanı hazırlandı.")
        
        while True:
            self.show_menu()
            
            try:
                choice = input("Seçiminizi yapın (1-5): ").strip()
                
                if choice == '1':
                    self.generate_schedule_menu()
                elif choice == '2':
                    self.export_excel_menu()
                elif choice == '3':
                    self.show_personnel()
                elif choice == '4':
                    self.show_current_schedule()
                elif choice == '5':
                    print("\n👋 Güle güle!")
                    sys.exit(0)
                else:
                    print("❌ Geçersiz seçim! 1-5 arası bir değer girin.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Program sonlandırıldı.")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Beklenmeyen hata: {str(e)}")

def main():
    app = ConsoleApp()
    app.run()

if __name__ == "__main__":
    main()
