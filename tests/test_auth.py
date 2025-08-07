import os
import sys
from unittest.mock import MagicMock, patch

import bcrypt
import pytest

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth import validate_email, validate_password
from database import get_connection


class TestAuthentication:
    """Tests pour l'authentification."""

    def test_validate_email_valid(self):
        """Test de validation d'emails valides."""
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "test123@test-domain.org", "a@b.co"]

        for email in valid_emails:
            assert validate_email(email), f"Email valide rejeté: {email}"

    def test_validate_email_invalid(self):
        """Test de validation d'emails invalides."""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "test@",
            "test.domain.com",
            "",
            "test@domain",
            "test..test@domain.com",
        ]

        for email in invalid_emails:
            assert not validate_email(email), f"Email invalide accepté: {email}"

    def test_validate_password_valid(self):
        """Test de validation de mots de passe valides."""
        valid_passwords = ["Password123", "MySecure1Pass", "Test1234", "AbC123def"]

        for password in valid_passwords:
            is_valid, msg = validate_password(password)
            assert is_valid, f"Mot de passe valide rejeté: {password} - {msg}"

    def test_validate_password_invalid(self):
        """Test de validation de mots de passe invalides."""
        invalid_cases = [
            ("short", "moins de 8 caractères"),
            ("nouppercase123", "pas de majuscule"),
            ("NOLOWERCASE123", "pas de minuscule"),
            ("NoNumbers", "pas de chiffre"),
            ("", "vide"),
        ]

        for password, reason in invalid_cases:
            is_valid, msg = validate_password(password)
            assert not is_valid, f"Mot de passe invalide accepté: {password} ({reason})"

    def test_user_creation_and_auth(self, clean_db):
        """Test de création d'utilisateur et d'authentification."""
        from database import get_connection

        # Créer un utilisateur
        email = "test@example.com"
        password = "TestPassword123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Vérifier que l'utilisateur existe
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == user_id
        assert result[1] == email
        assert bcrypt.checkpw(password.encode("utf-8"), result[2])

    def test_password_hashing(self):
        """Test du hachage des mots de passe."""
        password = "TestPassword123"

        # Générer deux hashes du même mot de passe
        hash1 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        hash2 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Les hashes doivent être différents
        assert hash1 != hash2

        # Mais la vérification doit fonctionner pour les deux
        assert bcrypt.checkpw(password.encode("utf-8"), hash1)
        assert bcrypt.checkpw(password.encode("utf-8"), hash2)

        # Un mauvais mot de passe ne doit pas marcher
        assert not bcrypt.checkpw("wrongpassword".encode("utf-8"), hash1)


if __name__ == "__main__":
    pytest.main([__file__])
