import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import bcrypt
import pytest
import streamlit as st

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.auth.auth import (
    LoginAttemptTracker,
    SecurityConfig,
    SessionManager,
    login_enhanced,
    logout_enhanced,
    register_user_enhanced,
    require_auth_enhanced,
    validate_email,
    validate_email_enhanced,
    validate_password,
    validate_password_enhanced,
)
from src.data.database import get_connection


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
        from src.data.database import get_connection

        # Créer un utilisateur
        email = "test@example.com"
        password = "TestPassword123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
            user_id = cursor.lastrowid
            conn.commit()

        # Vérifier que l'utilisateur existe
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, password FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()

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


class TestSecurityConfig:
    """Tests pour la configuration de sécurité."""

    def test_security_config_constants(self):
        """Test des constantes de configuration."""
        assert SecurityConfig.MAX_LOGIN_ATTEMPTS == 5
        assert SecurityConfig.LOCKOUT_DURATION == 900
        assert SecurityConfig.SESSION_TIMEOUT == 3600
        assert SecurityConfig.MIN_PASSWORD_LENGTH == 8
        assert SecurityConfig.REQUIRE_UPPERCASE is True
        assert SecurityConfig.REQUIRE_LOWERCASE is True
        assert SecurityConfig.REQUIRE_DIGIT is True


class TestLoginAttemptTracker:
    """Tests pour le tracking des tentatives de connexion."""

    def setup_method(self):
        """Setup pour chaque test."""
        # Nettoyer le state avant chaque test
        if hasattr(LoginAttemptTracker, "_failed_attempts"):
            LoginAttemptTracker._failed_attempts.clear()

    @patch("streamlit.session_state", new_callable=dict)
    def test_record_failed_attempt(self, mock_session_state):
        """Test enregistrement tentative échouée."""
        email = "test@example.com"

        # Première tentative
        LoginAttemptTracker.record_failed_attempt(email)

        # Vérifier qu'une clé a été créée dans session_state
        attempt_key = LoginAttemptTracker._get_attempt_key(email)
        assert attempt_key in mock_session_state
        assert mock_session_state[attempt_key]["count"] == 1

        # Deuxième tentative
        LoginAttemptTracker.record_failed_attempt(email)
        assert mock_session_state[attempt_key]["count"] == 2

    @patch("streamlit.session_state", new_callable=dict)
    def test_is_account_locked(self, mock_session_state):
        """Test vérification verrouillage compte."""
        email = "test@example.com"

        # Compte non verrouillé initialement
        is_locked, remaining_time = LoginAttemptTracker.is_locked_out(email)
        assert not is_locked

        # Ajouter le maximum de tentatives
        for i in range(SecurityConfig.MAX_LOGIN_ATTEMPTS):
            LoginAttemptTracker.record_failed_attempt(email)

        # Compte maintenant verrouillé
        is_locked, remaining_time = LoginAttemptTracker.is_locked_out(email)
        assert is_locked
        assert remaining_time is not None
        assert remaining_time > 0

    @patch("streamlit.session_state", new_callable=dict)
    def test_reset_attempts(self, mock_session_state):
        """Test reset des tentatives."""
        email = "test@example.com"

        # Ajouter quelques tentatives
        for i in range(3):
            LoginAttemptTracker.record_failed_attempt(email)

        attempt_key = LoginAttemptTracker._get_attempt_key(email)
        assert mock_session_state[attempt_key]["count"] == 3

        # Reset
        LoginAttemptTracker.reset_attempts(email)
        assert attempt_key not in mock_session_state


class TestSessionManager:
    """Tests pour la gestion de session."""

    def setup_method(self):
        """Setup pour chaque test."""
        # Clear session state before each test
        if hasattr(st, "session_state"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

    @patch("streamlit.session_state", new_callable=dict)
    def test_is_session_valid_no_timestamp(self, mock_session_state):
        """Test session sans timestamp."""
        assert not SessionManager.is_session_valid()

    @patch("streamlit.session_state", new_callable=dict)
    @patch("time.time")
    def test_is_session_valid_expired(self, mock_time, mock_session_state):
        """Test session expirée."""
        # Session créée il y a 2 heures
        past_time = time.time() - 7200
        mock_session_state["last_activity"] = past_time
        mock_time.return_value = time.time()

        assert not SessionManager.is_session_valid()

    @patch("time.time", return_value=1000.0)
    def test_is_session_valid_active(self, mock_time):
        """Test session active."""
        current_time = 1000.0
        recent_time = 400.0  # 600 seconds ago - still valid (SESSION_TIMEOUT = 3600)

        mock_session_state = {"user": {"id": 1, "email": "test@example.com"}, "last_activity": recent_time}

        with patch("streamlit.session_state", mock_session_state):
            assert SessionManager.is_session_valid()

    @patch("time.time")
    def test_update_activity(self, mock_time):
        """Test mise à jour activité."""
        current_time = 1234567890
        mock_time.return_value = current_time

        # Mock session_state comme un objet qui accepte les attributs
        mock_session_state = Mock()

        with patch("streamlit.session_state", mock_session_state):
            SessionManager.update_activity()

            assert mock_session_state.last_activity == current_time

    @patch("time.time", return_value=1000.0)
    def test_get_session_info(self, mock_time):
        """Test récupération informations session."""
        mock_session_state = Mock()
        mock_session_state.__contains__ = Mock(return_value=True)
        mock_session_state.user = {"id": 1, "email": "test@example.com"}
        mock_session_state.get = Mock(return_value=700.0)  # last_activity

        with patch("streamlit.session_state", mock_session_state):
            result = SessionManager.get_session_info()

            assert "user" in result
            assert "last_activity" in result
            assert "remaining_time" in result
            assert "is_valid" in result


class TestEnhancedAuth:
    """Tests pour les fonctions d'authentification améliorées."""

    def test_validate_email_enhanced_valid(self):
        """Test validation email améliorée - emails valides."""
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "Test123@Domain.Com"]  # Test case insensitive

        for email in valid_emails:
            assert validate_email_enhanced(email), f"Email valide rejeté: {email}"

    def test_validate_email_enhanced_invalid(self):
        """Test validation email améliorée - emails invalides."""
        invalid_emails = ["", "not-an-email", "@domain.com", "test@", "test@domain"]

        for email in invalid_emails:
            is_valid, msg = validate_email_enhanced(email)
            assert not is_valid, f"Email invalide accepté: {email}"
            assert msg  # Il devrait y avoir un message d'erreur

    def test_validate_password_enhanced_valid(self):
        """Test validation mot de passe améliorée - valides."""
        valid_passwords = ["Password123", "MySecure1Pass", "Test1234abcd"]

        for password in valid_passwords:
            is_valid, msg = validate_password_enhanced(password)
            assert is_valid, f"Mot de passe valide rejeté: {password} - {msg}"

    def test_validate_password_enhanced_too_short(self):
        """Test validation mot de passe - trop court."""
        is_valid, msg = validate_password_enhanced("Abc1")
        assert not is_valid
        assert "Au moins 8 caractères" in msg  # Majuscule correcte

    def test_validate_password_enhanced_no_uppercase(self):
        """Test validation mot de passe - pas de majuscule."""
        is_valid, msg = validate_password_enhanced("password123")
        assert not is_valid
        assert "majuscule" in msg

    def test_validate_password_enhanced_no_lowercase(self):
        """Test validation mot de passe - pas de minuscule."""
        is_valid, msg = validate_password_enhanced("PASSWORD123")
        assert not is_valid
        assert "minuscule" in msg

    def test_validate_password_enhanced_no_digit(self):
        """Test validation mot de passe - pas de chiffre."""
        is_valid, msg = validate_password_enhanced("PasswordAbc")
        assert not is_valid
        assert "chiffre" in msg

    @patch("streamlit.form")
    @patch("streamlit.text_input")
    @patch("streamlit.form_submit_button")
    @patch("streamlit.success")
    @patch("streamlit.error")
    @patch("src.auth.auth.get_connection")
    def test_register_user_enhanced_success(
        self, mock_get_connection, mock_error, mock_success, mock_submit, mock_text_input, mock_form
    ):
        """Test inscription utilisateur réussie."""
        # Mock du formulaire
        mock_form_obj = Mock()
        mock_form.return_value.__enter__ = Mock(return_value=mock_form_obj)
        mock_form.return_value.__exit__ = Mock(return_value=None)

        # Mock des inputs
        mock_text_input.side_effect = ["test@example.com", "Password123", "Password123"]
        mock_submit.return_value = True

        # Mock de la connexion DB
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Email n'existe pas
        mock_get_connection.return_value = mock_conn
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        register_user_enhanced()

        mock_success.assert_called()

    @patch("streamlit.form")
    @patch("streamlit.text_input")
    @patch("streamlit.form_submit_button")
    @patch("streamlit.error")
    @patch("src.auth.auth.get_connection")
    def test_register_user_enhanced_email_exists(
        self, mock_get_connection, mock_error, mock_submit, mock_text_input, mock_form
    ):
        """Test inscription - email existe déjà."""
        # Mock du formulaire
        mock_form_obj = Mock()
        mock_form.return_value.__enter__ = Mock(return_value=mock_form_obj)
        mock_form.return_value.__exit__ = Mock(return_value=None)

        # Mock des inputs
        mock_text_input.side_effect = ["existing@example.com", "Password123", "Password123"]
        mock_submit.return_value = True

        # Mock de la connexion DB - email existe
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # Email existe
        mock_get_connection.return_value = mock_conn
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        register_user_enhanced()

        mock_error.assert_called_with("❌ Un compte avec cet email existe déjà.")

    def test_require_auth_enhanced_no_user(self):
        """Test authentification requise - pas d'utilisateur."""
        mock_session_state = Mock()
        # Simule qu'il n'y a pas d'utilisateur
        mock_session_state.__contains__ = Mock(return_value=False)

        with patch("streamlit.session_state", mock_session_state):
            result = require_auth_enhanced()
            assert not result
            # Vérifier que la page a été définie sur "auth"
            assert mock_session_state.page == "auth"

    @patch("src.auth.auth.SessionManager.is_session_valid")
    def test_require_auth_enhanced_valid_session(self, mock_is_valid):
        """Test authentification requise - session valide."""
        mock_session_state = Mock()
        mock_session_state.__contains__ = lambda key: key == "user"
        mock_session_state.user = {"id": 1, "email": "test@example.com"}
        mock_is_valid.return_value = True

        with patch("streamlit.session_state", mock_session_state), patch(
            "src.auth.auth.SessionManager.update_activity"
        ) as mock_update:
            result = require_auth_enhanced()

            assert result
            mock_update.assert_called()

    def test_logout_enhanced(self):
        """Test déconnexion améliorée."""

        # Créer un objet qui supporte à la fois les attributs et les clés
        class MockSessionState:
            def __init__(self):
                self._data = {
                    "user": {"id": 1, "email": "test@example.com"},
                    "campaign": {"id": 1},
                    "history": [],
                    "page": "dashboard",
                }
                self.user = self._data["user"]

            def __contains__(self, key):
                return key in self._data

            def __delitem__(self, key):
                if key in self._data:
                    del self._data[key]
                if hasattr(self, key):
                    delattr(self, key)

            def keys(self):
                return self._data.keys()

        mock_session_state = MockSessionState()

        with patch("streamlit.session_state", mock_session_state), patch("streamlit.success") as mock_success, patch(
            "streamlit.rerun"
        ) as mock_rerun:
            logout_enhanced()

            mock_success.assert_called()
            mock_rerun.assert_called()
            # Vérifier que les clés ont été supprimées
            assert "user" not in mock_session_state


if __name__ == "__main__":
    pytest.main([__file__])
