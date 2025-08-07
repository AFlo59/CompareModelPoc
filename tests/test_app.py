import os
from database import init_db, get_connection

def test_database_init_and_tables():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    expected = {"users", "model_choices", "campaigns", "characters", "messages", "performance_logs"}
    assert expected.issubset(set(tables))
