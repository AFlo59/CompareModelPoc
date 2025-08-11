"""
Page du tableau de bord principal
"""

import streamlit as st

from src.auth.auth import logout, require_auth
from src.data.models import get_campaign_messages, get_user_campaigns


def show_dashboard_page() -> None:
    """Affiche le dashboard principal après connexion."""
    if not require_auth():
        return

    st.title("🎲 DnD AI GameMaster - Tableau de bord")

    # Message de bienvenue
    user_name = st.session_state.user.get("email", "Utilisateur")
    st.markdown(f"### Bonjour **{user_name}** ! 👋")

    # Vérification des campagnes existantes
    try:
        campaigns = get_user_campaigns(st.session_state.user["id"])
        total_campaigns = len(campaigns)
    except Exception as e:
        st.error(f"Erreur lors du chargement des campagnes: {e}")
        campaigns = []
        total_campaigns = 0

    # Statistiques rapides
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 Campagnes", total_campaigns)
    with col2:
        # Compter les messages totaux (approximatif)
        total_messages = sum(camp.get("message_count", 0) for camp in campaigns)
        st.metric("💬 Messages", total_messages)
    with col3:
        st.metric("🤖 Modèles", "4 disponibles")

    st.divider()

    # Actions principales
    st.markdown("### 🎯 Que souhaitez-vous faire ?")

    # Organiser en 2 colonnes pour un meilleur affichage
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎮 Jouer")

        if st.button("🆕 Créer une nouvelle campagne", use_container_width=True, type="primary"):
            st.session_state.page = "campaign"
            st.rerun()

        if campaigns:
            st.markdown("**Campagnes disponibles :**")
            for i, camp in enumerate(campaigns[:5]):  # Afficher jusqu'à 5 campagnes
                if st.button(
                    f"🏰 {camp['name']} ({camp.get('message_count', 0)} msg)", key=f"quick_camp_{i}", use_container_width=True
                ):
                    st.session_state.campaign = camp
                    # Charger l'historique
                    try:
                        messages = get_campaign_messages(st.session_state.user["id"], camp["id"])
                        st.session_state.history = messages
                    except Exception:
                        st.session_state.history = []
                    st.session_state.page = "chatbot"
                    st.rerun()

            # Bouton pour voir toutes les campagnes s'il y en a plus de 5
            if len(campaigns) > 5:
                if st.button("📚 Voir toutes les campagnes", use_container_width=True):
                    st.session_state.page = "campaign_or_resume"
                    st.rerun()

    with col2:
        st.markdown("#### 📊 Analyser")

        if st.button("📈 Voir les performances", use_container_width=True):
            st.session_state.page = "performance"
            st.rerun()

        if st.button("⚙️ Paramètres", use_container_width=True):
            st.session_state.page = "settings"
            st.rerun()

        st.markdown("#### 🚪 Session")
        if st.button("🔓 Se déconnecter", use_container_width=True):
            logout()

    # Section informative en bas
    if campaigns:
        st.divider()
        st.markdown("### 📋 Aperçu des campagnes")

        for camp in campaigns[:2]:  # Afficher détails des 2 premières
            with st.expander(f"🏰 {camp['name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Langue:** {camp['language']}")
                    st.write(f"**Messages:** {camp.get('message_count', 0)}")
                with col2:
                    st.write(f"**Thèmes:** {', '.join(camp.get('themes', []))}")
                    if camp.get("last_activity"):
                        st.write(f"**Dernière activité:** {camp['last_activity'][:10]}")
