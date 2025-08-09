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
        /* Cacher la navigation automatique de Streamlit */
        .css-1d391kg {
            display: none !important;
        }
        .css-1v0mbdj {
            display: none !important;
        }
        /* Cacher la section de navigation automatique */
        section[data-testid="stSidebar"] > div > div > div > ul {
            display: none !important;
        }
        /* Style pour nos boutons de navigation personnalisés */
        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
            text-align: left;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: 1px solid #667eea;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
            border-color: #764ba2;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(118, 75, 162, 0.3);
        }
        .stButton > button:active {
            transform: translateY(0px);
        }
        
        /* Boutons dans les pages principales */
        div[data-testid="column"] .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border: 1px solid #667eea;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        div[data-testid="column"] .stButton > button:hover {
            background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(118, 75, 162, 0.3);
        }
        
        /* Boutons de formulaire (connexion, inscription) */
        .stForm .stButton > button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border: 1px solid #667eea;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            width: 100%;
        }
        .stForm .stButton > button:hover {
            background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
            transform: translateY(-1px);
        }
        
        /* Boutons selon leur fonction */
        /* Bouton Success (vert) */
        .btn-success {
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%) !important;
            color: white !important;
            border: 1px solid #28a745 !important;
        }
        .btn-success:hover {
            background: linear-gradient(90deg, #20c997 0%, #28a745 100%) !important;
        }
        
        /* Bouton Danger (rouge) */
        .btn-danger {
            background: linear-gradient(90deg, #dc3545 0%, #fd7e14 100%) !important;
            color: white !important;
            border: 1px solid #dc3545 !important;
        }
        .btn-danger:hover {
            background: linear-gradient(90deg, #fd7e14 0%, #dc3545 100%) !important;
        }
        
        /* Bouton Warning (orange) */
        .btn-warning {
            background: linear-gradient(90deg, #ffc107 0%, #fd7e14 100%) !important;
            color: #212529 !important;
            border: 1px solid #ffc107 !important;
        }
        .btn-warning:hover {
            background: linear-gradient(90deg, #fd7e14 0%, #ffc107 100%) !important;
        }
        
        /* Bouton Info (cyan) */
        .btn-info {
            background: linear-gradient(90deg, #17a2b8 0%, #6f42c1 100%) !important;
            color: white !important;
            border: 1px solid #17a2b8 !important;
        }
        .btn-info:hover {
            background: linear-gradient(90deg, #6f42c1 0%, #17a2b8 100%) !important;
        }
        
        /* Style pour les cards de navigation pour qu'elles matchent le header */
        .sidebar .element-container {
            background: rgba(102, 126, 234, 0.1);
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        
        /* Amélioration de la sidebar */
        .sidebar .block-container {
            background: linear-gradient(180deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
            border-radius: 0 15px 15px 0;
        }
        
        /* Style spécifique pour le bouton de déconnexion */
        button[data-testid="stBaseButton-secondary"]:has-text("🚪 Déconnexion"),
        button:contains("🚪 Déconnexion") {
            background: linear-gradient(90deg, #dc3545 0%, #fd7e14 100%) !important;
            color: white !important;
            border: 1px solid #dc3545 !important;
        }
        
        /* Cibler spécifiquement le bouton logout par sa clé */
        div[data-testid="stButton"]:has(button[key="logout"]) button {
            background: linear-gradient(90deg, #dc3545 0%, #fd7e14 100%) !important;
            color: white !important;
            border: 1px solid #dc3545 !important;
        }
        div[data-testid="stButton"]:has(button[key="logout"]) button:hover {
            background: linear-gradient(90deg, #fd7e14 0%, #dc3545 100%) !important;
            box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3) !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_styled_button(label: str, key: str, button_type: str = "primary", use_container_width: bool = True):
    """
    Crée un bouton stylé selon son type.

    Args:
        label: Texte du bouton
        key: Clé unique du bouton
        button_type: Type de bouton ("primary", "success", "danger", "warning", "info")
        use_container_width: Utiliser toute la largeur
    """
    # Classes CSS selon le type
    css_classes = {
        "primary": "",  # Style par défaut (gradient bleu-violet)
        "success": "btn-success",
        "danger": "btn-danger",
        "warning": "btn-warning",
        "info": "btn-info",
    }

    css_class = css_classes.get(button_type, "")

    # Injecter le CSS pour ce bouton spécifique si nécessaire
    if css_class:
        st.markdown(
            f"""
        <style>
        div[data-testid="stButton"] button[key="{key}"] {{
            background: var(--{button_type}-bg) !important;
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

    return st.button(label, key=key, use_container_width=use_container_width)


def configure_page():
    """Configure la page Streamlit."""
    st.set_page_config(page_title="DnD AI GameMaster", page_icon="🎲", layout="wide", initial_sidebar_state="expanded")
