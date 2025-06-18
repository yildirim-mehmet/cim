#!/usr/bin/env python3
"""
Nöbet Programı Yönetim Sistemi
Duty Scheduling Management System

Bu program hastane/klinik personeli için nöbet programı oluşturur ve yönetir.
This program creates and manages duty schedules for hospital/clinic personnel.
"""

import sys
import os
from database import Database

def setup_environment():
    """Gerekli ortam ayarlarını yapar"""
    if not os.path.exists("nobet_programi.db"):
        print("Veritabanı oluşturuluyor...")
        db = Database()
        db.populate_sample_data()
        print("Örnek veriler yüklendi.")

def main():
    print("Nöbet Programı Yönetim Sistemi başlatılıyor...")
    setup_environment()
    
    try:
        from gui import main as gui_main
        gui_main()
    except ImportError as e:
        if "_tkinter" in str(e) or "tkinter" in str(e):
            print("⚠️  GUI modu kullanılamıyor (tkinter eksik). Konsol moduna geçiliyor...")
            from console_app import main as console_main
            console_main()
        else:
            raise e

if __name__ == "__main__":
    main()
