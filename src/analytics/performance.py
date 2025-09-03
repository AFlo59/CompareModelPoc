import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data.database import get_connection

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Coûts par modèle (USD par 1K tokens) - TARIFS ACTUELS 2025
MODEL_COSTS = {
    "GPT-4": {"in": 0.030, "out": 0.060},  # $30/$60 per 1M tokens
    "GPT-4o": {"in": 0.0025, "out": 0.010},  # $2.50/$10 per 1M tokens
    "Claude 3.5 Sonnet": {"in": 0.003, "out": 0.015},  # $3/$15 per 1M tokens
    "DeepSeek V3": {"in": 0.00014, "out": 0.00028},  # $0.14/$0.28 per 1M tokens
}


def get_performance_data(user_id: int, days: int = 30) -> pd.DataFrame:
    """
    Récupère les données de performance d'un utilisateur.

    Args:
        user_id: ID de l'utilisateur
        days: Nombre de jours à récupérer (défaut: 30)

    Returns:
        DataFrame avec les données de performance
    """
    conn = get_connection()
    try:
        query = """
            SELECT model, latency, tokens_in, tokens_out, timestamp
            FROM performance_logs
            WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        """.format(
            days
        )

        df = pd.read_sql_query(query, conn, params=(user_id,))

        if not df.empty:
            # Conversion du timestamp
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["date"] = df["timestamp"].dt.date

            # Calcul des coûts
            df["cost"] = df.apply(calculate_cost, axis=1)

        return df
    finally:
        conn.close()


def calculate_cost(row: pd.Series) -> float:
    """Calcule le coût d'une requête basé sur le modèle et les tokens."""
    model_name = row["model"]

    # Gestion de la rétrocompatibilité pour DeepSeek
    if model_name == "DeepSeek":
        model_name = "DeepSeek V3"

    costs = MODEL_COSTS.get(model_name, {"in": 0.01, "out": 0.01})
    return round((row["tokens_in"] / 1000) * costs["in"] + (row["tokens_out"] / 1000) * costs["out"], 4)


def show_performance_summary(df: pd.DataFrame) -> None:
    """Affiche un résumé des performances."""
    if df.empty:
        st.info("📊 Aucune donnée de performance disponible.")
        return

    # Métriques globales
    total_requests = len(df)
    total_cost = df["cost"].sum()
    avg_latency = df["latency"].mean()
    total_tokens = df["tokens_in"].sum() + df["tokens_out"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🔥 Requêtes totales", total_requests)
    with col2:
        st.metric("💰 Coût total", f"${total_cost:.4f}")
    with col3:
        st.metric("⚡ Latence moyenne", f"{avg_latency:.2f}s")
    with col4:
        st.metric("🎯 Tokens totaux", f"{total_tokens:,}")


def show_model_comparison(df: pd.DataFrame) -> None:
    """Affiche une comparaison entre les modèles."""
    if df.empty:
        return

    st.subheader("📈 Comparaison des modèles")

    # Agrégation par modèle
    model_stats = (
        df.groupby("model")
        .agg({"latency": ["mean", "std", "count"], "tokens_in": "mean", "tokens_out": "mean", "cost": ["mean", "sum"]})
        .round(4)
    )

    # Aplatir les colonnes multi-niveau
    model_stats.columns = ["_".join(col).strip() for col in model_stats.columns]
    model_stats = model_stats.reset_index()

    # Renommer pour plus de clarté
    model_stats.rename(
        columns={
            "latency_mean": "Latence moy. (s)",
            "latency_std": "Écart-type latence",
            "latency_count": "Nb requêtes",
            "tokens_in_mean": "Tokens entrée moy.",
            "tokens_out_mean": "Tokens sortie moy.",
            "cost_mean": "Coût moy. ($)",
            "cost_sum": "Coût total ($)",
        },
        inplace=True,
    )

    st.dataframe(model_stats, use_container_width=True)


def show_performance_charts(df: pd.DataFrame) -> None:
    """Affiche des graphiques de performance."""
    if df.empty:
        return

    st.subheader("📊 Graphiques de performance")

    col1, col2 = st.columns(2)

    with col1:
        # Graphique de latence par modèle
        fig_latency = px.box(
            df,
            x="model",
            y="latency",
            title="Distribution de la latence par modèle",
            labels={"latency": "Latence (secondes)", "model": "Modèle"},
        )
        fig_latency.update_layout(height=400)
        st.plotly_chart(fig_latency, use_container_width=True)

    with col2:
        # Graphique des coûts par modèle
        cost_by_model = df.groupby("model")["cost"].sum().reset_index()
        fig_cost = px.pie(cost_by_model, values="cost", names="model", title="Répartition des coûts par modèle")
        fig_cost.update_layout(height=400)
        st.plotly_chart(fig_cost, use_container_width=True)

    # Évolution temporelle
    if len(df) > 1:
        st.subheader("📈 Évolution temporelle")

        # Agrégation par jour
        daily_stats = (
            df.groupby(["date", "model"])
            .agg({"latency": "mean", "cost": "sum", "tokens_in": "sum", "tokens_out": "sum"})
            .reset_index()
        )

        tab1, tab2, tab3 = st.tabs(["Latence", "Coûts", "Tokens"])

        with tab1:
            fig_latency_time = px.line(
                daily_stats,
                x="date",
                y="latency",
                color="model",
                title="Évolution de la latence moyenne par jour",
                labels={"latency": "Latence (s)", "date": "Date"},
            )
            st.plotly_chart(fig_latency_time, use_container_width=True)

        with tab2:
            fig_cost_time = px.bar(
                daily_stats,
                x="date",
                y="cost",
                color="model",
                title="Coûts quotidiens par modèle",
                labels={"cost": "Coût ($)", "date": "Date"},
            )
            st.plotly_chart(fig_cost_time, use_container_width=True)

        with tab3:
            # Calculer le total de tokens par jour
            daily_stats["total_tokens"] = daily_stats["tokens_in"] + daily_stats["tokens_out"]
            fig_tokens_time = px.line(
                daily_stats,
                x="date",
                y="total_tokens",
                color="model",
                title="Évolution du nombre de tokens par jour",
                labels={"total_tokens": "Tokens totaux", "date": "Date"},
            )
            st.plotly_chart(fig_tokens_time, use_container_width=True)


def show_performance(user_id: int) -> None:
    """Affiche les performances des modèles avec onglets pour différentes vues."""
    st.title("📊 Analyse des Performances")

    # Onglets principaux
    tab1, tab2 = st.tabs(["🤖 Performances IA", "🖥️ Monitoring Système"])

    with tab1:
        show_ai_performance(user_id)

    with tab2:
        show_system_monitoring()


def show_ai_performance(user_id: int) -> None:
    """Affiche les performances des modèles IA."""
    st.title("📊 Performances Globales des Modèles")

    st.info("📈 **Vue d'ensemble** - Ces statistiques incluent toutes vos interactions avec l'IA, toutes campagnes confondues.")

    # Sélecteur de période
    col1, col2 = st.columns([3, 1])
    with col1:
        period = st.selectbox(
            "📅 Période d'analyse", options=[7, 30, 90, 365], index=1, format_func=lambda x: f"Derniers {x} jours"
        )

    with col2:
        st.button("🔄 Actualiser", use_container_width=True)

    # Récupération des données
    df = get_performance_data(user_id, period)

    if df.empty:
        st.info("� Aucune donnée de performance enregistrée pour cette période.")
        st.markdown(
            """
        💡 **Pour voir des statistiques ici :**
        - Utilisez le chatbot pour générer des réponses
        - Les performances sont enregistrées automatiquement
        - Revenez dans quelques minutes pour voir vos statistiques
        """
        )
        return

    # Affichage des résultats
    show_performance_summary(df)

    st.divider()

    show_model_comparison(df)

    st.divider()

    show_performance_charts(df)

    # Section détails
    with st.expander("📋 Données détaillées"):
        # Options d'affichage
        col1, col2 = st.columns(2)
        with col1:
            model_filter = st.multiselect("Filtrer par modèle", options=df["model"].unique(), default=df["model"].unique())
        with col2:
            sort_by = st.selectbox("Trier par", options=["timestamp", "latency", "cost", "model"], index=0)

        # Filtrage et tri
        filtered_df = df[df["model"].isin(model_filter)].sort_values(
            by=sort_by, ascending=False if sort_by in ["timestamp", "cost"] else True
        )

        # Formatage pour l'affichage
        display_df = filtered_df[["model", "latency", "tokens_in", "tokens_out", "cost", "timestamp"]].copy()
        display_df.columns = ["Modèle", "Latence (s)", "Tokens Entrée", "Tokens Sortie", "Coût ($)", "Horodatage"]

        st.dataframe(display_df, use_container_width=True, height=400)

        # Export CSV
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )


def show_system_monitoring() -> None:
    """Affiche les informations de monitoring système."""
    st.title("🖥️ Monitoring Système")

    st.info("📊 **Informations Système** - Vue d'ensemble de l'état du système")

    try:
        import platform

        import psutil

        st.success("✅ Module psutil détecté")

        # Informations générales
        col1, col2, col3 = st.columns(3)

        with col1:
            try:
                ram_percent = psutil.virtual_memory().percent
                st.metric("💾 RAM utilisée", f"{ram_percent:.1f}%")
            except Exception as e:
                st.metric("💾 RAM utilisée", "Erreur")
                st.error(f"Erreur RAM: {e}")

        with col2:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)  # Interval plus court
                st.metric("💽 CPU utilisé", f"{cpu_percent:.1f}%")
            except Exception as e:
                st.metric("💽 CPU utilisé", "Erreur")
                st.error(f"Erreur CPU: {e}")
        with col3:
            try:
                # Essayer '/' d'abord (Linux/Docker), puis 'C:' (Windows)
                try:
                    disk_usage = psutil.disk_usage("/")
                except (OSError, FileNotFoundError):
                    disk_usage = psutil.disk_usage("C:")
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                st.metric("💿 Disque utilisé", f"{disk_percent:.1f}%")
            except Exception:
                st.metric("💿 Disque utilisé", "N/A")

        st.divider()

        # Informations détaillées
        st.subheader("📋 Détails du système")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🖥️ Système d'exploitation**")
            st.write(f"• **OS:** {platform.system()} {platform.release()}")
            st.write(f"• **Architecture:** {platform.machine()}")
            st.write(f"• **Processeur:** {platform.processor()}")

        with col2:
            st.markdown("**💾 Mémoire**")
            memory = psutil.virtual_memory()
            st.write(f"• **Total:** {memory.total / (1024**3):.1f} GB")
            st.write(f"• **Disponible:** {memory.available / (1024**3):.1f} GB")
            st.write(f"• **Utilisée:** {memory.used / (1024**3):.1f} GB")

        # Status de l'application
        st.divider()
        st.subheader("🚀 État de l'application")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.success("✅ Base de données connectée")
        with col2:
            st.success("✅ Streamlit actif")
        with col3:
            st.success("✅ API endpoints disponibles")

    except ImportError:
        st.warning("⚠️ Module `psutil` non installé - Monitoring système limité")

        # Version simplifiée sans psutil
        st.subheader("📋 Informations basiques")

        col1, col2 = st.columns(2)

        with col1:
            # Importer platform ici pour éviter UnboundLocalError lorsque l'import dans le bloc try a échoué
            import platform  # noqa: F401

            st.markdown("**🖥️ Système**")
            st.write(f"• **OS:** {platform.system()}")
            st.write(f"• **Version:** {platform.release()}")

        with col2:
            st.markdown("**🚀 Application**")
            st.success("✅ Streamlit actif")
            st.success("✅ Base de données connectée")

    except Exception as e:
        st.error(f"❌ Erreur lors du monitoring système: {e}")

        # Fallback basique
        st.subheader("📋 État basique")
        st.success("✅ Application fonctionnelle")
