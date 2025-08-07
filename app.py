import streamlit as st
from auth import login, register_user, get_current_user
from database import init_db
from models import get_user_campaigns
from chatbot import launch_chat_interface
from portraits import generate_portrait

st.set_page_config(page_title="DnD AI GameMaster", layout="wide")

init_db()

# Session state for auth and flow
if 'page' not in st.session_state:
    st.session_state.page = 'auth'

if st.session_state.page == 'auth':
    st.title("🔐 Connexion ou Création de Compte")
    auth_choice = st.radio("Action", ["Connexion", "Créer un compte"])

    if auth_choice == "Connexion":
        user = login()
        if user:
            st.session_state.user = user
            st.session_state.page = 'choose_model'
            st.rerun()
    else:
        register_user()

elif st.session_state.page == 'choose_model':
    from models import save_model_choice
    st.title("🧠 Choisissez votre Modèle IA")
    model = st.selectbox("Modèle LLM", ["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"])
    if st.button("Valider le modèle"):
        save_model_choice(st.session_state.user["id"], model)
        st.session_state.page = 'campaign_or_resume'
        st.rerun()

elif st.session_state.page == 'campaign_or_resume':
    st.title("📚 Reprendre ou créer une campagne")
    campaigns = get_user_campaigns(st.session_state.user["id"])

    if campaigns:
        choice = st.radio("Souhaitez-vous :", ["Créer une nouvelle campagne", "Reprendre une campagne existante"])
    else:
        st.info("Aucune campagne trouvée, création obligatoire.")
        choice = "Créer une nouvelle campagne"

    if choice == "Créer une nouvelle campagne":
        st.session_state.page = 'campaign'
        st.rerun()
    elif choice == "Reprendre une campagne existante":
        selected = st.selectbox("Choisissez une campagne :", [c['name'] for c in campaigns])
        if st.button("Charger cette campagne"):
            for c in campaigns:
                if c['name'] == selected:
                    st.session_state.campaign = c
                    break
            st.session_state.page = 'character'
            st.rerun()

elif st.session_state.page == 'campaign':
    from models import create_campaign
    st.title("📌 Créez votre Campagne")
    name = st.text_input("Nom de la campagne")
    themes = st.multiselect("Thèmes", ["Fantasy", "Horreur", "Science-Fiction", "Mystère"])
    lang = st.selectbox("Langue", ["fr", "en"])
    if st.button("Créer la campagne") and name:
        from models import get_user_campaigns
        create_campaign(st.session_state.user["id"], name, themes, lang)
        st.session_state.campaign = {"name": name, "themes": themes, "language": lang}
        st.session_state.page = 'character'
        st.rerun()

elif st.session_state.page == 'character':
    from models import create_character
    st.title("🧙 Créez votre Personnage")
    name = st.text_input("Nom du personnage")
    classe = st.selectbox("Classe", ["Guerrier", "Magicien", "Voleur", "Clerc", "Paladin"])
    race = st.selectbox("Race", ["Humain", "Elfe", "Nain", "Orc", "Demi-elfe"])
    gender = st.selectbox("Genre", ["Homme", "Femme"])
    description = st.text_area("Description physique", help="Ex: grand, cicatrice, armure en cuir... (facultatif)")
    portrait_url = None

    if st.button("Générer le portrait"):
        portrait_url = generate_portrait(name or "aventurier inconnu", description or "aucune description")
        if portrait_url:
            st.image(portrait_url, caption="Portrait généré", width=256)
            st.session_state.portrait_url = portrait_url
        else:
            st.warning("Échec de génération du portrait.")

    if st.button("Créer le personnage") and name and classe and race:
        create_character(st.session_state.user["id"], name, classe, race, description, st.session_state.get("portrait_url"))
        st.session_state.character = {
            "name": name,
            "class": classe,
            "race": race,
            "gender": gender,
            "description": description,
            "portrait": st.session_state.get("portrait_url")
        }
        st.session_state.page = 'chatbot'
        st.rerun()

elif st.session_state.page == 'chatbot':
    st.sidebar.title("🎭 Personnage")
    if "character" in st.session_state:
        char = st.session_state.character
        st.sidebar.markdown(f"**{char['name']}**\n- {char['gender']} {char['race']} {char['class']}")
        st.sidebar.markdown(f"_{char['description']}_")
        if char.get("portrait"):
            st.sidebar.image(char["portrait"], width=128)

    st.sidebar.title("📜 Campagne")
    if "campaign" in st.session_state:
        camp = st.session_state.campaign
        st.sidebar.markdown(f"**{camp['name']}**\n- Langue: {camp['language']}\n- Thèmes: {', '.join(camp['themes'])}")

    # Onglets
    tabs = st.tabs(["🎲 Chatbot", "📈 Performances"])
    with tabs[0]:
        launch_chat_interface(st.session_state.user["id"])  # init message inclus
    with tabs[1]:
        from performance import show_performance
        show_performance(st.session_state.user["id"])
