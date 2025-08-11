"""
Tests additionnels pour src.data.database: get_db_path et migrations v4
"""

import os
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestDatabaseAdditional:
    @patch.dict(os.environ, {"DATABASE_PATH": "X:/custom.db"}, clear=False)
    def test_get_db_path_env(self):
        from src.data.database import get_db_path

        p = get_db_path()
        assert str(p).endswith("custom.db")

    def test_migration_v4_no_column_then_exists(self):
        from src.data.database import DatabaseSchema

        # DB mémoire avec table campaigns sans colonne ai_model
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("CREATE TABLE campaigns (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        # Exécuter migration v4 -> ajoute colonne
        DatabaseSchema._migration_v4(conn)
        # Re-vérifier, seconde exécution ne doit pas échouer
        DatabaseSchema._migration_v4(conn)
        # Confirmer présence de la colonne
        cols = [r[1] for r in cur.execute("PRAGMA table_info(campaigns)").fetchall()]
        assert "ai_model" in cols
