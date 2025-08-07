import streamlit as st
import pandas as pd
from database import get_connection

# Coûts par modèle (USD par 1K tokens)
MODEL_COSTS = {
    "GPT-4": {"in": 0.03, "out": 0.06},
    "GPT-4o": {"in": 0.005, "out": 0.015},
    "Claude 3.5 Sonnet": {"in": 0.003, "out": 0.015},
    "DeepSeek": {"in": 0.002, "out": 0.002}  # estimation fictive
}

def show_performance(user_id):
    st.title("📊 Performances des Modèles")
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT model, latency, tokens_in, tokens_out, timestamp
        FROM performance_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,))
    rows = c.fetchall()
    conn.close()

    if rows:
        df = pd.DataFrame(rows, columns=["Modèle", "Latence (s)", "Tokens Entrée", "Tokens Sortie", "Horodatage"])

        # Calcul des coûts
        def calculate_cost(row):
            costs = MODEL_COSTS.get(row["Modèle"], {"in": 0.01, "out": 0.01})
            return round((row["Tokens Entrée"] / 1000) * costs["in"] + (row["Tokens Sortie"] / 1000) * costs["out"], 4)

        df["Coût estimé ($)"] = df.apply(calculate_cost, axis=1)
        st.dataframe(df)

        avg_df = df.groupby("Modèle").agg({
            "Latence (s)": "mean",
            "Tokens Entrée": "mean",
            "Tokens Sortie": "mean",
            "Coût estimé ($)": "mean"
        }).round(3)

        st.subheader("📈 Moyennes par modèle")
        st.dataframe(avg_df)
    else:
        st.info("Aucune donnée de performance enregistrée pour le moment.")
