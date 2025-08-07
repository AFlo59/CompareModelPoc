import streamlit as st
import sqlite3
import bcrypt
from database import get_connection

def register_user():
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    confirm = st.text_input("Confirmer le mot de passe", type="password")
    
    if st.button("Créer le compte"):
        if password != confirm:
            st.error("Les mots de passe ne correspondent pas.")
            return

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
            conn.commit()
            st.success("Compte créé. Vous pouvez maintenant vous connecter.")
        except sqlite3.IntegrityError:
            st.error("Email déjà utilisé.")
        finally:
            conn.close()

def login():
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        result = c.fetchone()
        conn.close()

        if result and bcrypt.checkpw(password.encode(), result[1]):
            st.success("Connexion réussie")
            return {"id": result[0], "email": email}
        else:
            st.error("Identifiants incorrects")
            return None

def get_current_user():
    return st.session_state.get("user")