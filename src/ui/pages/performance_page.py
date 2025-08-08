"""
Page des performances et analytics
"""

import streamlit as st
from src.auth.auth import require_auth
from src.analytics.performance import show_performance

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
