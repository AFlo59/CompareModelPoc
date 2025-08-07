import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Utilisateur
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')

        # Choix du modèle
        c.execute('''CREATE TABLE IF NOT EXISTS model_choices (
            user_id INTEGER,
            model TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        # Campagnes
        c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            themes TEXT,
            language TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        # Personnages
        c.execute('''CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            class TEXT,
            race TEXT,
            description TEXT,
            portrait_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        # Historique du chat
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        # Performances des modèles
        c.execute('''CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            model TEXT,
            latency REAL,
            tokens_in INTEGER,
            tokens_out INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        conn.commit()

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
