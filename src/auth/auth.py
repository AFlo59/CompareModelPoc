"""
Module d'authentification optimisé avec sécurité renforcée
"""

import hashlib
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps

import bcrypt
import streamlit as st

from src.data.database import get_connection

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Configuration de sécurité centralisée."""

    # Tentatives de connexion
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes

    # Session
    SESSION_TIMEOUT = 3600  # 1 heure

    # Mot de passe
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False


class LoginAttemptTracker:
    """Suivi des tentatives de connexion pour prévenir les attaques par force brute."""

    @staticmethod
    def _get_client_id() -> str:
        """Génère un identifiant unique pour le client."""
        # Dans un environnement Streamlit, nous utilisons l'ID de session
        if hasattr(st, "session_state") and hasattr(st.session_state, "_session_id"):
            return str(st.session_state._session_id)
        return "anonymous"

    @staticmethod
    def _get_attempt_key(email: str) -> str:
        """Clé unique pour traquer les tentatives par email."""
        return f"login_attempts_{hashlib.md5(email.lower().encode()).hexdigest()}"

    @classmethod
    def is_locked_out(cls, email: str) -> Tuple[bool, Optional[int]]:
        """Vérifie si l'email est temporairement bloqué."""
        key = cls._get_attempt_key(email)

        if key not in st.session_state:
            return False, None

        attempt_data = st.session_state[key]
        attempts = attempt_data.get("count", 0)
        last_attempt = attempt_data.get("last_attempt", 0)

        if attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            time_since_last = time.time() - last_attempt
            if time_since_last < SecurityConfig.LOCKOUT_DURATION:
                remaining_time = int(SecurityConfig.LOCKOUT_DURATION - time_since_last)
                return True, remaining_time
            else:
                # Reset si le délai est écoulé
                del st.session_state[key]
                return False, None

        return False, None

    @classmethod
    def record_failed_attempt(cls, email: str) -> None:
        """Enregistre une tentative de connexion échouée."""
        key = cls._get_attempt_key(email)

        if key not in st.session_state:
            st.session_state[key] = {"count": 0, "last_attempt": 0}

        st.session_state[key]["count"] += 1
        st.session_state[key]["last_attempt"] = time.time()

        logger.warning(f"Tentative de connexion échouée #{st.session_state[key]['count']} pour {email}")

    @classmethod
    def reset_attempts(cls, email: str) -> None:
        """Remet à zéro les tentatives pour un email."""
        key = cls._get_attempt_key(email)
        if key in st.session_state:
            del st.session_state[key]


class SessionManager:
    """Gestionnaire de session avec timeout automatique."""

    @staticmethod
    def is_session_valid() -> bool:
        """Vérifie si la session actuelle est encore valide."""
        if "user" not in st.session_state:
            return False

        last_activity = st.session_state.get("last_activity")
        if not last_activity:
            return False

        time_since_activity = time.time() - last_activity
        return time_since_activity < SecurityConfig.SESSION_TIMEOUT

    @staticmethod
    def update_activity() -> None:
        """Met à jour le timestamp de dernière activité."""
        st.session_state.last_activity = time.time()

    @staticmethod
    def get_session_info() -> Dict:
        """Retourne les informations de session."""
        if "user" not in st.session_state:
            return {}

        last_activity = st.session_state.get("last_activity", time.time())
        time_since_activity = time.time() - last_activity
        remaining_time = max(0, SecurityConfig.SESSION_TIMEOUT - time_since_activity)

        return {
            "user": st.session_state.user,
            "last_activity": datetime.fromtimestamp(last_activity),
            "remaining_time": remaining_time,
            "is_valid": remaining_time > 0,
        }


def validate_email_enhanced(email: str) -> Tuple[bool, str]:
    """Validation d'email avec messages d'erreur détaillés."""
    if not email or not email.strip():
        return False, "L'email ne peut pas être vide"

    email = email.strip().lower()

    # Vérifications de base
    if len(email) > 254:
        return False, "L'email est trop long (max 254 caractères)"

    if ".." in email or email.startswith(".") or email.endswith("."):
        return False, "Format d'email invalide (points consécutifs)"

    # Pattern strict
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        return False, "Format d'email invalide"

    return True, "Email valide"


def validate_password_enhanced(password: str) -> Tuple[bool, str]:
    """Validation de mot de passe avec critères de sécurité stricts."""
    if not password:
        return False, "Le mot de passe ne peut pas être vide"

    errors = []

    if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
        errors.append(f"Au moins {SecurityConfig.MIN_PASSWORD_LENGTH} caractères")

    if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        errors.append("Au moins une majuscule")

    if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        errors.append("Au moins une minuscule")

    if SecurityConfig.REQUIRE_DIGIT and not re.search(r"\d", password):
        errors.append("Au moins un chiffre")

    if SecurityConfig.REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Au moins un caractère spécial")

    if errors:
        return False, "Mot de passe faible : " + ", ".join(errors)

    return True, "Mot de passe valide"


def hash_password_secure(password: str) -> bytes:
    """Hache un mot de passe avec bcrypt et salt."""
    try:
        salt = bcrypt.gensalt(rounds=12)  # Plus sécurisé que le défaut
        return bcrypt.hashpw(password.encode("utf-8"), salt)
    except Exception as e:
        logger.error(f"Erreur lors du hachage du mot de passe: {e}")
        raise


def register_user_enhanced() -> None:
    """Interface d'inscription utilisateur avec sécurité renforcée."""
    st.subheader("🆕 Créer un compte")

    with st.form("register_form"):
        email = st.text_input("Email", placeholder="votre.email@exemple.com")
        password = st.text_input("Mot de passe", type="password")
        password_confirm = st.text_input("Confirmer le mot de passe", type="password")

        # Affichage des critères de mot de passe
        with st.expander("📋 Critères du mot de passe"):
            st.write(f"• Au moins {SecurityConfig.MIN_PASSWORD_LENGTH} caractères")
            if SecurityConfig.REQUIRE_UPPERCASE:
                st.write("• Au moins une majuscule")
            if SecurityConfig.REQUIRE_LOWERCASE:
                st.write("• Au moins une minuscule")
            if SecurityConfig.REQUIRE_DIGIT:
                st.write("• Au moins un chiffre")

        submitted = st.form_submit_button("Créer le compte")

        if submitted:
            # Validation des entrées
            if not email or not password or not password_confirm:
                st.error("Veuillez remplir tous les champs.")
                return

            # Validation email
            email_valid, email_msg = validate_email_enhanced(email)
            if not email_valid:
                st.error(f"❌ {email_msg}")
                return

            # Validation mot de passe
            password_valid, password_msg = validate_password_enhanced(password)
            if not password_valid:
                st.error(f"❌ {password_msg}")
                return

            # Confirmation mot de passe
            if password != password_confirm:
                st.error("❌ Les mots de passe ne correspondent pas.")
                return

            # Vérification existence utilisateur
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
                    if cursor.fetchone():
                        st.error("❌ Un compte avec cet email existe déjà.")
                        return

                    # Création du compte
                    hashed_password = hash_password_secure(password)
                    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email.lower(), hashed_password))
                    conn.commit()

                    st.success("✅ Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                    logger.info(f"Nouveau compte créé pour: {email.lower()}")

            except Exception as e:
                st.error(f"❌ Erreur lors de la création du compte: {str(e)}")
                logger.error(f"Erreur création compte pour {email}: {e}")


def login_enhanced() -> Optional[Dict[str, any]]:
    """Interface de connexion avec protection contre les attaques par force brute."""
    st.subheader("🔑 Connexion")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="votre.email@exemple.com")
        password = st.text_input("Mot de passe", type="password")

        submitted = st.form_submit_button("Se connecter")

        if submitted:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
                return None

            # Validation email
            email_valid, email_msg = validate_email_enhanced(email)
            if not email_valid:
                st.error(f"❌ {email_msg}")
                return None

            # Vérification lockout
            is_locked, remaining_time = LoginAttemptTracker.is_locked_out(email)
            if is_locked:
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                st.error(f"🔒 Compte temporairement bloqué. Réessayez dans {minutes}m {seconds}s.")
                return None

            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, password FROM users WHERE email = ?", (email.lower(),))
                    result = cursor.fetchone()

                    if result and bcrypt.checkpw(password.encode("utf-8"), result[1]):
                        # Connexion réussie
                        LoginAttemptTracker.reset_attempts(email)
                        SessionManager.update_activity()

                        user_data = {"id": result[0], "email": email.lower()}
                        st.success("✅ Connexion réussie !")
                        logger.info(f"Connexion réussie pour: {email.lower()}")
                        return user_data
                    else:
                        # Échec de connexion
                        LoginAttemptTracker.record_failed_attempt(email)
                        st.error("❌ Email ou mot de passe incorrect.")
                        return None

            except Exception as e:
                st.error(f"❌ Erreur lors de la connexion: {str(e)}")
                logger.error(f"Erreur connexion pour {email}: {e}")
                return None


def require_auth_enhanced() -> bool:
    """Vérification d'authentification avec gestion de timeout de session."""
    if not SessionManager.is_session_valid():
        if "user" in st.session_state:
            st.warning("🕐 Votre session a expiré. Veuillez vous reconnecter.")
            logout_enhanced()
        else:
            st.warning("🔒 Vous devez être connecté pour accéder à cette page.")

        st.session_state.page = "auth"
        return False

    # Mettre à jour l'activité
    SessionManager.update_activity()
    return True


def logout_enhanced() -> None:
    """Déconnexion sécurisée avec nettoyage complet de la session."""
    if "user" in st.session_state:
        email = st.session_state.user.get("email", "Inconnu")
        logger.info(f"Déconnexion de: {email}")

    # Nettoyer complètement la session
    keys_to_remove = ["user", "character", "campaign", "history", "page", "portrait_url", "last_activity", "model_choice"]

    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

    # Nettoyer aussi les clés de tentatives de connexion
    keys_to_check = list(st.session_state.keys())
    for key in keys_to_check:
        if key.startswith("login_attempts_"):
            del st.session_state[key]

    st.session_state.page = "auth"
    st.success("✅ Déconnexion réussie !")
    st.rerun()


def get_current_user_enhanced() -> Optional[Dict[str, any]]:
    """Retourne l'utilisateur actuel avec vérification de session."""
    if not SessionManager.is_session_valid():
        return None
    return st.session_state.get("user")


def session_info_widget() -> None:
    """Widget d'information de session pour la sidebar."""
    if "user" in st.session_state:
        session_info = SessionManager.get_session_info()
        remaining_minutes = int(session_info["remaining_time"] // 60)

        st.sidebar.markdown(f"**👤 {session_info['user']['email']}**")
        st.sidebar.markdown(f"⏱️ Session: {remaining_minutes}min restantes")

        if remaining_minutes < 5:
            st.sidebar.warning("⚠️ Session bientôt expirée")


# Fonctions de rétrocompatibilité
def validate_email(email: str) -> bool:
    """Validation d'email (rétrocompatibilité)."""
    valid, _ = validate_email_enhanced(email)
    return valid


def validate_password(password: str) -> Tuple[bool, str]:
    """Validation de mot de passe (rétrocompatibilité)."""
    return validate_password_enhanced(password)


def register_user() -> None:
    """Inscription utilisateur (rétrocompatibilité)."""
    register_user_enhanced()


def login() -> Optional[Dict[str, any]]:
    """Connexion utilisateur (rétrocompatibilité)."""
    return login_enhanced()


def require_auth() -> bool:
    """Vérification d'authentification (rétrocompatibilité)."""
    return require_auth_enhanced()


def logout() -> None:
    """Déconnexion (rétrocompatibilité)."""
    logout_enhanced()


def get_current_user() -> Optional[Dict[str, any]]:
    """Utilisateur actuel (rétrocompatibilité)."""
    return get_current_user_enhanced()
