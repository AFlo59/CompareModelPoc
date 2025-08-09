import os
import sys

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.database import get_connection, init_db


def test_database_init_and_tables(test_db):
    """Test d'initialisation et de vérification des tables de la base de données."""
    with get_connection() as conn:
        cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    expected = {"users", "model_choices", "campaigns", "characters", "messages", "performance_logs"}
    assert expected.issubset(set(tables)), f"Tables manquantes: {expected - set(tables)}"


def test_database_connection(test_db):
    """Test de connexion à la base de données."""
    with get_connection() as conn:
        assert conn is not None

        # Test d'une requête simple
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 1


def test_users_table_structure(test_db):
    """Test de la structure de la table users."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Vérifier la structure de la table users
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()

    column_names = [col[1] for col in columns]
    expected_columns = ["id", "email", "password"]

    for col in expected_columns:
        assert col in column_names, f"Colonne manquante: {col}"


def test_campaigns_table_structure(test_db):
    """Test de la structure de la table campaigns."""
    with get_connection() as conn:
        cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(campaigns)")
    columns = cursor.fetchall()

    column_names = [col[1] for col in columns]
    expected_columns = ["id", "user_id", "name", "themes", "language"]

    for col in expected_columns:
        assert col in column_names, f"Colonne manquante: {col}"


def test_characters_table_structure(test_db):
    """Test de la structure de la table characters."""
    with get_connection() as conn:
        cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(characters)")
    columns = cursor.fetchall()

    column_names = [col[1] for col in columns]
    expected_columns = ["id", "user_id", "name", "class", "race", "description", "portrait_url"]

    for col in expected_columns:
        assert col in column_names, f"Colonne manquante: {col}"
