import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="nobet_programi.db"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file {self.db_path} not found. Please ensure the database file exists.")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database_schema(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Personel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad VARCHAR(100) NOT NULL,
                statu VARCHAR(50) NOT NULL,
                Aktif BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS GunDeger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad VARCHAR(50) NOT NULL,
                deger DECIMAL(3,1) NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tatil (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gunDegerId INTEGER NOT NULL,
                ad VARCHAR(100) NOT NULL,
                tarih DATE NOT NULL,
                FOREIGN KEY (gunDegerId) REFERENCES GunDeger(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Nobet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personelId INTEGER NOT NULL,
                gunDegerId INTEGER NOT NULL,
                ad VARCHAR(100) NOT NULL,
                deger DECIMAL(3,1) NOT NULL,
                tarih DATE NOT NULL,
                kayit DATETIME DEFAULT CURRENT_TIMESTAMP,
                degisiklik BOOLEAN DEFAULT 0,
                esTarih DATE,
                yenTarih DATE,
                FOREIGN KEY (personelId) REFERENCES Personel(id),
                FOREIGN KEY (gunDegerId) REFERENCES GunDeger(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Mazeret (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personelId INTEGER NOT NULL,
                tarih DATE NOT NULL,
                tut BOOLEAN NOT NULL,
                FOREIGN KEY (personelId) REFERENCES Personel(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_and_populate_sample_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Personel")
        personel_count = cursor.fetchone()[0]
        
        if personel_count > 0:
            conn.close()
            return
        
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
        
        cursor.executemany("INSERT INTO Personel (id, ad, statu, Aktif) VALUES (?, ?, ?, ?)", personel_data)
        
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
        
        cursor.executemany("INSERT INTO GunDeger (id, ad, deger) VALUES (?, ?, ?)", gun_deger_data)
        
        tatil_data = [
            (1, 9, 'Ramazan 1', '2025-06-07'),
            (2, 10, 'Ramazan 2', '2025-06-08'),
            (3, 11, 'Ramazan 3', '2025-06-09'),
            (4, 12, 'Ramazan 4', '2025-06-10'),
            (5, 13, 'Ramazan 5', '2025-06-11'),
            (6, 14, 'Ramazan 6', '2025-12'),
            (7, 8, '19 Mayıs', '2025-05-19')
        ]
        
        cursor.executemany("INSERT INTO Tatil (id, gunDegerId, ad, tarih) VALUES (?, ?, ?, ?)", tatil_data)
        
        mazeret_data = [
            (1, 2, '2025-06-08', 0),
            (2, 5, '2025-06-15', 1),
            (3, 1, '2025-06-22', 0),
            (4, 7, '2025-06-23', 1)
        ]
        
        cursor.executemany("INSERT INTO Mazeret (id, personelId, tarih, tut) VALUES (?, ?, ?, ?)", mazeret_data)
        
        conn.commit()
        conn.close()
