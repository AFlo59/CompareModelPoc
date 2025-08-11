"""
Compléments pour get_db_path: alias module vs config vs défaut
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_get_db_path_module_alias_preferred_when_equal():
    import importlib

    import src.data.database as db

    db = importlib.reload(db)
    with patch.object(db, "DB_PATH", Path("mod.db"), create=True), patch.object(db.DatabaseConfig, "DB_PATH", Path("mod.db")):
        p = db.get_db_path()
        assert str(p).endswith("mod.db")


def test_get_db_path_config_preferred_when_different():
    import importlib

    import src.data.database as db

    db = importlib.reload(db)
    with patch.object(db, "DB_PATH", Path("mod.db"), create=True), patch.object(db.DatabaseConfig, "DB_PATH", Path("cfg.db")):
        p = db.get_db_path()
        assert str(p).endswith("cfg.db")


def test_get_db_path_default_when_none():
    import importlib

    import src.data.database as db

    db = importlib.reload(db)
    # Retirer DB_PATH alias et mettre config à None
    if hasattr(db, "DB_PATH"):
        delattr(db, "DB_PATH")
    with patch.object(db.DatabaseConfig, "DB_PATH", None):
        p = db.get_db_path()
        assert str(p).endswith("database.db")
