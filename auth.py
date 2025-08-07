import logging
import re
import sqlite3
from typing import Dict, Optional

import bcrypt
import streamlit as st

from database import get_connection

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Valide le format d'un email."""
    if not email or not email.strip():
        return False

    # Pattern plus strict pour éviter les points consécutifs
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"

    # Vérifications supplémentaires
    if ".." in email or email.startswith(".") or email.endswith("."):
        return False

    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    Valide la force d'un mot de passe.

    Returns:
        Tuple (is_valid, message)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, "Mot de passe valide"


def register_user() -> None:
    """Interface d'inscription d'un nouvel utilisateur."""
    st.subheader("🆕 Créer un compte")

    with st.form("register_form"):
        email = st.text_input("Email", placeholder="votre.email@exemple.com")
        password = st.text_input("Mot de passe", type="password", help="8+ caractères, majuscule, minuscule, chiffre")
        confirm = st.text_input("Confirmer le mot de passe", type="password")

        submitted = st.form_submit_button("Créer le compte")

        if submitted:
            # Validation des entrées
            if not email or not password:
                st.error("Tous les champs sont obligatoires.")
                return

            if not validate_email(email):
                st.error("Format d'email invalide.")
                return

            password_valid, password_msg = validate_password(password)
            if not password_valid:
                st.error(password_msg)
                return

            if password != confirm:
                st.error("Les mots de passe ne correspondent pas.")
                return

            # Hachage sécurisé du mot de passe
            try:
                hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

                conn = get_connection()
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email.lower(), hashed))
                    conn.commit()
                    st.success("✅ Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                    logger.info(f"Nouveau compte créé pour: {email}")
                except sqlite3.IntegrityError:
                    st.error("❌ Cet email est déjà utilisé.")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création du compte: {str(e)}")
                    logger.error(f"Erreur création compte pour {email}: {e}")
                finally:
                    conn.close()
            except Exception as e:
                st.error(f"❌ Erreur de chiffrement: {str(e)}")
                logger.error(f"Erreur hachage mot de passe: {e}")


def login() -> Optional[Dict[str, any]]:
    """
    Interface de connexion utilisateur.

    Returns:
        Dictionnaire avec les infos utilisateur si succès, None sinon
    """
    st.subheader("🔑 Connexion")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="votre.email@exemple.com")
        password = st.text_input("Mot de passe", type="password")

        submitted = st.form_submit_button("Se connecter")

        if submitted:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
                return None

            if not validate_email(email):
                st.error("Format d'email invalide.")
                return None

            try:
                conn = get_connection()
                try:
                    c = conn.cursor()
                    c.execute("SELECT id, password FROM users WHERE email = ?", (email.lower(),))
                    result = c.fetchone()

                    if result and bcrypt.checkpw(password.encode("utf-8"), result[1]):
                        st.success("✅ Connexion réussie !")
                        user_data = {"id": result[0], "email": email.lower()}
                        logger.info(f"Connexion réussie pour: {email}")
                        return user_data
                    else:
                        st.error("❌ Email ou mot de passe incorrect.")
                        logger.warning(f"Tentative de connexion échouée pour: {email}")
                        return None
                except Exception as e:
                    st.error(f"❌ Erreur lors de la connexion: {str(e)}")
                    logger.error(f"Erreur connexion pour {email}: {e}")
                    return None
                finally:
                    conn.close()
            except Exception as e:
                st.error(f"❌ Erreur de base de données: {str(e)}")
                logger.error(f"Erreur DB lors connexion: {e}")
                return None


def get_current_user() -> Optional[Dict[str, any]]:
    """Récupère l'utilisateur actuellement connecté depuis la session."""
    return st.session_state.get("user")


def logout() -> None:
    """Déconnecte l'utilisateur actuel."""
    if "user" in st.session_state:
        email = st.session_state.user.get("email", "Inconnu")
        logger.info(f"Déconnexion de: {email}")

    # Nettoyer la session
    keys_to_remove = ["user", "character", "campaign", "history", "page", "portrait_url"]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.page = "auth"
    st.success("✅ Déconnexion réussie !")
    st.rerun()


def require_auth() -> bool:
    """
    Vérifie si l'utilisateur est authentifié.

    Returns:
        True si authentifié, False sinon
    """
    user = get_current_user()
    if not user:
        st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
        st.session_state.page = "auth"
        return False
    return True
