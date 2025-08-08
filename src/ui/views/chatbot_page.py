"""
Page du chatbot principal
"""

import streamlit as st
from src.auth.auth import require_auth, logout
from src.ai.chatbot import launch_chat_interface
from src.data.models import get_user_campaigns, get_campaign_messages

def show_chatbot_page() -> None:
    """Affiche la page principale du chatbot."""
    if not require_auth():
        return

    # Sidebar avec informations
    with st.sidebar:
        # Bouton de déconnexion
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout()

        st.divider()

        # Sélecteur de campagne
        st.markdown("### 🎯 Changer de campagne")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Autre campagne", use_container_width=True):
                st.session_state.page = "campaign_or_resume"
                st.rerun()
        with col2:
            if st.button("🆕 Nouvelle", use_container_width=True):
                st.session_state.page = "campaign"
                st.rerun()

        # Sélecteur de campagnes existantes dans un selectbox
        try:
            user_campaigns = get_user_campaigns(st.session_state.user["id"])
            if user_campaigns and len(user_campaigns) > 1:
                current_campaign_id = st.session_state.get("campaign", {}).get("id")

                campaign_options = {f"{camp['name']} ({camp['message_count']} msg)": camp for camp in user_campaigns}

                selected_campaign_name = st.selectbox(
                    "📚 Campagnes rapides :",
                    options=list(campaign_options.keys()),
                    index=(
                        0
                        if not current_campaign_id
                        else next(
                            (i for i, (_, camp) in enumerate(campaign_options.items()) if camp["id"] == current_campaign_id), 0
                        )
                    ),
                    help="Changement rapide de campagne",
                )

                if st.button("🔁 Changer", use_container_width=True):
                    selected_campaign = campaign_options[selected_campaign_name]
                    st.session_state.campaign = selected_campaign

                    # Charger l'historique de la campagne
                    try:
                        messages = get_campaign_messages(st.session_state.user["id"], selected_campaign["id"])
                        st.session_state.history = messages
                        st.success(f"📖 Campagne '{selected_campaign['name']}' chargée!")

                        # Forcer le rechargement complet de la page pour mettre à jour le chatbot
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        except Exception as e:
            st.error(f"Erreur campagnes: {e}")

        st.divider()

        # Informations campagne (EN PREMIER)
        st.markdown("### 📜 Campagne")
        if "campaign" in st.session_state and st.session_state.campaign:
            camp = st.session_state.campaign

            # Portrait du MJ en premier s'il existe
            if camp.get("gm_portrait"):
                st.image(camp["gm_portrait"], width=200, caption="Maître du Jeu", use_column_width=False)

            st.markdown(
                f"""
            <div class="campaign-info">
                <h4>{camp['name']}</h4>
                <p><strong>Langue:</strong> {camp['language']}</p>
                <p><strong>Thèmes:</strong> {', '.join(camp.get('themes', []))}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.divider()

        # Informations personnage (EN SECOND)
        st.markdown("### 🎭 Personnage")
        if "character" in st.session_state and st.session_state.character:
            char = st.session_state.character

            # Portrait en premier s'il existe
            if char.get("portrait"):
                st.image(char["portrait"], width=200, caption=f"Portrait de {char['name']}", use_column_width=False)

            st.markdown(
                f"""
            <div class="character-card">
                <h4>{char['name']}</h4>
                <p><strong>{char.get('gender', '')} {char.get('race', '')} {char.get('class', '')}</strong></p>
                <p><em>{char.get('description', 'Aucune description')}</em></p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Navigation principale avec radio buttons
    st.markdown("### 🧭 Navigation")

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

    current_section = st.radio("Choisissez une section :", ["🎲 Aventure", "📊 Performances", "⚙️ Paramètres"], horizontal=True)

    st.divider()

    if current_section == "🎲 Aventure":
        launch_chat_interface(st.session_state.user["id"])
    elif current_section == "📊 Performances":
        from src.analytics.performance import show_performance
        show_performance(st.session_state.user["id"])
    else:  # Paramètres
        st.subheader("⚙️ Paramètres de l'application")

        # Réinitialisation des données
        st.markdown("### 🗑️ Gestion des données")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Nouvelle aventure", help="Efface l'historique du chat actuel"):
                if "history" in st.session_state:
                    del st.session_state["history"]
                st.success("Historique réinitialisé !")
                st.rerun()

        with col2:
            if st.button("🎭 Changer de personnage", help="Retour à la création de personnage"):
                st.session_state.page = "character"
                st.rerun()
