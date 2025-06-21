#!/usr/bin/env python3

import sqlite3
from datetime import date

def populate_test_data():
    """Populate database with test data from the original requirements"""
    
    conn = sqlite3.connect('nobet_programi.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM Nobet")
    cursor.execute("DELETE FROM Mazeret") 
    cursor.execute("DELETE FROM Tatil")
    cursor.execute("DELETE FROM Personel")
    cursor.execute("DELETE FROM GunDeger")
    
    gun_deger_data = [
        (1, 'Pazartesi', 1.2),
        (2, 'Salı', 1.1),
        (3, 'Çarşamba', 1.1),
        (4, 'Perşembe', 0.9),
        (5, 'Cuma', 1.4),
        (6, 'Cumartesi', 2.0),
        (7, 'Pazar', 1.6),
        (8, 'Resmi Tatil', 2.2),
        (9, 'Dini Tatil 1', 2.4),
        (10, 'Dini Tatil 2', 2.9),
        (11, 'Dini Tatil 3', 2.9),
        (12, 'Dini Tatil 4', 3.0),
        (13, 'Dini Tatil 5', 2.9),
        (14, 'Dini Tatil 6', 2.4)
    ]
    
    for gd in gun_deger_data:
        cursor.execute("INSERT OR REPLACE INTO GunDeger (id, ad, deger) VALUES (?, ?, ?)", gd)
    
    personel_data = [
        (1, 'Ayşe', 'Doktor', 1),
        (2, 'Mehmet', 'Hemşire', 1),
        (3, 'Selin', 'Uzman', 1),
        (4, 'Onur', 'Teknisyen', 1),
        (5, 'Zeynep', 'Doktor', 0),
        (6, 'Arda', 'Hemşire', 1),
        (7, 'Eda', 'Uzman', 1),
        (8, 'Cem', 'Doktor', 1),
        (9, 'Elif', 'Teknisyen', 1)
    ]
    
    for p in personel_data:
        cursor.execute("INSERT OR REPLACE INTO Personel (id, ad, statu, Aktif) VALUES (?, ?, ?, ?)", p)
    
    tatil_data = [
        (1, 9, 'Ramazan 1', '2025-06-07'),
        (2, 10, 'Ramazan 2', '2025-06-08'),
        (3, 11, 'Ramazan 3', '2025-06-09'),
        (4, 12, 'Ramazan 4', '2025-06-10'),
        (5, 13, 'Ramazan 5', '2025-06-11'),
        (6, 14, 'Ramazan 6', '2025-06-12'),
        (7, 8, '19 Mayıs', '2025-06-19')
    ]
    
    for t in tatil_data:
        cursor.execute("INSERT OR REPLACE INTO Tatil (id, gunDegerId, ad, tarih) VALUES (?, ?, ?, ?)", t)
    
    mazeret_data = [
        (1, 2, '2025-06-08', 0),
        (2, 5, '2025-06-15', 1),
        (3, 1, '2025-06-22', 0),
        (4, 7, '2025-06-23', 1)
    ]
    
    for m in mazeret_data:
        cursor.execute("INSERT OR REPLACE INTO Mazeret (id, personelId, tarih, tut) VALUES (?, ?, ?, ?)", m)
    
    conn.commit()
    conn.close()
    
    print("✅ Test data populated successfully!")
    print("Personnel: 9 total (8 active)")
    print("Day values: 14 entries")
    print("Holidays: 7 entries")
    print("Exemptions: 4 entries")

if __name__ == "__main__":
    populate_test_data()
