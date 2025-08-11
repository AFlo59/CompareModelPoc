"""
Tests pour le module de base de données optimisé
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.database import DatabaseConfig, DatabaseConnection, DatabaseSchema, get_optimized_connection, init_optimized_db


class TestDatabaseConfig:
    """Tests pour la configuration de base de données."""

    def test_database_config_attributes(self):
        """Test des attributs de configuration."""
        assert hasattr(DatabaseConfig, "DB_PATH")
        assert hasattr(DatabaseConfig, "PRAGMA_SETTINGS")
        assert hasattr(DatabaseConfig, "SCHEMA_VERSION")

        # Vérifier que PRAGMA_SETTINGS contient les optimisations attendues
        pragma_list = DatabaseConfig.PRAGMA_SETTINGS
        assert any("journal_mode=WAL" in pragma for pragma in pragma_list)
        assert any("synchronous=NORMAL" in pragma for pragma in pragma_list)
        assert any("cache_size" in pragma for pragma in pragma_list)

    def test_schema_version_is_integer(self):
        """Test que la version du schéma est un entier."""
        assert isinstance(DatabaseConfig.SCHEMA_VERSION, int)
        assert DatabaseConfig.SCHEMA_VERSION > 0


class TestDatabaseConnection:
    """Tests pour le gestionnaire de connexion."""

    def setup_method(self):
        """Setup avant chaque test."""
        # Nettoyer les connexions thread-local
        if hasattr(DatabaseConnection._thread_local, "connection"):
            try:
                DatabaseConnection._thread_local.connection.close()
            except:
                pass
            del DatabaseConnection._thread_local.connection

    def test_get_connection_creates_connection(self):
        """Test que get_connection crée une connexion."""
        with patch.object(DatabaseConnection, "_create_optimized_connection") as mock_create:
            mock_conn = Mock()
            mock_create.return_value = mock_conn

            conn = DatabaseConnection.get_connection()
            assert conn == mock_conn
            mock_create.assert_called_once()

    def test_get_connection_reuses_connection(self):
        """Test que get_connection réutilise la connexion existante."""
        with patch.object(DatabaseConnection, "_create_optimized_connection") as mock_create:
            mock_conn = Mock()
            mock_create.return_value = mock_conn

            # Premier appel
            conn1 = DatabaseConnection.get_connection()
            # Deuxième appel
            conn2 = DatabaseConnection.get_connection()

            assert conn1 == conn2
            # _create_optimized_connection ne doit être appelé qu'une fois
            mock_create.assert_called_once()

    @patch("src.data.database.sqlite3.connect")
    def test_create_optimized_connection(self, mock_connect):
        """Test de création d'une connexion optimisée."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        conn = DatabaseConnection._create_optimized_connection()

        # Vérifier que sqlite3.connect a été appelé avec les bons paramètres
        mock_connect.assert_called_once()
        call_args = mock_connect.call_args
        assert "check_same_thread" in call_args.kwargs
        assert call_args.kwargs["check_same_thread"] is False

        # Vérifier que les PRAGMA ont été exécutés
        assert mock_conn.execute.call_count >= len(DatabaseConfig.PRAGMA_SETTINGS)

        # Vérifier que row_factory a été défini
        assert mock_conn.row_factory == sqlite3.Row

    def test_close_all_connections(self):
        """Test de fermeture de toutes les connexions."""
        with patch.object(DatabaseConnection, "_create_optimized_connection") as mock_create:
            mock_conn = Mock()
            mock_create.return_value = mock_conn

            # Créer une connexion
            DatabaseConnection.get_connection()

            # Fermer toutes les connexions
            DatabaseConnection.close_all_connections()

            # Vérifier que close a été appelé
            mock_conn.close.assert_called_once()


class TestDatabaseSchema:
    """Tests pour le gestionnaire de schéma."""

    def create_test_connection(self):
        """Crée une connexion de test en mémoire."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        return conn

    def test_get_schema_version_no_table(self):
        """Test de récupération de version quand la table n'existe pas."""
        conn = self.create_test_connection()
        version = DatabaseSchema.get_schema_version(conn)
        assert version == 0

    def test_set_and_get_schema_version(self):
        """Test de définition et récupération de version."""
        conn = self.create_test_connection()

        # Définir la version
        DatabaseSchema.set_schema_version(conn, 3)

        # Récupérer la version
        version = DatabaseSchema.get_schema_version(conn)
        assert version == 3

    def test_create_tables(self):
        """Test de création des tables."""
        conn = self.create_test_connection()

        # Créer les tables
        DatabaseSchema.create_tables(conn)

        # Vérifier que les tables principales existent
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ["users", "model_choices", "campaigns", "characters", "messages", "performance_logs"]
        for table in expected_tables:
            assert table in tables

    def test_create_indexes(self):
        """Test de création des index."""
        conn = self.create_test_connection()

        # Créer les tables (qui inclut les index)
        DatabaseSchema.create_tables(conn)

        # Vérifier que des index existent
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = [row[0] for row in cursor.fetchall()]

        # Vérifier quelques index critiques
        assert any("idx_users_email" in idx for idx in indexes)
        assert any("idx_messages_campaign" in idx for idx in indexes)
        assert any("idx_performance_user" in idx for idx in indexes)

    def test_run_migrations_new_database(self):
        """Test des migrations sur une nouvelle base de données."""
        conn = self.create_test_connection()

        # Les migrations doivent fonctionner sur une base vide
        DatabaseSchema.run_migrations(conn)

        # Vérifier que la version finale est définie
        version = DatabaseSchema.get_schema_version(conn)
        assert version == DatabaseConfig.SCHEMA_VERSION

    def test_migration_v1(self):
        """Test de la migration version 1."""
        conn = self.create_test_connection()

        # Créer une structure de base simple
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE campaigns (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT)")

        # Exécuter la migration v1
        DatabaseSchema._migration_v1(conn)

        # Les migrations doivent fonctionner même si les colonnes existent déjà
        # Pas d'erreur attendue

    def test_migration_v2(self):
        """Test de la migration version 2."""
        conn = self.create_test_connection()

        # Créer des tables de base
        DatabaseSchema.create_tables(conn)

        # Exécuter la migration v2
        DatabaseSchema._migration_v2(conn)

        # Vérifier que les nouveaux index existent
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = [row[0] for row in cursor.fetchall()]

        # Au moins quelques index doivent exister
        assert len(indexes) > 0

    def test_migration_v3(self):
        """Test de la migration version 3."""
        conn = self.create_test_connection()

        # Créer des tables de base
        DatabaseSchema.create_tables(conn)

        # Exécuter la migration v3
        DatabaseSchema._migration_v3(conn)

        # Les nouvelles colonnes doivent être ajoutées sans erreur
        # Vérifier la structure d'une table
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        # Les colonnes de base doivent exister
        assert "id" in columns
        assert "email" in columns


class TestContextManager:
    """Tests pour le context manager optimisé."""

    @patch("src.data.database.DatabaseConnection.get_connection")
    def test_get_optimized_connection_success(self, mock_get_conn):
        """Test du context manager en cas de succès."""
        mock_conn = Mock()
        mock_get_conn.return_value = mock_conn

        with get_optimized_connection() as conn:
            assert conn == mock_conn
            # Simuler une opération
            conn.execute("SELECT 1")

        # Vérifier que BEGIN et COMMIT ont été appelés
        mock_conn.execute.assert_any_call("BEGIN")
        mock_conn.commit.assert_called_once()

    @patch("src.data.database.DatabaseConnection.get_connection")
    def test_get_optimized_connection_exception(self, mock_get_conn):
        """Test du context manager en cas d'exception."""
        mock_conn = Mock()
        mock_get_conn.return_value = mock_conn

        with pytest.raises(ValueError):
            with get_optimized_connection() as conn:
                # Simuler une erreur
                raise ValueError("Test error")

        # Vérifier que rollback a été appelé
        mock_conn.rollback.assert_called_once()
        # Commit ne doit pas être appelé
        mock_conn.commit.assert_not_called()


class TestInitOptimizedDb:
    """Tests pour l'initialisation de la base de données."""

    @patch("src.data.database.get_optimized_connection")
    @patch("src.data.database.DatabaseSchema.create_tables")
    @patch("src.data.database.DatabaseSchema.run_migrations")
    def test_init_optimized_db(self, mock_migrations, mock_create_tables, mock_get_conn):
        """Test d'initialisation de la base de données optimisée."""
        mock_conn = Mock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        init_optimized_db()

        # Vérifier que les fonctions ont été appelées
        mock_create_tables.assert_called_once_with(mock_conn)
        mock_migrations.assert_called_once_with(mock_conn)

        # Vérifier que ANALYZE et PRAGMA optimize ont été exécutés
        mock_conn.execute.assert_any_call("ANALYZE")
        mock_conn.execute.assert_any_call("PRAGMA optimize")

    @patch("src.data.database.DatabaseConfig")
    @patch("src.data.database.get_optimized_connection")
    def test_init_optimized_db_creates_directory(self, mock_get_conn, mock_config):
        """Test que l'initialisation crée le répertoire si nécessaire."""
        # Créer un répertoire temporaire pour le test
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = Path(temp_dir) / "subdir" / "test.db"
            mock_config.DB_PATH = test_db_path

            # Le répertoire parent n'existe pas encore
            assert not test_db_path.parent.exists()

            mock_conn = Mock()
            # Configurer le cursor pour que fetchone() retourne une valeur valide
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = None  # Pas de version existante
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            # Configurer DatabaseConfig.SCHEMA_VERSION pour être un entier
            mock_config.SCHEMA_VERSION = 4

            init_optimized_db()

            # Le répertoire parent doit maintenant exister
            assert test_db_path.parent.exists()


if __name__ == "__main__":
    pytest.main([__file__])
