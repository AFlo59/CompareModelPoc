"""
Page des paramètres utilisateur
"""

import streamlit as st

from src.auth.auth import require_auth
from src.data.models import get_user_campaigns, get_user_model_choice, save_model_choice


def show_settings_page() -> None:
    """Page dédiée aux paramètres globaux de l'application."""
    if not require_auth():
        return

    st.title("⚙️ Paramètres de l'application")

    # Bouton retour au dashboard - TOUJOURS accessible
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🏠 Retour au tableau de bord", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.divider()

    # Informations utilisateur
    st.markdown("### 👤 Informations du compte")
    user_email = st.session_state.user.get("email", "Non défini")
    st.info(f"**Email :** {user_email}")

    # Statistiques globales avec gestion d'erreur robuste
    try:
        campaigns = get_user_campaigns(st.session_state.user["id"])
        total_campaigns = len(campaigns)
        total_messages = sum(camp.get("message_count", 0) for camp in campaigns)
    except Exception as e:
        st.warning(f"⚠️ Erreur lors du chargement des statistiques: {e}")
        total_campaigns = 0
        total_messages = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 Campagnes créées", total_campaigns)
    with col2:
        st.metric("💬 Messages totaux", total_messages)
    with col3:
        st.metric("🤖 Modèles utilisés", "Multiple")

    st.divider()

    # Préférences de modèle
    st.markdown("### 🤖 Préférences de modèle IA")

    # Modèles disponibles (devrait être importé de config)
    available_models = ["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"]

    # Modèle actuellement sélectionné avec gestion d'erreur
    try:
        current_model = get_user_model_choice(st.session_state.user["id"])
        if current_model not in available_models:
            current_model = available_models[0]  # Fallback
    except Exception as e:
        st.warning(f"⚠️ Erreur lors du chargement du modèle: {e}")
        current_model = available_models[0]

    # Sélecteur de modèle par défaut
    selected_model = st.selectbox(
        "Choisissez votre modèle IA par défaut:",
        available_models,
        index=available_models.index(current_model) if current_model in available_models else 0,
        help="Ce modèle sera sélectionné par défaut lors de vos prochaines sessions de chat",
    )

    if st.button("💾 Sauvegarder les préférences"):
        try:
            # Tentative de sauvegarde avec gestion robuste
            save_model_choice(st.session_state.user["id"], selected_model)
            st.success(f"✅ Modèle par défaut sauvegardé : {selected_model}")

            # Forcer le rafraîchissement du cache
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde : {e}")
            st.warning("💡 **Conseil :** Essayez de rafraîchir la page ou de vous déconnecter/reconnecter")

            # Bouton de récupération d'erreur
            if st.button("🔄 Rafraîchir la page"):
                st.rerun()

    # Informations sur les modèles
    st.divider()
    st.markdown("### 📊 Informations sur les modèles")

    model_info = {
        "GPT-4": {"icon": "🧠", "desc": "Le plus avancé, excellent pour la créativité", "cost": "$$$$"},
        "GPT-4o": {"icon": "⚡", "desc": "Version optimisée, plus rapide et économique", "cost": "$$$"},
        "Claude 3.5 Sonnet": {"icon": "🎭", "desc": "Excellent pour le roleplay et la narration", "cost": "$$$"},
        "DeepSeek": {"icon": "💰", "desc": "Alternative économique, bon rapport qualité/prix", "cost": "$"},
    }

    for model, info in model_info.items():
        with st.expander(f"{info['icon']} {model}"):
            st.write(f"**Description:** {info['desc']}")
            st.write(f"**Coût relatif:** {info['cost']}")

    st.divider()

    # Section aide
    st.markdown("### ❓ Aide et support")
    st.markdown(
        """
    - **Problème technique ?** Vérifiez que vos clés API sont bien configurées
    - **Performance lente ?** Essayez GPT-4o pour des réponses plus rapides
    - **Budget limité ?** DeepSeek offre un bon rapport qualité/prix
    - **Roleplay immersif ?** Claude 3.5 Sonnet excelle dans la narration
    """
    )
