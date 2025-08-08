"""
Page d'authentification
"""

import streamlit as st
from src.auth.auth import get_current_user, login, logout, register_user, require_auth
from src.data.models import get_user_campaigns

def determine_user_next_page(user_id: int) -> str:
    """Détermine la prochaine page à afficher selon l'état de l'utilisateur."""
    try:
        campaigns = get_user_campaigns(user_id)
        # Si l'utilisateur a des campagnes, aller au dashboard
        # Sinon, l'inviter à créer une campagne
        return "dashboard" if campaigns else "campaign"
    except Exception:
        # En cas d'erreur, rediriger vers dashboard (sécurisé)
        return "dashboard"

def show_auth_page() -> None:
    """Affiche la page d'authentification."""
    # Vérifier si l'utilisateur est déjà connecté
    if "user" in st.session_state and st.session_state.user:
        # Rediriger automatiquement si déjà connecté
        next_page = determine_user_next_page(st.session_state.user["id"])
        st.session_state.page = next_page
        st.rerun()
        return
    
    st.markdown(
        '<div class="main-header"><h1>🎲 DnD AI GameMaster</h1><p>Votre assistant IA pour des aventures épiques</p></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        auth_choice = st.radio("Choisissez une action", ["🔑 Connexion", "🆕 Créer un compte"], horizontal=True)

        if auth_choice == "🔑 Connexion":
            user = login()
            if user:
                st.session_state.user = user
                # Afficher un message de succès persistant
                st.success("✅ Connexion réussie ! Redirection en cours...")
                # Redirection intelligente selon l'état de l'utilisateur
                next_page = determine_user_next_page(user["id"])
                st.session_state.page = next_page
                # Délai court pour laisser le temps de voir le message
                import time
                time.sleep(1)
                st.rerun()
        else:
            register_user()
