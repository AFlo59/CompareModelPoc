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

    # === HEADER DE LA PAGE AVEC INFOS CAMPAGNE/JOUEUR ===
    # Structure en 3 colonnes : Campagne | Espace | Personnage
    header_col1, header_col2, header_col3 = st.columns([2, 1, 2])
    
    # COLONNE GAUCHE : INFORMATIONS CAMPAGNE + PORTRAIT MJ
    with header_col1:
        if "campaign" in st.session_state and st.session_state.campaign:
            camp = st.session_state.campaign
            
            # Card campagne avec style
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                padding: 1rem;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 1rem;
            ">
                <h3 style="margin: 0 0 0.5rem 0; color: #667eea;">📜 {camp['name']}</h3>
                <p style="margin: 0.2rem 0;"><strong>🌍 Langue:</strong> {camp['language']}</p>
                <p style="margin: 0.2rem 0;"><strong>🎭 Thèmes:</strong> {', '.join(camp.get('themes', []))}</p>
                <p style="margin: 0.2rem 0;"><strong>🤖 IA:</strong> {camp.get('ai_model', 'GPT-4o')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Portrait du MJ si disponible
            if camp.get("gm_portrait"):
                st.image(camp["gm_portrait"], width=150, caption="🧙‍♂️ Maître du Jeu")
            else:
                # Afficher un avatar de secours si pas de portrait
                st.image("https://api.dicebear.com/7.x/adventurer/png?seed=GameMaster&size=128", width=120)
        else:
            st.warning("⚠️ Aucune campagne sélectionnée")
    
    # COLONNE MILIEU : ESPACEMENT
    with header_col2:
        st.empty()
    
    # COLONNE DROITE : INFORMATIONS PERSONNAGE + PORTRAIT
    with header_col3:
        if "character" in st.session_state and st.session_state.character:
            char = st.session_state.character
            
            # Card personnage avec style
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(118, 75, 162, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
                padding: 1rem;
                border-radius: 10px;
                border-left: 4px solid #764ba2;
                margin-bottom: 1rem;
            ">
                <h3 style="margin: 0 0 0.5rem 0; color: #764ba2;">🎭 {char['name']}</h3>
                <p style="margin: 0.2rem 0;"><strong>📊 Niveau {char.get('level', 1)}</strong></p>
                <p style="margin: 0.2rem 0;"><strong>🧬 Race:</strong> {char.get('race', 'Inconnue')}</p>
                <p style="margin: 0.2rem 0;"><strong>⚔️ Classe:</strong> {char.get('class', 'Inconnue')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Portrait du personnage si disponible
            if char.get("portrait_url"):
                st.image(char["portrait_url"], width=150, caption=f"🧙‍♂️ {char['name']}")
            else:
                st.image(f"https://api.dicebear.com/7.x/adventurer/png?seed={char['name']}&size=128", width=120)
        else:
            st.warning("⚠️ Aucun personnage sélectionné")

    st.divider()

    # === SIDEBAR SIMPLIFIÉE POUR NAVIGATION ===
    with st.sidebar:
        st.markdown("### 🎯 Navigation Rapide")

        # Boutons de navigation campagne
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Autre campagne", use_container_width=True):
                st.session_state.page = "campaign"
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

                campaign_options = {f"{camp['name']} ({camp.get('message_count', 0)} msg)": camp for camp in user_campaigns}

                selected_campaign_name = st.selectbox(
                    "📚 Changement rapide :",
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        except Exception as e:
            st.error(f"Erreur campagnes: {e}")

        st.divider()
        
        # Navigation vers autres pages
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("🧙‍♂️ Mes Personnages", use_container_width=True):
            st.session_state.page = "character"
            st.rerun()

    # === INTERFACE PRINCIPALE DU CHATBOT ===
    st.markdown("### 🎲 Interface de Jeu")
    
    # Onglets pour organiser les fonctionnalités
    tab1, tab2, tab3 = st.tabs(["🎲 Chat & Aventure", "📊 Performances", "⚙️ Paramètres"])
    
    with tab1:
        # Interface de chat principale
        launch_chat_interface(st.session_state.user["id"])
    
    with tab2:
        # Performances de l'utilisateur
        from src.analytics.performance import show_performance
        show_performance(st.session_state.user["id"])
    
    with tab3:
        # Paramètres spécifiques au chatbot
        st.subheader("⚙️ Paramètres de Session")

        # Gestion des données de session
        st.markdown("### 🗑️ Gestion des Données")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Nouvelle Aventure", help="Efface l'historique du chat actuel", use_container_width=True):
                if "history" in st.session_state:
                    del st.session_state["history"]
                st.success("✅ Historique réinitialisé !")
                st.rerun()

        with col2:
            if st.button("🎭 Changer Personnage", help="Retour à la gestion des personnages", use_container_width=True):
                st.session_state.page = "character"
                st.rerun()
        
        with col3:
            if st.button("🏕️ Changer Campagne", help="Retour à la gestion des campagnes", use_container_width=True):
                st.session_state.page = "campaign"
                st.rerun()
        
        st.divider()
        
        # Informations de session
        st.markdown("### 📊 Informations de Session")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "campaign" in st.session_state and st.session_state.campaign:
                st.info(f"**Campagne active :** {st.session_state.campaign.get('name', 'Sans nom')}")
            else:
                st.warning("⚠️ Aucune campagne active")
        
        with col2:
            if "character" in st.session_state and st.session_state.character:
                st.info(f"**Personnage actif :** {st.session_state.character.get('name', 'Sans nom')}")
            else:
                st.warning("⚠️ Aucun personnage actif")
