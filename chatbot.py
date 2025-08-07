import streamlit as st
import time
from database import get_connection
from models import get_user_campaigns
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_last_model(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT model FROM model_choices WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "GPT-4"

def get_previous_history(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def store_message(user_id, role, content):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()

def store_performance(user_id, model, latency, tokens_in, tokens_out):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO performance_logs (user_id, model, latency, tokens_in, tokens_out) VALUES (?, ?, ?, ?, ?)",
              (user_id, model, latency, tokens_in, tokens_out))
    conn.commit()
    conn.close()

def launch_chat_interface(user_id):
    st.title("🎲 Donjons & Dragons - Chatbot")
    model = get_last_model(user_id)

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
        conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        conn.commit()
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
        st.session_state.history.append({"role": "system", "content": system_prompt})

        with st.spinner("Initialisation de la partie..."):
            t0 = time.time()
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=st.session_state.history,
                temperature=0.9,
            )
            latency = time.time() - t0
            tokens_in = response["usage"]["prompt_tokens"]
            tokens_out = response["usage"]["completion_tokens"]
            store_performance(user_id, model, latency, tokens_in, tokens_out)
            intro_msg = response.choices[0].message.content
            st.session_state.history.append({"role": "assistant", "content": intro_msg})
            store_message(user_id, "system", system_prompt)
            store_message(user_id, "assistant", intro_msg)

    for msg in st.session_state.history:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Votre action ?"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})
        store_message(user_id, "user", prompt)

        with st.spinner("Réponse du MJ..."):
            t0 = time.time()
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=st.session_state.history,
                    temperature=0.8,
                )
                latency = time.time() - t0
                tokens_in = response["usage"]["prompt_tokens"]
                tokens_out = response["usage"]["completion_tokens"]
                store_performance(user_id, model, latency, tokens_in, tokens_out)
                reply = response.choices[0].message.content
            except Exception as e:
                reply = "Erreur : " + str(e)

        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.history.append({"role": "assistant", "content": reply})
        store_message(user_id, "assistant", reply)
