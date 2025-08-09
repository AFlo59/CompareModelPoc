"""
Page de gestion des campagnes
"""

from typing import List

import streamlit as st

from src.ai.portraits import generate_gm_portrait
from src.auth.auth import require_auth
from src.data.models import PerformanceManager, create_campaign, get_user_campaigns, update_campaign_portrait


def show_campaign_page() -> None:
    """Page dédiée à la gestion des campagnes."""
    if not require_auth():
        return

    st.title("🏕️ Gestion des Campagnes")

    # Bouton retour au dashboard - TOUJOURS accessible
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🏠 Retour au tableau de bord", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.divider()

    # Récupération des campagnes existantes
    user_id = st.session_state.user["id"]

    try:
        campaigns = get_user_campaigns(user_id)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des campagnes : {e}")
        campaigns = []

    # Section : Mes campagnes existantes
    if campaigns:
        st.subheader("📚 Mes Campagnes")

        for campaign in campaigns:
            with st.expander(f"🎲 {campaign.get('name', 'Campagne sans nom')}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Thèmes :** {campaign.get('themes', 'Non défini')}")
                with col2:
                    st.write(f"**Langue :** {campaign.get('language', 'Non défini')}")
                with col3:
                    if st.button(f"🚀 Jouer", key=f"play_{campaign['id']}"):
                        st.session_state.selected_campaign = campaign["id"]
                        st.session_state.page = "chatbot"
                        st.rerun()

        st.divider()

    # Section : Créer une nouvelle campagne
    st.subheader("➕ Créer une Nouvelle Campagne")

    with st.form("create_campaign_form"):
        # Nom de la campagne
        campaign_name = st.text_input(
            "🏷️ Nom de la campagne", placeholder="Ma Campagne Épique", help="Donnez un nom mémorable à votre campagne"
        )

        # Thèmes
        col1, col2 = st.columns(2)

        with col1:
            primary_theme = st.selectbox(
                "🎭 Thème principal",
                ["Fantasy", "Science-Fiction", "Horror", "Moderne", "Post-Apocalyptique", "Steampunk", "Cyberpunk"],
                help="Le thème principal de votre campagne",
            )

        with col2:
            secondary_themes = st.multiselect(
                "🎨 Thèmes secondaires (optionnel)",
                ["Aventure", "Mystère", "Romance", "Politique", "Guerre", "Exploration", "Magie", "Technologie"],
                help="Thèmes additionnels pour enrichir votre campagne",
            )

        # Langue, modèle IA et style
        col1, col2, col3 = st.columns(3)

        with col1:
            language = st.selectbox(
                "🌍 Langue", ["Français", "English", "Español", "Deutsch"], help="Langue principale pour la narration"
            )

        with col2:
            ai_model = st.selectbox(
                "🤖 Modèle IA du Maître de Jeu",
                ["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"],
                help="Le modèle IA qui gérera le chat et la narration",
            )

        with col3:
            tone = st.selectbox(
                "🎪 Ton de la campagne",
                ["Épique", "Sombre", "Léger", "Humoristique", "Sérieux", "Dramatique"],
                help="L'ambiance générale de votre campagne",
            )

        # Description
        description = st.text_area(
            "📝 Description (optionnel)",
            placeholder="Décrivez l'univers, l'histoire de fond, les enjeux...",
            help="Plus de détails aideront l'IA à créer une meilleure expérience",
        )

        # Options avancées pour l'image du MJ (mêmes options que le portrait personnage)
        with st.expander("🎨 Options du portrait du Maître de Jeu"):
            gm_art_style = st.selectbox(
                "🖼️ Style artistique du portrait (MJ)",
                [
                    "Fantasy Réaliste",
                    "Anime/Manga",
                    "Art Conceptuel",
                    "Peinture Classique",
                    "Illustration Moderne",
                ],
                help="Style pour la génération du portrait du MJ",
            )
            gm_expression = st.selectbox(
                "😊 Expression/Humeur (MJ)",
                ["Neutre", "Déterminé", "Mystérieux", "Jovial", "Sombre", "Heroïque", "Sage"],
                help="Expression générale du MJ",
            )

        # Bouton de création
        submitted = st.form_submit_button("🚀 Créer la Campagne", use_container_width=True)

        if submitted:
            if not campaign_name.strip():
                st.error("❌ Le nom de la campagne est obligatoire !")
            else:
                try:
                    # Combiner les thèmes
                    all_themes = [primary_theme] + secondary_themes
                    if tone not in all_themes:
                        all_themes.append(tone)

                    with st.spinner("🏕️ Création de la campagne et génération du portrait du MJ..."):
                        # Créer la campagne avec le modèle IA
                        campaign_id = create_campaign(
                            user_id=user_id,
                            name=campaign_name.strip(),
                            themes=all_themes,
                            language=language,
                            ai_model=ai_model,  # Nouveau paramètre
                        )

                        st.success(f"✅ Campagne '{campaign_name}' créée avec succès !")

                        # Générer le portrait du Maître de Jeu
                        try:
                            st.info("🎨 Génération du portrait du Maître de Jeu...")

                            # Préparer le thème pour le portrait
                            main_theme = primary_theme.lower()
                            import time

                            start = time.time()
                            gm_portrait_url = generate_gm_portrait(
                                campaign_theme=main_theme,
                                campaign_name=campaign_name.strip() or None,
                                secondary_themes=secondary_themes or None,
                                tone=tone,
                                language=language,
                                model_name=ai_model,
                                expression=gm_expression,
                                art_style=gm_art_style,
                                campaign_description=(description or None),
                            )
                            latency = time.time() - start

                            if gm_portrait_url:
                                st.success("🎨 Portrait du Maître de Jeu généré !")
                                st.image(gm_portrait_url, width=200, caption="Votre Maître de Jeu")

                                # Sauvegarder l'URL du portrait dans la campagne
                                if update_campaign_portrait(campaign_id, gm_portrait_url):
                                    st.success("💾 Portrait du MJ sauvegardé !")
                                else:
                                    st.warning("⚠️ Portrait généré mais erreur de sauvegarde")
                            else:
                                st.warning("⚠️ Impossible de générer le portrait du MJ (clé API manquante?)")

                        except Exception as e:
                            st.warning(f"⚠️ Erreur lors de la génération du portrait du MJ : {e}")
                        finally:
                            try:
                                # Traquer la génération d'image dans les performances (0 tokens, modèle DALL-E 3)
                                PerformanceManager.store_performance(
                                    user_id=user_id,
                                    model="DALL-E 3",
                                    latency=latency if "latency" in locals() else 0.0,
                                    tokens_in=0,
                                    tokens_out=0,
                                    campaign_id=campaign_id,
                                    cost_estimate=None,
                                )
                            except Exception:
                                pass

                        # Redirection vers la création de personnage
                        st.success("🧙‍♂️ **Prochaine étape :** Créez votre personnage !")
                        st.info(f"**Modèle sélectionné :** {ai_model} gérera votre aventure")

                        # Sauvegarder l'ID de la campagne pour la création de personnage
                        st.session_state.selected_campaign = campaign_id

                        # Petite pause puis redirection vers création personnage
                        import time

                        time.sleep(3)
                        st.session_state.page = "character"
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur lors de la création : {e}")
                    st.warning("💡 **Conseil :** Essayez de rafraîchir la page")

    # Section aide
    st.divider()
    st.markdown("### 💡 Conseils pour créer une bonne campagne")

    st.markdown(
        """
    - **🎯 Nom évocateur** : Choisissez un nom qui inspire l'aventure
    - **🎭 Thèmes cohérents** : Mélangez les thèmes avec parcimonie
    - **📝 Description détaillée** : Plus vous donnez d'infos, mieux l'IA comprendra votre vision
    - **🌍 Langue** : Assurez-vous que tous les joueurs parlent la langue choisie
    """
    )
