"""
Module des vues UI pour l'application DnD AI GameMaster.

Ce module contient toutes les pages de l'interface utilisateur Streamlit
organisées sous forme de vues modulaires.
"""

# Import des vues principales
from .auth_page import determine_user_next_page, show_auth_page
from .campaign_page import show_campaign_page
from .character_page import show_character_page
from .chatbot_page import show_chatbot_page
from .dashboard_page import show_dashboard_page
from .settings_page import show_settings_page

__all__ = [
    "show_auth_page",
    "determine_user_next_page",
    "show_dashboard_page",
    "show_chatbot_page",
    "show_campaign_page",
    "show_character_page",
    "show_settings_page",
]

__doc__ = "Module des vues UI - DnD AI GameMaster"
