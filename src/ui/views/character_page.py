"""
Page de création et gestion des personnages
"""

import streamlit as st
from src.auth.auth import require_auth
from src.data.models import get_user_characters, create_character, get_user_campaigns, update_character_portrait
from src.ai.portraits import generate_portrait
from typing import List, Optional

def show_character_page() -> None:
    """Page dédiée à la gestion des personnages."""
    if not require_auth():
        return

    st.title("🧙‍♂️ Gestion des Personnages")

    # Boutons retour - TOUJOURS accessibles
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🏕️ Mes Campagnes", use_container_width=True):
            st.session_state.page = "campaign"
            st.rerun()
    with col3:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.divider()

    # Récupération des données
    user_id = st.session_state.user["id"]
    
    try:
        campaigns = get_user_campaigns(user_id)
        characters = get_user_characters(user_id)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {e}")
        campaigns, characters = [], []

    # Section : Mes personnages existants
    if characters:
        st.subheader("🎭 Mes Personnages")
        
        for character in characters:
            with st.expander(f"🧙‍♂️ {character.get('name', 'Personnage sans nom')} ({character.get('char_class', 'Classe inconnue')})"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if character.get('portrait_url'):
                        st.image(character['portrait_url'], width=100)
                    else:
                        st.write("🖼️ Pas de portrait")
                
                with col2:
                    st.write(f"**Race :** {character.get('race', 'Non définie')}")
                    st.write(f"**Classe :** {character.get('char_class', 'Non définie')}")
                
                with col3:
                    campaign_id = character.get('campaign_id')
                    campaign_name = "Campagne inconnue"
                    if campaign_id:
                        for camp in campaigns:
                            if camp['id'] == campaign_id:
                                campaign_name = camp.get('name', 'Sans nom')
                                break
                    st.write(f"**Campagne :** {campaign_name}")
                
                with col4:
                    if st.button(f"🎮 Jouer", key=f"play_char_{character['id']}"):
                        st.session_state.selected_campaign = character.get('campaign_id')
                        st.session_state.selected_character = character['id']
                        st.session_state.page = "chatbot"
                        st.rerun()
        
        st.divider()
    
    # Vérifier s'il y a des campagnes
    if not campaigns:
        st.warning("⚠️ **Aucune campagne trouvée !**")
        st.info("💡 **Créez d'abord une campagne** avant de pouvoir créer un personnage.")
        if st.button("🏕️ Créer une Campagne", use_container_width=True):
            st.session_state.page = "campaign"
            st.rerun()
        return
    
    # Section : Créer un nouveau personnage
    st.subheader("➕ Créer un Nouveau Personnage")
    
    with st.form("create_character_form"):
        # Sélection de la campagne
        campaign_options = {camp['id']: f"{camp['name']} ({', '.join(camp.get('themes', []))})" for camp in campaigns}
        selected_campaign_id = st.selectbox(
            "🏕️ Choisir la campagne",
            options=list(campaign_options.keys()),
            format_func=lambda x: campaign_options[x],
            help="Sélectionnez la campagne pour ce personnage"
        )
        
        # Informations du personnage
        col1, col2 = st.columns(2)
        
        with col1:
            character_name = st.text_input(
                "👤 Nom du personnage",
                placeholder="Gandalf le Gris",
                help="Le nom de votre personnage"
            )
            
            character_race = st.selectbox(
                "🧬 Race",
                ["Humain", "Elfe", "Nain", "Halfelin", "Drakéide", "Gnome", "Demi-Elfe", "Demi-Orc", "Tieffelin", "Autre"],
                help="La race de votre personnage"
            )
        
        with col2:
            character_class = st.selectbox(
                "⚔️ Classe",
                ["Guerrier", "Mage", "Voleur", "Clerc", "Ranger", "Paladin", "Barde", "Sorcier", "Warlock", "Druide", "Moine", "Barbare", "Autre"],
                help="La classe de votre personnage"
            )
            
            character_level = st.number_input(
                "📊 Niveau",
                min_value=1,
                max_value=20,
                value=1,
                help="Le niveau de départ de votre personnage"
            )
        
        # Description détaillée
        character_description = st.text_area(
            "📝 Description du personnage",
            placeholder="""Décrivez votre personnage : 
- Apparence physique (taille, corpulence, couleur des cheveux/yeux)
- Personnalité et traits de caractère
- Histoire personnelle et motivations
- Équipement et objets particuliers
- Capacités spéciales ou particularités""",
            height=120,
            help="Plus de détails = meilleur portrait généré par l'IA"
        )
        
        # Options avancées
        with st.expander("🎨 Options avancées de génération"):
            art_style = st.selectbox(
                "🖼️ Style artistique du portrait",
                ["Fantasy Réaliste", "Anime/Manga", "Art Conceptuel", "Peinture Classique", "Illustration Moderne"],
                help="Style pour la génération du portrait"
            )
            
            portrait_mood = st.selectbox(
                "😊 Expression/Humeur",
                ["Neutre", "Déterminé", "Mystérieux", "Jovial", "Sombre", "Heroïque", "Sage"],
                help="L'expression générale du personnage"
            )
        
        # Bouton de création
        submitted = st.form_submit_button("🚀 Créer le Personnage", use_container_width=True)
        
        if submitted:
            if not character_name.strip():
                st.error("❌ Le nom du personnage est obligatoire !")
            else:
                try:
                    # Récupérer les infos de la campagne pour le contexte
                    selected_campaign = next((camp for camp in campaigns if camp['id'] == selected_campaign_id), None)
                    
                    with st.spinner("🎨 Création du personnage et génération du portrait..."):
                        # Créer le personnage d'abord (sans portrait)
                        character_id = create_character(
                            user_id=user_id,
                            name=character_name.strip(),
                            char_class=character_class,
                            race=character_race,
                            description=character_description,
                            campaign_id=selected_campaign_id,
                            level=character_level
                        )
                        
                        st.success(f"✅ Personnage '{character_name}' créé avec succès !")
                        
                        # Générer le portrait du personnage
                        try:
                            st.info("🎨 Génération du portrait en cours...")
                            
                            # Préparer le prompt pour le portrait
                            campaign_context = ""
                            if selected_campaign:
                                themes = ", ".join(selected_campaign.get('themes', []))
                                campaign_context = f"dans un univers {themes}"
                            
                            portrait_prompt = f"""
                            Personnage : {character_name}
                            Race : {character_race}
                            Classe : {character_class}
                            Niveau : {character_level}
                            Contexte : {campaign_context}
                            Description : {character_description}
                            Style : {art_style}
                            Expression : {portrait_mood}
                            """
                            
                            portrait_url = generate_portrait(
                                name=character_name,
                                description=portrait_prompt
                            )
                            
                            if portrait_url:
                                # Mettre à jour le personnage avec le portrait
                                if update_character_portrait(character_id, portrait_url):
                                    st.success("🎨 Portrait généré et sauvegardé avec succès !")
                                    st.image(portrait_url, width=200, caption=f"Portrait de {character_name}")
                                else:
                                    st.warning("🎨 Portrait généré mais erreur de sauvegarde")
                                    st.image(portrait_url, width=200, caption=f"Portrait de {character_name}")
                            else:
                                st.warning("⚠️ Impossible de générer le portrait, mais le personnage est créé.")
                                
                        except Exception as e:
                            st.warning(f"⚠️ Erreur lors de la génération du portrait : {e}")
                            st.info("💡 Le personnage est créé, vous pourrez générer le portrait plus tard.")
                        
                        # Redirection vers le chatbot
                        st.success("🎮 **Prêt à jouer !** Redirection vers le chat...")
                        st.session_state.selected_campaign = selected_campaign_id
                        st.session_state.selected_character = character_id
                        
                        # Petite pause puis redirection
                        import time
                        time.sleep(2)
                        st.session_state.page = "chatbot"
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création : {e}")
                    st.warning("💡 **Conseil :** Essayez de rafraîchir la page")

    # Section aide
    st.divider()
    st.markdown("### 💡 Conseils pour créer un bon personnage")
    
    st.markdown("""
    - **🎭 Nom évocateur** : Choisissez un nom qui correspond à la race et au monde
    - **📝 Description détaillée** : Plus vous donnez de détails, plus le portrait sera précis
    - **🏕️ Cohérence** : Assurez-vous que votre personnage correspond à l'univers de la campagne
    - **🎨 Style artistique** : Choisissez un style qui vous plaît pour le portrait
    - **⚔️ Classe appropriée** : Réfléchissez au rôle que vous voulez jouer dans l'aventure
    """)
