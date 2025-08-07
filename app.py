import logging
from typing import Any, Dict, Optional

import streamlit as st

from auth import get_current_user, login, logout, register_user, require_auth
from chatbot import launch_chat_interface
from database import init_db
from models import (
    create_campaign,
    create_character,
    get_campaign_messages,
    get_user_campaigns,
    get_user_model_choice,
    save_model_choice,
)
from portraits import generate_portrait

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(page_title="DnD AI GameMaster", page_icon="🎲", layout="wide", initial_sidebar_state="expanded")

# CSS personnalisé
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


def initialize_app() -> None:
    """Initialise l'application et la base de données."""
    try:
        init_db()
        logger.info("Application initialisée avec succès")
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation: {e}")
        logger.error(f"Erreur initialisation: {e}")
        st.stop()


def determine_user_next_page(user_id: int) -> str:
    """Détermine la prochaine page à afficher selon l'état de l'utilisateur."""
    try:
        # Toujours aller au dashboard après connexion pour laisser le choix à l'utilisateur
        return "dashboard"

    except Exception as e:
        logger.error(f"Erreur lors de la détermination de la prochaine page: {e}")
        return "dashboard"  # Fallback sécurisé vers le dashboard


def show_auth_page() -> None:
    """Affiche la page d'authentification."""
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
                # Redirection intelligente selon l'état de l'utilisateur
                next_page = determine_user_next_page(user["id"])
                st.session_state.page = next_page
                st.rerun()
        else:
            register_user()


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
                    except:
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


def show_performance_page() -> None:
    """Page dédiée aux performances."""
    if not require_auth():
        return

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.divider()

    from performance import show_performance

    show_performance(st.session_state.user["id"])


def show_settings_page() -> None:
    """Page dédiée aux paramètres globaux de l'application."""
    if not require_auth():
        return

    st.title("⚙️ Paramètres de l'application")

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.divider()

    # Informations utilisateur
    st.markdown("### 👤 Informations du compte")
    user_email = st.session_state.user.get("email", "Non défini")
    st.info(f"**Email :** {user_email}")

    # Statistiques globales
    try:
        campaigns = get_user_campaigns(st.session_state.user["id"])
        total_campaigns = len(campaigns)
        total_messages = sum(camp.get("message_count", 0) for camp in campaigns)
    except:
        total_campaigns = 0
        total_messages = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 Campagnes créées", total_campaigns)
    with col2:
        st.metric("💬 Messages totaux", total_messages)
    with col3:
        current_model = get_user_model_choice(st.session_state.user["id"])
        st.metric("🤖 Modèle préféré", current_model or "Non défini")

    st.divider()

    # Préférences par défaut
    st.markdown("### 🎯 Préférences par défaut")

    # Choix du modèle par défaut
    st.markdown("**Modèle IA par défaut pour les nouvelles campagnes :**")
    model_info = {
        "GPT-4": "� Le plus avancé, créatif et précis",
        "GPT-4o": "⚡ Optimisé, rapide et économique",
        "Claude 3.5 Sonnet": "🎭 Excellent pour le roleplay et la narration",
        "DeepSeek": "💰 Le plus économique, bon rapport qualité/prix",
    }

    current_model = get_user_model_choice(st.session_state.user["id"]) or "GPT-4o"
    new_model = st.selectbox(
        "Choisir le modèle par défaut",
        options=list(model_info.keys()),
        index=list(model_info.keys()).index(current_model) if current_model in model_info else 1,
        format_func=lambda x: f"{x} - {model_info[x]}",
        help="Ce modèle sera automatiquement sélectionné lors de la création de nouvelles campagnes",
    )

    if st.button("💾 Sauvegarder les préférences"):
        try:
            save_model_choice(st.session_state.user["id"], new_model)
            st.success(f"✅ Modèle par défaut mis à jour : {new_model}")
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde : {e}")

    st.divider()

    # Actions avancées (uniquement si on a des campagnes)
    if total_campaigns > 0:
        st.markdown("### 🗑️ Gestion des données")
        st.warning("⚠️ Actions avancées - Utilisez avec précaution")

        if st.button(
            "🔄 Nouvelle aventure dans la campagne actuelle", help="Efface l'historique du chat de la campagne en cours"
        ):
            if "history" in st.session_state:
                del st.session_state["history"]
            st.success("✅ Historique de la campagne actuelle réinitialisé !")
            st.rerun()
    else:
        st.info("ℹ️ Créez votre première campagne pour accéder aux options avancées !")

    st.divider()

    # Section aide
    st.markdown("### ❓ Aide et support")
    st.markdown(
        """
    **� Comment utiliser l'application :**
    1. **Créez une campagne** avec votre univers et thèmes préférés
    2. **Créez votre personnage** avec ses caractéristiques
    3. **Lancez l'aventure** et laissez l'IA vous guider
    4. **Analysez vos parties** avec les statistiques de performance
    
    **🤖 Modèles IA disponibles :**
    - **GPT-4** : Le plus performant pour des histoires complexes
    - **GPT-4o** : Équilibré entre performance et rapidité
    - **Claude 3.5 Sonnet** : Excellent pour le roleplay immersif
    - **DeepSeek** : Économique pour de longues sessions
    """
    )

    st.divider()

    # Actions de session
    st.markdown("### 🚪 Session")
    if st.button("🔓 Se déconnecter", use_container_width=True):
        logout()


def show_campaign_or_resume_page() -> None:
    """Affiche toutes les campagnes disponibles avec détails."""
    if not require_auth():
        return

    st.title("📚 Toutes vos campagnes")

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

    # Bouton pour créer une nouvelle campagne
    if st.button("🆕 Créer une nouvelle campagne", use_container_width=True, type="primary"):
        st.session_state.page = "campaign"
        st.rerun()

    st.divider()

    try:
        campaigns = get_user_campaigns(st.session_state.user["id"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des campagnes: {e}")
        campaigns = []

    if campaigns:
        st.subheader(f"📋 {len(campaigns)} campagne(s) disponible(s)")

        # Affichage des campagnes existantes avec informations détaillées
        for i, campaign in enumerate(campaigns):
            with st.container():
                # CSS pour les cartes de campagne
                st.markdown(
                    f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                    color: white;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                ">
                    <h3 style="margin: 0 0 10px 0; color: white;">🏰 {campaign['name']}</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">
                        <div><strong>🌍 Langue:</strong> {campaign['language']}</div>
                        <div><strong>🎭 Thèmes:</strong> {', '.join(campaign['themes']) if campaign['themes'] else 'Aucun'}</div>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9em; opacity: 0.9;">
                        <div><strong>💬 Messages:</strong> {campaign['message_count']}</div>
                        <div><strong>⏰ Dernière activité:</strong> {campaign['last_activity'][:10] if campaign['last_activity'] else 'Jamais'}</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                col1, col2, col3 = st.columns([2, 1, 1])
                with col2:
                    if st.button(f"🎮 Reprendre", key=f"resume_{i}", use_container_width=True):
                        # Charger la campagne et son historique
                        st.session_state.campaign = campaign

                        # Charger l'historique des messages de cette campagne
                        try:
                            messages = get_campaign_messages(st.session_state.user["id"], campaign["id"])
                            st.session_state.history = messages
                            st.success(f"📖 Campagne '{campaign['name']}' chargée avec {len(messages)} messages!")
                        except Exception as e:
                            st.error(f"Erreur lors du chargement: {e}")
                            st.session_state.history = []

                        # Aller directement au chatbot si on a déjà des messages
                        if st.session_state.history:
                            st.session_state.page = "chatbot"
                        else:
                            st.session_state.page = "character"
                        st.rerun()
                with col3:
                    if st.button(f"🗑️ Supprimer", key=f"delete_{i}", use_container_width=True):
                        # Ici on pourrait ajouter une confirmation de suppression
                        st.warning("⚠️ Suppression de campagne - fonctionnalité à implémenter")

            st.divider()
    else:
        st.info("🗂️ Aucune campagne trouvée. Créons votre première aventure !")
        if st.button("🚀 Créer ma première campagne"):
            st.session_state.page = "campaign"
            st.rerun()


def show_campaign_creation_page() -> None:
    """Affiche la page de création de campagne."""
    if not require_auth():
        return

    st.title("📌 Créez votre Campagne")

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.divider()

    with st.form("campaign_form"):
        name = st.text_input("🏷️ Nom de la campagne", placeholder="Ex: Les Mystères d'Eldoria")

        themes = st.multiselect(
            "🎨 Thèmes",
            ["Fantasy", "Horreur", "Science-Fiction", "Mystère", "Aventure", "Politique", "Romance"],
            help="Sélectionnez les thèmes qui définiront l'ambiance de votre campagne",
        )

        lang = st.selectbox("🌍 Langue", ["fr", "en"], index=0)

        # Ajout du choix du modèle IA
        st.markdown("### 🧠 Choisissez votre Modèle IA")
        model_info = {
            "GPT-4": "🚀 Le plus avancé, créatif et précis",
            "GPT-4o": "⚡ Optimisé, rapide et économique",
            "Claude 3.5 Sonnet": "🎭 Excellent pour le roleplay et la narration",
            "DeepSeek": "💰 Le plus économique, bon rapport qualité/prix",
        }

        model = st.selectbox(
            "Modèle LLM",
            options=list(model_info.keys()),
            format_func=lambda x: f"{x} - {model_info[x]}",
            help="Le modèle choisi sera utilisé pour cette campagne",
        )

        description = st.text_area(
            "📝 Description (optionnelle)", placeholder="Décrivez brièvement l'univers ou l'intrigue de votre campagne..."
        )

        submitted = st.form_submit_button("🎯 Créer la campagne")

        if submitted:
            if not name.strip():
                st.error("Le nom de la campagne est obligatoire.")
            else:
                try:
                    # Sauvegarder le choix du modèle
                    save_model_choice(st.session_state.user["id"], model)

                    # Génération automatique du portrait du MJ
                    gm_portrait_url = None
                    with st.spinner("🎨 Génération du portrait du Maître du Jeu..."):
                        gm_description = f"Maître du Jeu pour {name.strip()}, univers {', '.join(themes) if themes else 'fantastique'}, sage et mystérieux"
                        gm_portrait_url = generate_portrait("Maître du Jeu", gm_description)
                        if gm_portrait_url:
                            st.success("✅ Portrait du MJ généré !")

                    campaign_id = create_campaign(st.session_state.user["id"], name.strip(), themes, lang, gm_portrait_url)
                    st.session_state.campaign = {
                        "id": campaign_id,
                        "name": name.strip(),
                        "themes": themes,
                        "language": lang,
                        "description": description,
                        "gm_portrait": gm_portrait_url,
                    }
                    st.success(f"✅ Campagne '{name}' créée avec modèle {model} !")
                    st.session_state.page = "character"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création: {e}")


def show_character_creation_page() -> None:
    """Affiche la page de création de personnage."""
    if not require_auth():
        return

    st.title("🧙 Créez votre Personnage")

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("character_form"):
            name = st.text_input("👤 Nom du personnage", placeholder="Ex: Arwen Lameargent")

            col_a, col_b = st.columns(2)
            with col_a:
                classe = st.selectbox(
                    "⚔️ Classe",
                    ["Guerrier", "Magicien", "Voleur", "Clerc", "Paladin", "Rôdeur", "Barde", "Barbare", "Sorcier", "Druide"],
                )
                race = st.selectbox(
                    "🧬 Race", ["Humain", "Elfe", "Nain", "Orc", "Demi-elfe", "Halfelin", "Tieffelin", "Gnome", "Dragonide"]
                )
            with col_b:
                gender = st.selectbox("👥 Genre", ["Homme", "Femme", "Non-binaire"])
                age = st.number_input("🎂 Âge", min_value=16, max_value=1000, value=25)

            description = st.text_area(
                "📝 Description physique",
                placeholder="Ex: Grand elfe aux cheveux argentés, porte une armure en cuir noir ornée de runes...",
                help="Cette description sera utilisée pour générer le portrait",
            )

            submitted = st.form_submit_button("✨ Créer le personnage")

        # Bouton séparé pour le portrait
        if st.button("🎨 Générer le portrait"):
            if name.strip():
                with st.spinner("🎨 Génération du portrait en cours..."):
                    portrait_url = generate_portrait(name.strip(), description.strip() if description else None)
                    if portrait_url:
                        st.session_state.portrait_url = portrait_url
                        st.success("✅ Portrait généré avec succès !")
                        st.rerun()
                    else:
                        st.warning("⚠️ Échec de génération du portrait. Vous pourrez continuer sans portrait.")
            else:
                st.error("Veuillez d'abord saisir un nom pour le personnage.")

        if submitted:
            if not all([name.strip(), classe, race]):
                st.error("Les champs nom, classe et race sont obligatoires.")
            else:
                try:
                    # Génération automatique du portrait s'il n'existe pas
                    portrait_url = st.session_state.get("portrait_url")
                    if not portrait_url:
                        with st.spinner("🎨 Génération automatique du portrait..."):
                            portrait_url = generate_portrait(
                                name.strip(),
                                f"{classe} {race}, {description.strip() if description else 'personnage fantastique'}",
                            )
                            if portrait_url:
                                st.session_state.portrait_url = portrait_url
                                st.success("✅ Portrait généré automatiquement !")

                    character_id = create_character(
                        st.session_state.user["id"],
                        name.strip(),
                        classe,
                        race,
                        description.strip() if description else None,
                        portrait_url,
                    )

                    st.session_state.character = {
                        "id": character_id,
                        "name": name.strip(),
                        "class": classe,
                        "race": race,
                        "gender": gender,
                        "age": age,
                        "description": description.strip() if description else None,
                        "portrait": portrait_url,
                    }

                    st.success(f"✅ Personnage '{name}' créé avec succès !")
                    st.session_state.page = "chatbot"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création: {e}")

    with col2:
        st.subheader("🖼️ Aperçu")
        if st.session_state.get("portrait_url"):
            st.image(st.session_state.portrait_url, caption="Portrait généré", width=300)
        else:
            st.info("Aucun portrait généré pour le moment.")


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
        from performance import show_performance

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


def main() -> None:
    """Fonction principale de l'application."""
    # Initialisation
    initialize_app()

    # Gestion du state de navigation
    if "page" not in st.session_state:
        st.session_state.page = "auth"

    # Routage des pages
    page_functions = {
        "auth": show_auth_page,
        "dashboard": show_dashboard_page,
        "campaign_or_resume": show_campaign_or_resume_page,
        "campaign": show_campaign_creation_page,
        "character": show_character_creation_page,
        "chatbot": show_chatbot_page,
        "performance": show_performance_page,
        "settings": show_settings_page,
    }

    current_page = st.session_state.page
    if current_page in page_functions:
        try:
            page_functions[current_page]()
        except Exception as e:
            st.error(f"❌ Erreur dans la page {current_page}: {e}")
            logger.error(f"Erreur page {current_page}: {e}")
    else:
        st.error(f"Page inconnue: {current_page}")
        st.session_state.page = "auth"
        st.rerun()


if __name__ == "__main__":
    main()
