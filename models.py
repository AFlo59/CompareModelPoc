import sqlite3
import json
from database import get_connection

def save_model_choice(user_id, model):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM model_choices WHERE user_id = ?", (user_id,))
    c.execute("INSERT INTO model_choices (user_id, model) VALUES (?, ?)", (user_id, model))
    conn.commit()
    conn.close()

def create_campaign(user_id, name, themes, language):
    themes_str = json.dumps(themes)
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO campaigns (user_id, name, themes, language)
                 VALUES (?, ?, ?, ?)''', (user_id, name, themes_str, language))
    conn.commit()
    conn.close()

def create_character(user_id, name, classe, race, description, portrait_url):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO characters (user_id, name, class, race, description, portrait_url)
                 VALUES (?, ?, ?, ?, ?, ?)''', (user_id, name, classe, race, description, portrait_url))
    conn.commit()
    conn.close()

def get_user_campaigns(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, themes, language FROM campaigns WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "themes": json.loads(r[2]), "language": r[3]} for r in rows]
