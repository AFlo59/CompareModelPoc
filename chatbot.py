import streamlit as st
import time
import logging
from typing import List, Dict, Any, Optional
from database import get_connection
from models import get_user_campaigns
from openai import OpenAI
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des clients API
def get_openai_client() -> OpenAI:
    """Initialise et retourne un client OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY manquante")
    return OpenAI(api_key=api_key)

def get_anthropic_client() -> anthropic.Anthropic:
    """Initialise et retourne un client Anthropic."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY manquante")
    return anthropic.Anthropic(api_key=api_key)

def get_last_model(user_id: int) -> str:
    """Récupère le dernier modèle choisi par l'utilisateur."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT model FROM model_choices WHERE user_id = ? ORDER BY rowid DESC LIMIT 1", (user_id,))
        row = c.fetchone()
        return row[0] if row else "GPT-4"
    finally:
        conn.close()

def get_previous_history(user_id: int) -> List[Dict[str, str]]:
    """Récupère l'historique des messages depuis la base de données."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC LIMIT 50", (user_id,))
        rows = c.fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]
    finally:
        conn.close()

def store_message(user_id: int, role: str, content: str) -> None:
    """Stocke un message dans la base de données."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
        conn.commit()
    finally:
        conn.close()

def store_performance(user_id: int, model: str, latency: float, tokens_in: int, tokens_out: int) -> None:
    """Stocke les données de performance dans la base de données."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO performance_logs (user_id, model, latency, tokens_in, tokens_out) VALUES (?, ?, ?, ?, ?)",
                  (user_id, model, latency, tokens_in, tokens_out))
        conn.commit()
    finally:
        conn.close()

def call_ai_model(model: str, messages: List[Dict[str, str]], temperature: float = 0.8) -> Dict[str, Any]:
    """
    Appelle le modèle d'IA approprié selon le nom du modèle.
    
    Returns:
        Dict contenant 'content', 'tokens_in', 'tokens_out'
    """
    try:
        if model.startswith("GPT-4"):
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4" if model == "GPT-4" else "gpt-4o",
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            return {
                'content': response.choices[0].message.content,
                'tokens_in': response.usage.prompt_tokens,
                'tokens_out': response.usage.completion_tokens
            }
        elif model == "Claude 3.5 Sonnet":
            client = get_anthropic_client()
            # Séparer le message système des autres messages
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            # S'assurer qu'il y a au moins un message utilisateur
            if not user_messages:
                user_messages = [{"role": "user", "content": "Commençons l'aventure !"}]
                    
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                temperature=temperature,
                system=system_msg if system_msg else "Tu es un assistant IA.",
                messages=user_messages
            )
            return {
                'content': response.content[0].text,
                'tokens_in': response.usage.input_tokens,
                'tokens_out': response.usage.output_tokens
            }
        else:
            # Fallback vers GPT-4 pour modèles non supportés
            logger.warning(f"Modèle {model} non supporté, utilisation de GPT-4")
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            return {
                'content': response.choices[0].message.content,
                'tokens_in': response.usage.prompt_tokens,
                'tokens_out': response.usage.completion_tokens
            }
    except Exception as e:
        logger.error(f"Erreur avec le modèle {model}: {e}")
        raise

def launch_chat_interface(user_id: int) -> None:
    """Lance l'interface de chat principal."""
    st.title("🎲 Donjons & Dragons - Chatbot")
    model = get_last_model(user_id)
    
    # Affichage du modèle actuel
    st.info(f"🤖 Modèle actuel: **{model}**")

    if 'history' not in st.session_state:
        # Si pas d'historique en mémoire, on le récupère depuis la DB
        st.session_state.history = get_previous_history(user_id)
        if st.session_state.history:
            with st.chat_message("assistant"):
                st.markdown("_Bienvenue de retour. Voici un rappel de votre session précédente. Reprenez quand vous êtes prêt !_")

    # Bouton pour réinitialiser la session
    if st.button("🔄 Recommencer une nouvelle aventure"):
        st.session_state.history = []
        conn = get_connection()
        try:
            conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()
        st.rerun()

    # Nouvelle session automatique
    if not st.session_state.history:
        char = st.session_state.get("character", {})
        camp = st.session_state.get("campaign", {})

        system_prompt = f"""
Tu es un Maître du Jeu (MJ) expert en jeux de rôle, chargé d'animer une session immersive de Donjons & Dragons.
Voici les informations de départ :

Campagne : "{camp.get('name', 'Inconnue')}"
Langue : {camp.get('language', 'fr')}
Thèmes : {', '.join(camp.get('themes', []))}

Personnage Joueur :
- Nom : {char.get('name', 'Sans nom')}
- Classe : {char.get('class', 'Indéfinie')}
- Race : {char.get('race', 'Inconnue')}
- Genre : {char.get('gender', 'Non précisé')}
- Description : {char.get('description', 'Aucune')}

Ta mission : démarrer l'aventure directement par une scène narrative qui capte l'attention. Pose une situation intrigante, un décor vivant, et invite le joueur à réagir. Tu ne donnes pas d'option multiple, tu attends simplement sa réponse roleplay.
        """
        
        # Ajouter le message système
        st.session_state.history.append({"role": "system", "content": system_prompt})
        
        # Pour Claude, nous devons ajouter un message utilisateur initial
        initial_user_message = "Commençons l'aventure !"
        st.session_state.history.append({"role": "user", "content": initial_user_message})

        with st.spinner("Initialisation de la partie..."):
            try:
                t0 = time.time()
                ai_response = call_ai_model(model, st.session_state.history, temperature=0.9)
                latency = time.time() - t0
                
                intro_msg = ai_response['content']
                store_performance(user_id, model, latency, ai_response['tokens_in'], ai_response['tokens_out'])
                
                st.session_state.history.append({"role": "assistant", "content": intro_msg})
                store_message(user_id, "system", system_prompt)
                store_message(user_id, "user", initial_user_message)
                store_message(user_id, "assistant", intro_msg)
                
                logger.info(f"Session initialisée pour utilisateur {user_id} avec {model}")
            except Exception as e:
                st.error(f"Erreur lors de l'initialisation: {e}")
                logger.error(f"Erreur initialisation pour utilisateur {user_id}: {e}")

    # Affichage de l'historique
    for msg in st.session_state.history:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Interface de saisie
    if prompt := st.chat_input("Votre action ?"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})
        store_message(user_id, "user", prompt)

        with st.spinner("Réponse du MJ..."):
            try:
                t0 = time.time()
                ai_response = call_ai_model(model, st.session_state.history, temperature=0.8)
                latency = time.time() - t0
                
                reply = ai_response['content']
                store_performance(user_id, model, latency, ai_response['tokens_in'], ai_response['tokens_out'])
                
                logger.info(f"Réponse générée en {latency:.2f}s avec {model}")
            except Exception as e:
                reply = f"Erreur technique : {str(e)}"
                logger.error(f"Erreur génération réponse: {e}")

        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.history.append({"role": "assistant", "content": reply})
        store_message(user_id, "assistant", reply)
