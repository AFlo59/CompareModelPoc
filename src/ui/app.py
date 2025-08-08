"""
Application principale Streamlit refactorisée
"""

import logging
from typing import Any, Dict, Optional

import streamlit as st

from src.ui.components.styles import apply_custom_css, configure_page
from src.ui.pages.auth_page import show_auth_page
from src.ui.pages.dashboard_page import show_dashboard_page
from src.ui.pages.chatbot_page import show_chatbot_page
from src.ui.pages.performance_page import show_performance_page
from src.ui.pages.settings_page import show_settings_page
from src.data.database import init_db

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

def main() -> None:
    """Fonction principale de l'application."""
    # Configuration de la page
    configure_page()
    
    # Application des styles CSS
    apply_custom_css()
    
    # Initialisation
    initialize_app()

    # Gestion du state de navigation
    if "page" not in st.session_state:
        st.session_state.page = "auth"

    # Routage des pages
    page_functions = {
        "auth": show_auth_page,
        "dashboard": show_dashboard_page,
        "chatbot": show_chatbot_page,
        "performance": show_performance_page,
        "settings": show_settings_page,
        # TODO: Ajouter les autres pages (campaign, character, etc.)
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
