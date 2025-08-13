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
    # Patch la variable d'environnement pour qu'elle n'interfère pas
    with patch.dict(os.environ, {}, clear=False), patch.object(db, "DB_PATH", Path("mod.db"), create=True), patch.object(
        db.DatabaseConfig, "DB_PATH", Path("mod.db")
    ):
        # S'assurer que DATABASE_PATH n'est pas définie
        if "DATABASE_PATH" in os.environ:
            del os.environ["DATABASE_PATH"]
        p = db.get_db_path()
        assert str(p).endswith("mod.db")


def test_get_db_path_config_preferred_when_different():
    import importlib

    import src.data.database as db

    db = importlib.reload(db)
    # Patch la variable d'environnement pour qu'elle n'interfère pas
    with patch.dict(os.environ, {}, clear=False), patch.object(db, "DB_PATH", Path("mod.db"), create=True), patch.object(
        db.DatabaseConfig, "DB_PATH", Path("cfg.db")
    ):
        # S'assurer que DATABASE_PATH n'est pas définie
        if "DATABASE_PATH" in os.environ:
            del os.environ["DATABASE_PATH"]
        p = db.get_db_path()
        assert str(p).endswith("cfg.db")


def test_get_db_path_default_when_none():
    import importlib

    import src.data.database as db

    db = importlib.reload(db)
    # Patch la variable d'environnement pour qu'elle n'interfère pas
    with patch.dict(os.environ, {}, clear=False), patch.object(db.DatabaseConfig, "DB_PATH", None):
        # S'assurer que DATABASE_PATH n'est pas définie
        if "DATABASE_PATH" in os.environ:
            del os.environ["DATABASE_PATH"]
        # Retirer DB_PATH alias
        if hasattr(db, "DB_PATH"):
            delattr(db, "DB_PATH")
        p = db.get_db_path()
        assert str(p).endswith("database.db")
