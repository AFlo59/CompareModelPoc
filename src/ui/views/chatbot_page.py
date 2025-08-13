"""
Page du chatbot principal
"""

import time

import streamlit as st

from src.ai.chatbot import launch_chat_interface
from src.auth.auth import logout, require_auth
from src.data.models import get_campaign_messages, get_user_campaigns, get_user_characters


def show_chatbot_page() -> None:
    """Affiche la page principale du chatbot."""
    if not require_auth():
        return

    # *** FORCER LA RÉACTUALISATION DES DONNÉES SI CHANGEMENT DE CAMPAGNE ***
    user_id = st.session_state.user["id"]

    # Vérifier si on a un selected_campaign mais pas de campaign en session
    selected_campaign_id = getattr(st.session_state, "selected_campaign", None)
    current_campaign_id = st.session_state.get("campaign", {}).get("id")

    if selected_campaign_id and selected_campaign_id != current_campaign_id:
        # Recharger la campagne depuis la base
        try:
            fresh_campaigns = get_user_campaigns(user_id)
            new_campaign = next((c for c in fresh_campaigns if c.get("id") == selected_campaign_id), None)
            if new_campaign:
                st.session_state.campaign = new_campaign
                # Réinitialiser l'historique pour cette nouvelle campagne
                if "history" in st.session_state:
                    del st.session_state["history"]

                # Forcer l'initialisation pour une nouvelle campagne
                st.session_state.force_campaign_init = True
                st.success(f"✅ Campagne '{new_campaign.get('name', 'Inconnue')}' chargée !")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement de la campagne : {e}")

    # Auto-refresh si on vient de créer un personnage ou une campagne
    if hasattr(st.session_state, "force_campaign_init") and st.session_state.force_campaign_init:
        st.session_state.force_campaign_init = False
        try:
            # Recharger toutes les données
            fresh_campaigns = get_user_campaigns(user_id)
            if selected_campaign_id:
                new_campaign = next((c for c in fresh_campaigns if c.get("id") == selected_campaign_id), None)
                if new_campaign:
                    st.session_state.campaign = new_campaign
        except Exception:
            pass

    # Déterminer la campagne et le personnage actifs (robuste: attribut ou clé dict)
    campaign = getattr(st.session_state, "campaign", None)
    if campaign is None:
        try:
            campaign = st.session_state.get("campaign")
        except Exception:
            campaign = None
    character = getattr(st.session_state, "character", None)
    if character is None:
        try:
            character = st.session_state.get("character")
        except Exception:
            character = None

    # Rafraîchir depuis la base pour récupérer les dernières URLs de portraits
    try:
        user_id = st.session_state.user["id"]
        fresh_campaigns = get_user_campaigns(user_id)
        if campaign:
            fresh_camp = next((c for c in fresh_campaigns if c.get("id") == campaign.get("id")), None)
            if fresh_camp:
                st.session_state.campaign = fresh_camp
                campaign = fresh_camp
        if character:
            fresh_chars = get_user_characters(user_id)
            fresh_char = next((ch for ch in fresh_chars if ch.get("id") == character.get("id")), None)
            if fresh_char:
                st.session_state.character = fresh_char
                character = fresh_char
    except Exception:
        pass

    # Si aucun personnage n'est en session mais qu'une campagne est active,
    # tenter de sélectionner automatiquement le dernier personnage lié à cette campagne
    if campaign and not character:
        try:
            all_characters = get_user_characters(user_id)
            linked = [c for c in all_characters if c.get("campaign_id") == campaign.get("id")]
            if linked:
                st.session_state.character = linked[0]
                character = linked[0]
        except Exception:
            pass

    # === INTERFACE EN-TÊTE ===
    st.markdown("### 🎲 Interface de Jeu")
    # Important: créer d'abord l'onglet principal pour stabiliser la zone d'entrée en bas
    tab1, tab2, tab3 = st.tabs(["🎲 Chat & Aventure", "📊 Performances", "⚙️ Paramètres"])

    # Les cartes de campagne/personnage doivent vivre dans l'onglet pour apparaître sous les onglets mais au-dessus du chat

    # === SIDEBAR SIMPLIFIÉE POUR NAVIGATION ===
    with st.sidebar:
        st.markdown("### 🎯 Navigation Rapide")

        # Boutons de navigation campagne
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Autre campagne", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
        with col2:
            if st.button("🆕 Nouvelle campagne", use_container_width=True):
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

                    # Forcer le changement de campagne avec nettoyage
                    old_campaign_id = st.session_state.get("campaign", {}).get("id")
                    if selected_campaign["id"] != old_campaign_id:
                        st.session_state.campaign = selected_campaign
                        st.session_state.selected_campaign = selected_campaign["id"]

                        # Charger l'historique de la nouvelle campagne AVANT le rerun
                        try:
                            messages = get_campaign_messages(st.session_state.user["id"], selected_campaign["id"])
                            st.session_state.history = messages
                            st.success(f"🔄 Campagne '{selected_campaign['name']}' chargée avec {len(messages)} messages!")
                        except Exception as e:
                            st.error(f"❌ Erreur lors du chargement des messages: {e}")
                            # Nettoyer l'historique en cas d'erreur
                            if "history" in st.session_state:
                                del st.session_state["history"]

                        # Forcer la réinitialisation après avoir chargé les messages
                        st.rerun()
                    else:
                        # Même campagne sélectionnée, juste recharger les messages
                        try:
                            messages = get_campaign_messages(st.session_state.user["id"], selected_campaign["id"])
                            st.session_state.history = messages
                            st.success(f"� Messages rechargés: {len(messages)} messages!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors du rechargement: {e}")
        except Exception as e:
            st.error(f"Erreur campagnes: {e}")

        st.divider()

    with tab1:
        # Cartes Campagne / Personnage juste sous les onglets (avant le chat)
        cards_col1, _, cards_col3 = st.columns([2, 1, 2])

        with cards_col1:
            if campaign:
                camp = campaign
                st.markdown(
                    f"""
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
                """,
                    unsafe_allow_html=True,
                )
                # Affichage cohérent du portrait MJ
                gm_portrait = camp.get("gm_portrait")
                if gm_portrait and str(gm_portrait).strip() and gm_portrait != "None":
                    try:
                        st.image(gm_portrait, width=150, caption="🧙‍♂️ Maître du Jeu")
                    except Exception:
                        # Fallback si l'URL est invalide
                        st.image(
                            "https://api.dicebear.com/7.x/adventurer/png?seed=GameMaster&size=128",
                            width=120,
                            caption="🧙‍♂️ Maître du Jeu (placeholder)",
                        )
                else:
                    st.image(
                        "https://api.dicebear.com/7.x/adventurer/png?seed=GameMaster&size=128",
                        width=120,
                        caption="🧙‍♂️ Maître du Jeu (placeholder)",
                    )
            else:
                st.warning("⚠️ Aucune campagne sélectionnée")

        with cards_col3:
            if character:
                char = character
                st.markdown(
                    f"""
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
                """,
                    unsafe_allow_html=True,
                )
                # Affichage cohérent du portrait personnage
                char_portrait = char.get("portrait_url")
                if char_portrait and str(char_portrait).strip() and char_portrait != "None":
                    try:
                        st.image(char_portrait, width=150, caption=f"🎭 {char['name']}")
                    except Exception:
                        # Fallback si l'URL est invalide
                        st.image(
                            f"https://api.dicebear.com/7.x/adventurer/png?seed={char['name']}&size=128",
                            width=120,
                            caption=f"🎭 {char['name']} (placeholder)",
                        )
                else:
                    st.image(
                        f"https://api.dicebear.com/7.x/adventurer/png?seed={char['name']}&size=128",
                        width=120,
                        caption=f"🎭 {char['name']} (placeholder)",
                    )
            else:
                st.warning("⚠️ Aucun personnage sélectionné")

        st.divider()

        # Génération différée du portrait si marqué en attente (background-like)
        try:
            pending = st.session_state.get("pending_portrait")
            if pending:
                with st.spinner("🎨 Génération du portrait en arrière-plan..."):
                    import time

                    from src.ai.portraits import PortraitGenerator
                    from src.analytics.performance import store_performance

                    start = time.time()

                    # Utiliser la nouvelle méthode enrichie pour générer le portrait
                    url = PortraitGenerator.generate_character_portrait_with_save(
                        name=pending["name"],
                        character_id=pending["character_id"],
                        race=pending["race"],
                        char_class=pending["char_class"],
                        level=pending["level"],
                        gender=pending["gender"],
                        description=None,  # Utilise les infos automatiques
                        art_style=pending["style"],
                        mood=pending["mood"],
                        campaign_context=pending["campaign_context"],
                    )

                    latency = time.time() - start

                    # Enregistrer les performances
                    try:
                        # Utiliser dall-e-3 comme modèle par défaut pour les stats
                        used_model = "dall-e-3" if url and not url.startswith("https://api.dicebear.com") else "template"
                        store_performance(
                            st.session_state.user["id"],
                            used_model,
                            latency,
                            0,
                            0,
                            pending["campaign_id"],
                        )
                    except Exception:
                        pass
                # Nettoyer l'état après génération
                del st.session_state["pending_portrait"]
        except Exception:
            pass

        # Interface de chat principale sous les cartes (input doit rester en bas)
        launch_chat_interface(st.session_state.user["id"])

    with tab2:
        # Performances de l'utilisateur
        from src.analytics.performance import show_performance

        show_performance(st.session_state.user["id"])

    with tab3:
        # Paramètres spécifiques au chatbot
        st.subheader("⚙️ Paramètres de Session")

        # Gestion des données de session avec recovery
        st.markdown("### 🗑️ Gestion des Données")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Nouvelle Aventure", help="Efface l'historique du chat actuel", use_container_width=True):
                if "history" in st.session_state:
                    del st.session_state["history"]
                st.success("✅ Historique réinitialisé !")
                st.rerun()

        with col2:
            if st.button(
                "🔄 Récupérer Discussion", help="Recharge la dernière conversation depuis la base", use_container_width=True
            ):
                try:
                    # Recharger les messages depuis la base de données
                    campaign_id = st.session_state.get("campaign", {}).get("id")
                    if campaign_id:
                        messages = get_campaign_messages(st.session_state.user["id"], campaign_id, limit=50)
                        if messages:
                            # Convertir en format d'historique
                            history = []
                            for msg in messages:
                                role = "user" if msg.get("role") == "user" else "assistant"
                                history.append({"role": role, "content": msg.get("content", "")})
                            st.session_state.history = history
                            st.success(f"✅ {len(messages)} messages récupérés !")
                        else:
                            st.info("ℹ️ Aucune conversation précédente trouvée")
                    else:
                        st.warning("⚠️ Aucune campagne active")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la récupération : {e}")
                st.rerun()

        with col3:
            if st.button("� Changer Personnage", help="Retour à la gestion des personnages", use_container_width=True):
                st.session_state.page = "character"
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
