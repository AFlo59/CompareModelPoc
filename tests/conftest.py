"""
Configuration globale pour les tests pytest.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session")
def test_db():
    """Fixture pour créer une base de données temporaire pour les tests."""
    # Créer un fichier temporaire pour la DB de test
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    test_db_file.close()

    # Patcher le chemin de la DB avant d'importer les modules
    original_db_path = None
    try:
        from src.data import database

        original_db_path = database.DB_PATH
        database.DB_PATH = Path(test_db_file.name)

        # Initialiser la DB de test
        database.init_db()

        yield test_db_file.name

    finally:
        # Restaurer le chemin original
        if original_db_path:
            database.DB_PATH = original_db_path

        # Nettoyer le fichier temporaire
        try:
            os.unlink(test_db_file.name)
        except:
            pass


@pytest.fixture
def clean_db(test_db):
    """Fixture pour nettoyer la base de données entre les tests."""
    from src.data.database import get_connection

    # Nettoyer toutes les tables avant le test
    with get_connection() as conn:
        cursor = conn.cursor()

        # Supprimer toutes les données
        tables = ["performance_logs", "messages", "characters", "campaigns", "model_choices", "users"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")

        conn.commit()

    yield

    # Optionnel: nettoyer après le test aussi
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        conn.commit()


@pytest.fixture
def sample_user(clean_db):
    """Fixture pour créer un utilisateur de test."""
    import bcrypt

    from src.data.database import get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        hashed_password = bcrypt.hashpw("testpassword123".encode("utf-8"), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@example.com", hashed_password))
        user_id = cursor.lastrowid
        conn.commit()

    return {"id": user_id, "email": "test@example.com"}
