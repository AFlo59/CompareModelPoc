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

        # Gérer le cas où DB_PATH n'est pas encore défini
        try:
            original_db_path = database.DB_PATH
        except AttributeError:
            original_db_path = database.DatabaseConfig.DB_PATH

        # Patcher les deux pour être sûr
        if hasattr(database, "DB_PATH"):
            database.DB_PATH = Path(test_db_file.name)
        database.DatabaseConfig.DB_PATH = Path(test_db_file.name)

        # Initialiser la DB de test avec le nouveau schéma optimisé
        # Force la recréation pour s'assurer du bon schéma
        database.DatabaseConfig.DB_PATH.parent.mkdir(exist_ok=True)

        with database.get_optimized_connection() as conn:
            # Supprimer toutes les tables existantes pour forcer la recréation
            cursor = conn.cursor()
            tables = ["performance_logs", "messages", "characters", "campaigns", "model_choices", "users", "schema_version"]
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

            # Créer les tables avec le nouveau schéma
            database.DatabaseSchema.create_tables(conn)

            # Exécuter les migrations
            database.DatabaseSchema.run_migrations(conn)

            # Optimiser la base de données
            conn.execute("ANALYZE")
            conn.execute("PRAGMA optimize")

        yield test_db_file.name

    finally:
        # Restaurer le chemin original
        if original_db_path:
            if hasattr(database, "DB_PATH"):
                database.DB_PATH = original_db_path
            database.DatabaseConfig.DB_PATH = original_db_path

        # Nettoyer le fichier temporaire
        try:
            os.unlink(test_db_file.name)
        except:
            pass


@pytest.fixture
def clean_db(test_db):
    """Fixture pour nettoyer la base de données entre les tests."""
    from src.data.database import DatabaseConnection

    # Forcer une nouvelle connexion pour éviter les problèmes de connexion fermée
    DatabaseConnection._connection = None

    # Nettoyer toutes les tables avant le test
    try:
        from src.data.database import get_optimized_connection

        with get_optimized_connection() as conn:
            cursor = conn.cursor()

            # Supprimer toutes les données
            tables = ["performance_logs", "messages", "characters", "campaigns", "model_choices", "users"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")

            conn.commit()
    except Exception as e:
        # En cas d'erreur, ne pas faire échouer le test
        print(f"Warning: Could not clean database before test: {e}")

    yield

    # Nettoyer après le test et fermer la connexion proprement
    try:
        from src.data.database import get_optimized_connection

        with get_optimized_connection() as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()

        # Fermer et réinitialiser la connexion pour le test suivant
        if DatabaseConnection._connection:
            DatabaseConnection._connection.close()
            DatabaseConnection._connection = None
    except Exception as e:
        # En cas d'erreur, ne pas faire échouer le test
        print(f"Warning: Could not clean database after test: {e}")


@pytest.fixture
def sample_user(clean_db):
    """Fixture pour créer un utilisateur de test."""
    import bcrypt

    from src.data.database import DatabaseConnection, get_optimized_connection

    # S'assurer que la DB est bien initialisée avec le bon schéma
    try:
        # Forcer une nouvelle connexion si nécessaire
        if DatabaseConnection._connection is None:
            DatabaseConnection._connection = None

        with get_optimized_connection() as conn:
            cursor = conn.cursor()

            # Vérifier que la table users existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                raise RuntimeError("Table users not found")

            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",))
            existing_user = cursor.fetchone()

            if existing_user:
                user_id = existing_user[0]
            else:
                hashed_password = bcrypt.hashpw("testpassword123".encode("utf-8"), bcrypt.gensalt())
                cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@example.com", hashed_password))
                user_id = cursor.lastrowid
                conn.commit()

        return {"id": user_id, "email": "test@example.com"}
    except Exception as e:
        # Ne pas skip, mais plutôt lever l'erreur pour voir ce qui ne va pas
        print(f"Error creating sample user: {e}")
        # Essayer de réinitialiser la connexion et réessayer
        DatabaseConnection._connection = None
        raise
