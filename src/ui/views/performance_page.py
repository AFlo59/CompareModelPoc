"""
Page des performances et analytics
"""

import streamlit as st
from src.auth.auth import require_auth
import src.analytics.performance as performance


def show_performance(user_id: int) -> None:
    """Wrapper pour permettre le patch des tests et déléguer à analytics."""
    # Délègue à la fonction réelle, ce qui permet que
    # - le patch sur src.ui.views.performance_page.show_performance fonctionne (ce wrapper)
    # - le patch sur src.analytics.performance.show_performance fonctionne (appel délégué)
    return performance.show_performance(user_id)

def show_performance_page() -> None:
    """Page dédiée aux performances."""
    if not require_auth():
        return

    # Bouton retour au dashboard
    if st.button("🏠 Retour au tableau de bord"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.divider()

    show_performance(st.session_state.user["id"])
