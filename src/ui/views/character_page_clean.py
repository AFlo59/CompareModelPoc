import base64
import io
from typing import Optional

import requests
import streamlit as st
from PIL import Image

from ...ai.portraits import generate_character_portrait
from ...database import create_user_with_character, get_campaign_details, get_database_session


def show_character_page():
    """Page de création de personnage."""
    st.title("🎭 Création de Personnage")

    if "user_id" not in st.session_state or not st.session_state.user_id:
        st.error("❌ Veuillez vous connecter pour créer un personnage")
        return

    user_id = st.session_state.user_id

    # Formulaire de création de personnage
    with st.form("character_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("🏷️ Nom du personnage *", placeholder="Ex: Aragorn")
            race = st.selectbox(
                "🧝 Race *",
                ["Humain", "Elfe", "Nain", "Halfelin", "Demi-Elfe", "Demi-Orque", "Gnome", "Tieffelin", "Drakéide"],
            )
            char_class = st.selectbox(
                "⚔️ Classe *",
                [
                    "Guerrier",
                    "Mage",
                    "Voleur",
                    "Clerc",
                    "Ranger",
                    "Paladin",
                    "Barbare",
                    "Barde",
                    "Druide",
                    "Sorcier",
                    "Warlock",
                    "Moine",
                ],
            )

        with col2:
            level = st.number_input("🎯 Niveau", min_value=1, max_value=20, value=1)
            campaign_id = st.selectbox(
                "📚 Campagne *",
                options=[] if "campaigns" not in st.session_state else [c["id"] for c in st.session_state.campaigns],
                format_func=lambda x: next((c["title"] for c in st.session_state.get("campaigns", []) if c["id"] == x), "")
                if x
                else "Sélectionner une campagne",
                index=None,
            )

        description = st.text_area(
            "📝 Description du personnage *",
            placeholder="Décrivez l'apparence, la personnalité, l'histoire de votre personnage...",
            height=150,
        )

        art_style = st.selectbox(
            "🎨 Style artistique du portrait",
            ["fantasy", "realistic", "anime", "cartoon", "digital_art"],
            format_func=lambda x: {
                "fantasy": "🧙 Fantasy classique",
                "realistic": "📸 Réaliste",
                "anime": "🎌 Anime/Manga",
                "cartoon": "🎨 Cartoon",
                "digital_art": "💻 Art numérique",
            }.get(x, x),
        )

        submitted = st.form_submit_button("🎭 Créer le Personnage", use_container_width=True)

        if submitted:
            # Validation
            if not all([name, race, char_class, description, campaign_id]):
                st.error("❌ Veuillez remplir tous les champs obligatoires")
                return

            # Vérifier que la campagne existe
            with get_database_session() as session:
                campaign_details = get_campaign_details(session, campaign_id)
                if not campaign_details:
                    st.error("❌ Campagne sélectionnée invalide")
                    return

            # Afficher le progrès
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Étape 1: Création du personnage
                status_text.text("🎭 Création du personnage...")
                progress_bar.progress(25)

                character_data = {
                    "name": name,
                    "race": race,
                    "char_class": char_class,
                    "level": level,
                    "description": description,
                    "campaign_id": campaign_id,
                    "art_style": art_style,
                }

                # Étape 2: Génération du portrait
                status_text.text("🎨 Génération du portrait...")
                progress_bar.progress(50)

                portrait_url = None
                try:
                    portrait_url = generate_character_portrait(character_data)
                    if portrait_url:
                        character_data["portrait_url"] = portrait_url
                        status_text.text("✅ Portrait généré avec succès!")
                    else:
                        status_text.text("⚠️ Portrait par défaut utilisé")
                except Exception as e:
                    st.warning(f"⚠️ Impossible de générer le portrait: {e}")
                    status_text.text("⚠️ Portrait par défaut utilisé")

                progress_bar.progress(75)

                # Étape 3: Sauvegarde en base
                status_text.text("💾 Sauvegarde du personnage...")

                with get_database_session() as session:
                    character_id = create_user_with_character(session, user_id, character_data, campaign_id)

                    if character_id:
                        # Étape 4: Préparation de l'initialisation
                        progress_bar.progress(90)
                        status_text.text("⚙️ Préparation de l'aventure...")

                        # Stocker les infos nécessaires pour l'initialisation
                        st.session_state.selected_character_id = character_id
                        st.session_state.selected_campaign_id = campaign_id
                        st.session_state.character_name = name
                        st.session_state.campaign_title = campaign_details.get("title", "")

                        # Préparer l'introduction automatique
                        intro = f"Je suis {name}, {race} {char_class} de niveau {level}. {description}"
                        st.session_state.character_intro = intro
                        st.session_state.auto_start_intro = True

                        # Persister l'initialisation en base
                        try:
                            from ...ai.chatbot import store_message_optimized

                            system_content = (
                                "Tu es un MJ immersif, concis quand nécessaire, et tu avances l'histoire scène par scène."
                            )
                            store_message_optimized(user_id, "system", system_content, campaign_id)
                            store_message_optimized(user_id, "user", intro, campaign_id)
                        except Exception:
                            pass  # Ne pas bloquer si échec de persistance

                        # Finalisation
                        progress_bar.progress(100)
                        status_text.text("🎉 Personnage créé avec succès!")

                        # Afficher le portrait si généré
                        if portrait_url:
                            st.success("🎨 Portrait généré avec succès!")
                            try:
                                if portrait_url.startswith(("http://", "https://")):
                                    response = requests.get(portrait_url, timeout=10)
                                    if response.status_code == 200:
                                        image = Image.open(io.BytesIO(response.content))
                                        st.image(image, caption=f"Portrait de {name}", width=300)
                                elif portrait_url.startswith("data:image"):
                                    st.image(portrait_url, caption=f"Portrait de {name}", width=300)
                            except Exception:
                                pass

                        # Redirection automatique vers le chatbot
                        st.success(f"🎭 Personnage **{name}** créé avec succès!")
                        st.info("🚀 Redirection vers l'aventure...")

                        # Petit délai pour que l'utilisateur voie le succès
                        import time

                        time.sleep(2)

                        # Redirection
                        st.session_state.page = "chatbot"
                        st.rerun()

                    else:
                        st.error("❌ Erreur lors de la création du personnage")

            except Exception as e:
                st.error(f"❌ Erreur lors de la création : {e}")
                st.warning("💡 **Conseil :** Essayez de rafraîchir la page")

    # Section aide
    st.divider()
    st.markdown("### 💡 Conseils pour créer un bon personnage")

    st.markdown(
        """
    - **🎭 Nom évocateur** : Choisissez un nom qui correspond à la race et au monde
    - **📝 Description détaillée** : Plus vous donnez de détails, plus le portrait sera précis
    - **🏕️ Cohérence** : Assurez-vous que votre personnage correspond à l'univers de la campagne
    - **🎨 Style artistique** : Choisissez un style qui vous plaît pour le portrait
    - **⚔️ Classe appropriée** : Réfléchissez au rôle que vous voulez jouer dans l'aventure
    """
    )
