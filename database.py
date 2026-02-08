import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Tuple

def init_db():
    """Bazani ishga tushirish"""
    print("📂 Database ishga tushirilmoqda...")
    
    db_path = 'movie_bot.db'
    print(f"📍 Database yo'li: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                phone_number TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                description TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Mavjud jadvallar: {tables}")
        
        if ('movies',) in tables:
            cursor.execute("PRAGMA table_info(movies);")
            columns = cursor.fetchall()
            print(f"📋 Movies jadvali ustunlari: {columns}")
        
        conn.commit()
        conn.close()
        print("✅ Database muvaffaqiyatli ishga tushirildi")
        
    except Exception as e:
        print(f"❌ Database ishga tushirishda xato: {e}")
        raise

def add_user(user_id: int, full_name: str, username: str, phone_number: str) -> bool:
    """Foydalanuvchi qo'shish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, full_name, username, phone_number)
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, username, phone_number))
        
        conn.commit()
        conn.close()
        print(f"✅ Foydalanuvchi qo'shildi: {user_id}")
        return True
    except Exception as e:
        print(f"❌ Foydalanuvchi qo'shishda xato: {e}")
        return False

def get_user(user_id: int) -> Optional[Tuple]:
    """Foydalanuvchini olish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return user
    except Exception as e:
        print(f"❌ Foydalanuvchi olishda xato: {e}")
        return None

def add_movie(file_id: str, description: str, code: str) -> bool:
    """Film qo'shish"""
    print(f"🎬 Film qo'shilmoqda: code={code}")
    
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM movies WHERE code = ?', (str(code),))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"⚠️ {code} kodi allaqachon mavjud!")
            conn.close()
            return False
        
        cursor.execute('''
            INSERT INTO movies (file_id, description, code) 
            VALUES (?, ?, ?)
        ''', (file_id, description, str(code)))
        
        conn.commit()
        
        cursor.execute('SELECT COUNT(*) FROM movies WHERE code = ?', (str(code),))
        count = cursor.fetchone()[0]
        print(f"✅ Film saqlandi. {code} kodli filmlar: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Film qo'shishda xato: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_movie_by_code(code: str) -> Optional[Tuple]:
    """Filmni kod orqali olish"""
    try:
        print(f"🔍 Film qidirilmoqda: {code}")
        
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_id, description FROM movies WHERE code = ?', (str(code),))
        movie = cursor.fetchone()
        
        if movie:
            print(f"✅ Film topildi: {code}")
        else:
            print(f"❌ Film topilmadi: {code}")
            cursor.execute('SELECT code FROM movies')
            all_codes = cursor.fetchall()
            print(f"📋 Mavjud kodlar: {all_codes}")
        
        conn.close()
        return movie
    except Exception as e:
        print(f"❌ Film olishda xato: {e}")
        return None

def get_all_movies() -> List[Tuple]:
    """Barcha filmlarni olish"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT code, description FROM movies ORDER BY id DESC')
        movies = cursor.fetchall()
        
        conn.close()
        return movies
    except Exception as e:
        print(f"❌ Barcha filmlarni olishda xato: {e}")
        return []

def get_total_movies_count() -> int:
    """Jami film soni"""
    try:
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM movies')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        print(f"❌ Film sonini olishda xato: {e}")
        return 0

def get_movies_by_page(page: int, limit: int) -> List[Tuple]:
    """Sahifalab film olish"""
    try:
        offset = (page - 1) * limit
        conn = sqlite3.connect('movie_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, description FROM movies 
            ORDER BY id DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        movies = cursor.fetchall()
        conn.close()
        return movies
    except Exception as e:
        print(f"❌ Sahifalab film olishda xato: {e}")
        return []