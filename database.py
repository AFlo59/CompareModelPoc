import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Utilisateur
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )"""
        )

        # Choix du modèle
        c.execute(
            """CREATE TABLE IF NOT EXISTS model_choices (
            user_id INTEGER,
            model TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )"""
        )

        # Table user_models pour les nouveaux choix de modèles
        c.execute(
            """CREATE TABLE IF NOT EXISTS user_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            model_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )"""
        )

        # Campagnes
        c.execute(
            """CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            themes TEXT,
            language TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )"""
        )

        # Personnages
        c.execute(
            """CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            class TEXT,
            race TEXT,
            description TEXT,
            portrait_url TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )"""
        )

        # Historique du chat
        c.execute(
            """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )"""
        )

        # Performances des modèles avec campaign_id
        c.execute(
            """CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            model TEXT,
            latency REAL,
            tokens_in INTEGER,
            tokens_out INTEGER,
            campaign_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        )"""
        )

        # Migration : ajouter campaign_id à performance_logs si elle n'existe pas
        try:
            c.execute("ALTER TABLE performance_logs ADD COLUMN campaign_id INTEGER")
            conn.commit()
        except sqlite3.OperationalError:
            # La colonne existe déjà
            pass

        # Migration : ajouter gm_portrait à campaigns si elle n'existe pas
        try:
            c.execute("ALTER TABLE campaigns ADD COLUMN gm_portrait TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # La colonne existe déjà
            pass

        # Migration : ajouter campaign_id à messages si elle n'existe pas
        try:
            c.execute("ALTER TABLE messages ADD COLUMN campaign_id INTEGER")
            c.execute("CREATE INDEX IF NOT EXISTS idx_messages_campaign ON messages(campaign_id)")
            conn.commit()
        except sqlite3.OperationalError:
            # La colonne existe déjà
            pass

        conn.commit()


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
