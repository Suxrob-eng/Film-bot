import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect("filmbot.db")
    cur = conn.cursor()


    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        full_name VARCHAR,
        username VARCHAR,
        phone_number VARCHAR,
        created_at TEXT                    
        )""")
    

    cur.execute("""CREATE TABLE IF NOT EXISTS movies(
        movie_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_file TEXT,
        movie_desc TEXT,
        movie_code INTEGER UNIQUE,
        created_at TEXT      
            )""")


    conn.commit()
    conn.close()



def add_user(user_id, full_name, username, phone_number):
    conn = sqlite3.connect("filmbot.db")
    cur = conn.cursor()
    created_at = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cur.execute("INSERT INTO users (user_id, full_name, username, phone_number, created_at) VALUES (?,?,?,?,?)", (user_id, full_name, username, phone_number, created_at))
    conn.commit()
    conn.close()



def get_user(user_id):
    conn = sqlite3.connect("filmbot.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id, ))
    user = cur.fetchall()
    conn.commit()
    conn.close()
    return user



def add_movie(movie_file, movie_desc, movie_code):
    conn = sqlite3.connect("filmbot.db")
    cur = conn.cursor()
    created_at = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cur.execute("INSERT INTO movies (movie_file, movie_desc, movie_code, created_at) VALUES (?, ?, ?, ?)", (movie_file, movie_desc, movie_code, created_at))
    conn.commit()
    conn.close()


def get_movie_by_code(movie_code):
    conn = sqlite3.connect("filmbot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT movie_file, movie_desc FROM movies WHERE movie_code = ?",
        (movie_code,)
    )
    movie = cur.fetchone()
    conn.close()
    return movie
