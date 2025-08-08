"""
Styles CSS et configuration de l'interface utilisateur
"""

import streamlit as st

def apply_custom_css():
    """Applique les styles CSS personnalisés."""
    st.markdown(
        """
    <style>
        .main-header {
            text-align: center;
            padding: 1rem 0;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .character-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin-top: 0.5rem;
        }
        .campaign-info {
            background: #e8f4f8;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #17a2b8;
            margin-top: 0.5rem;
        }
        /* Réduire l'espace après les images dans la sidebar */
        .sidebar .stImage {
            margin-bottom: 0.5rem !important;
        }
        /* Réduire l'espace général de la sidebar */
        .sidebar .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* Réduire l'espace des dividers */
        .sidebar hr {
            margin: 0.5rem 0 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

def configure_page():
    """Configure la page Streamlit."""
    st.set_page_config(
        page_title="DnD AI GameMaster", 
        page_icon="🎲", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )
