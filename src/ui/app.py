"""
Application principale Streamlit refactorisée
"""

import logging
from typing import Any, Dict, Optional

import streamlit as st

from src.data.database import init_db
from src.ui.components.styles import apply_custom_css, configure_page, create_styled_button
from src.ui.views.auth_page import show_auth_page
from src.ui.views.campaign_page import show_campaign_page
from src.ui.views.character_page import show_character_page
from src.ui.views.chatbot_page import show_chatbot_page
from src.ui.views.dashboard_page import show_dashboard_page
from src.ui.views.performance_page import show_performance_page
from src.ui.views.settings_page import show_settings_page

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_app() -> None:
    """Initialise l'application."""
    try:
        init_db()
        logger.info("Application initialisée avec succès")
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation: {e}")
        logger.error(f"Erreur initialisation: {e}")
        st.stop()


def show_navigation() -> None:
    """Affiche la navigation dans la sidebar."""
    # Vérifier si l'utilisateur est connecté
    user = st.session_state.get("user", None)

    if user:
        with st.sidebar:
            # Info utilisateur
            st.markdown(
                f"""
            <div style="
                background: rgba(102, 126, 234, 0.1);
                padding: 0.8rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                border-left: 4px solid #667eea;
            ">
                <strong>👤 {user.get('email', 'Utilisateur')}</strong>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Navigation principale
            nav_pages = {
                "🏠 Tableau de bord": "dashboard",
                "💬 Chat avec IA": "chatbot",
                "📊 Performances": "performance",
                "⚙️ Paramètres": "settings",
            }

            for label, page_key in nav_pages.items():
                if st.button(label, key=page_key, use_container_width=True):
                    st.session_state.page = page_key
                    st.rerun()

            st.markdown("---")

            # Déconnexion avec style danger
            if st.button("🚪 Déconnexion", key="logout", use_container_width=True):
                # Clear user session
                if "user" in st.session_state:
                    del st.session_state["user"]
                st.session_state.page = "auth"
                st.rerun()


def main() -> None:
    """Fonction principale de l'application."""
    # Configuration de la page
    configure_page()

    # Application des styles CSS
    apply_custom_css()

    # Initialisation SEULEMENT au premier chargement
    if "app_initialized" not in st.session_state:
        initialize_app()
        st.session_state.app_initialized = True

    # Gestion du state de navigation
    if "page" not in st.session_state:
        st.session_state.page = "auth"

    # Afficher la navigation si connecté
    user = st.session_state.get("user", None)
    if user:
        show_navigation()

    # Routage des pages
    page_functions = {
        "auth": show_auth_page,
        "dashboard": show_dashboard_page,
        "campaign": show_campaign_page,
        "character": show_character_page,
        "chatbot": show_chatbot_page,
        "performance": show_performance_page,
        "settings": show_settings_page,
    }

    current_page = st.session_state.page
    if current_page in page_functions:
        try:
            page_functions[current_page]()
        except Exception as e:
            st.error(f"❌ Erreur dans la page {current_page}: {e}")
            logger.error(f"Erreur page {current_page}: {e}")
    else:
        st.error(f"Page inconnue: {current_page}")
        st.session_state.page = "auth"
        st.rerun()


if __name__ == "__main__":
    main()
