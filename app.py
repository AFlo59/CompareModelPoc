import streamlit as st
import logging
from typing import Dict, Any, Optional
from auth import login, register_user, get_current_user, logout, require_auth
from database import init_db
from models import get_user_campaigns, save_model_choice, create_campaign, create_character
from chatbot import launch_chat_interface
from portraits import generate_portrait

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="DnD AI GameMaster",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
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
    }
    .campaign-info {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

def initialize_app() -> None:
    """Initialise l'application et la base de données."""
    try:
        init_db()
        logger.info("Application initialisée avec succès")
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation: {e}")
        logger.error(f"Erreur initialisation: {e}")
        st.stop()

def show_auth_page() -> None:
    """Affiche la page d'authentification."""
    st.markdown('<div class="main-header"><h1>🎲 DnD AI GameMaster</h1><p>Votre assistant IA pour des aventures épiques</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        auth_choice = st.radio(
            "Choisissez une action",
            ["🔑 Connexion", "🆕 Créer un compte"],
            horizontal=True
        )

        if auth_choice == "🔑 Connexion":
            user = login()
            if user:
                st.session_state.user = user
                st.session_state.page = 'choose_model'
                st.rerun()
        else:
            register_user()

def show_model_choice_page() -> None:
    """Affiche la page de choix du modèle IA."""
    if not require_auth():
        return
        
    st.title("🧠 Choisissez votre Modèle IA")
    
    # Information sur les modèles
    model_info = {
        "GPT-4": "🚀 Le plus avancé, créatif et précis",
        "GPT-4o": "⚡ Optimisé, rapide et économique",
        "Claude 3.5 Sonnet": "🎭 Excellent pour le roleplay et la narration",
        "DeepSeek": "💰 Le plus économique, bon rapport qualité/prix"
    }
    
    st.markdown("### 🎯 Choisissez le modèle qui correspond à votre style de jeu :")
    
    model = st.selectbox(
        "Modèle LLM",
        options=list(model_info.keys()),
        format_func=lambda x: f"{x} - {model_info[x]}"
    )
    
    # Affichage des détails du modèle sélectionné
    st.info(f"**{model}** : {model_info[model]}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ Valider le modèle", use_container_width=True):
            try:
                save_model_choice(st.session_state.user["id"], model)
                st.success(f"Modèle {model} sélectionné !")
                st.session_state.page = 'campaign_or_resume'
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde: {e}")

def show_campaign_or_resume_page() -> None:
    """Affiche la page de choix entre créer ou reprendre une campagne."""
    if not require_auth():
        return
        
    st.title("📚 Reprendre ou créer une campagne")
    
    try:
        campaigns = get_user_campaigns(st.session_state.user["id"])
    except Exception as e:
        st.error(f"Erreur lors du chargement des campagnes: {e}")
        campaigns = []

    if campaigns:
        choice = st.radio(
            "Souhaitez-vous :",
            ["🆕 Créer une nouvelle campagne", "📖 Reprendre une campagne existante"]
        )
        
        if choice == "🆕 Créer une nouvelle campagne":
            st.session_state.page = 'campaign'
            st.rerun()
        else:
            st.subheader("📋 Campagnes disponibles")
            
            # Affichage des campagnes existantes
            for i, campaign in enumerate(campaigns):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="campaign-info">
                            <h4>{campaign['name']}</h4>
                            <p><strong>Langue:</strong> {campaign['language']}</p>
                            <p><strong>Thèmes:</strong> {', '.join(campaign['themes'])}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button(f"🎮 Charger", key=f"load_{i}"):
                            st.session_state.campaign = campaign
                            st.session_state.page = 'character'
                            st.rerun()
    else:
        st.info("🗂️ Aucune campagne trouvée. Créons votre première aventure !")
        if st.button("🚀 Créer ma première campagne"):
            st.session_state.page = 'campaign'
            st.rerun()

def show_campaign_creation_page() -> None:
    """Affiche la page de création de campagne."""
    if not require_auth():
        return
        
    st.title("📌 Créez votre Campagne")
    
    with st.form("campaign_form"):
        name = st.text_input("🏷️ Nom de la campagne", placeholder="Ex: Les Mystères d'Eldoria")
        
        themes = st.multiselect(
            "🎨 Thèmes",
            ["Fantasy", "Horreur", "Science-Fiction", "Mystère", "Aventure", "Politique", "Romance"],
            help="Sélectionnez les thèmes qui définiront l'ambiance de votre campagne"
        )
        
        lang = st.selectbox("🌍 Langue", ["fr", "en"], index=0)
        
        description = st.text_area(
            "📝 Description (optionnelle)",
            placeholder="Décrivez brièvement l'univers ou l'intrigue de votre campagne..."
        )
        
        submitted = st.form_submit_button("🎯 Créer la campagne")
        
        if submitted:
            if not name.strip():
                st.error("Le nom de la campagne est obligatoire.")
            else:
                try:
                    campaign_id = create_campaign(st.session_state.user["id"], name.strip(), themes, lang)
                    st.session_state.campaign = {
                        "id": campaign_id,
                        "name": name.strip(),
                        "themes": themes,
                        "language": lang,
                        "description": description
                    }
                    st.success(f"✅ Campagne '{name}' créée avec succès !")
                    st.session_state.page = 'character'
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création: {e}")

def show_character_creation_page() -> None:
    """Affiche la page de création de personnage."""
    if not require_auth():
        return
        
    st.title("🧙 Créez votre Personnage")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("character_form"):
            name = st.text_input("👤 Nom du personnage", placeholder="Ex: Arwen Lameargent")
            
            col_a, col_b = st.columns(2)
            with col_a:
                classe = st.selectbox("⚔️ Classe", [
                    "Guerrier", "Magicien", "Voleur", "Clerc", "Paladin",
                    "Rôdeur", "Barde", "Barbare", "Sorcier", "Druide"
                ])
                race = st.selectbox("🧬 Race", [
                    "Humain", "Elfe", "Nain", "Orc", "Demi-elfe",
                    "Halfelin", "Tieffelin", "Gnome", "Dragonide"
                ])
            with col_b:
                gender = st.selectbox("👥 Genre", ["Homme", "Femme", "Non-binaire"])
                age = st.number_input("🎂 Âge", min_value=16, max_value=1000, value=25)
            
            description = st.text_area(
                "📝 Description physique",
                placeholder="Ex: Grand elfe aux cheveux argentés, porte une armure en cuir noir ornée de runes...",
                help="Cette description sera utilisée pour générer le portrait"
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
                    character_id = create_character(
                        st.session_state.user["id"],
                        name.strip(),
                        classe,
                        race,
                        description.strip() if description else None,
                        st.session_state.get("portrait_url")
                    )
                    
                    st.session_state.character = {
                        "id": character_id,
                        "name": name.strip(),
                        "class": classe,
                        "race": race,
                        "gender": gender,
                        "age": age,
                        "description": description.strip() if description else None,
                        "portrait": st.session_state.get("portrait_url")
                    }
                    
                    st.success(f"✅ Personnage '{name}' créé avec succès !")
                    st.session_state.page = 'chatbot'
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
        
        # Informations personnage
        st.markdown("### 🎭 Personnage")
        if "character" in st.session_state:
            char = st.session_state.character
            st.markdown(f"""
            <div class="character-card">
                <h4>{char['name']}</h4>
                <p><strong>{char['gender']} {char['race']} {char['class']}</strong></p>
                <p><em>{char.get('description', 'Aucune description')}</em></p>
            </div>
            """, unsafe_allow_html=True)
            
            if char.get("portrait"):
                st.image(char["portrait"], width=200)
        else:
            st.info("Aucun personnage sélectionné")

        st.divider()
        
        # Informations campagne
        st.markdown("### 📜 Campagne")
        if "campaign" in st.session_state:
            camp = st.session_state.campaign
            st.markdown(f"""
            <div class="campaign-info">
                <h4>{camp['name']}</h4>
                <p><strong>Langue:</strong> {camp['language']}</p>
                <p><strong>Thèmes:</strong> {', '.join(camp['themes'])}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Aucune campagne sélectionnée")

    # Navigation principale avec radio buttons
    st.markdown("### 🧭 Navigation")
    current_section = st.radio(
        "Choisissez une section :",
        ["🎲 Aventure", "📊 Performances", "⚙️ Paramètres"],
        horizontal=True
    )
    
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
                if 'history' in st.session_state:
                    del st.session_state['history']
                st.success("Historique réinitialisé !")
                st.rerun()
        
        with col2:
            if st.button("🎭 Changer de personnage", help="Retour à la création de personnage"):
                st.session_state.page = 'character'
                st.rerun()

def main() -> None:
    """Fonction principale de l'application."""
    # Initialisation
    initialize_app()
    
    # Gestion du state de navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'auth'

    # Routage des pages
    page_functions = {
        'auth': show_auth_page,
        'choose_model': show_model_choice_page,
        'campaign_or_resume': show_campaign_or_resume_page,
        'campaign': show_campaign_creation_page,
        'character': show_character_creation_page,
        'chatbot': show_chatbot_page
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
        st.session_state.page = 'auth'
        st.rerun()

if __name__ == "__main__":
    main()
