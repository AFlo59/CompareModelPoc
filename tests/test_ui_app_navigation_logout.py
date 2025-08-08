"""
Tests supplémentaires pour src.ui.app: navigation sidebar et logout
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class SessionLike(dict):
    def __getattr__(self, k):
        return self.get(k)
    def __setattr__(self, k, v):
        self[k] = v


def _col():
    c = Mock()
    c.__enter__ = Mock(return_value=c)
    c.__exit__ = Mock(return_value=None)
    return c


class TestUIAppNavigationLogout:
    @patch('src.ui.app.st')
    def test_show_navigation_clicks(self, mock_st):
        from src.ui.app import show_navigation

        sess = SessionLike()
        sess.user = {"email": "u@test"}
        mock_st.session_state = sess

        # Simuler un click sur "📊 Performances" (retourne True uniquement pour ce label)
        def button_side_effect(label, **kwargs):
            return "📊 Performances" in label
        mock_st.button.side_effect = button_side_effect

        show_navigation()
        assert mock_st.session_state.page == "performance"
        mock_st.rerun.assert_called()

    @patch('src.ui.app.st')
    def test_logout_button(self, mock_st):
        from src.ui.app import show_navigation

        sess = SessionLike()
        sess.user = {"email": "u@test"}
        mock_st.session_state = sess

        # Aucun click sur les boutons de nav; click sur logout seulement
        def button_side_effect(label, **kwargs):
            return "🚪 Déconnexion" in label
        mock_st.button.side_effect = button_side_effect

        show_navigation()
        # user doit être supprimé et page redirigée vers auth
        assert "user" not in mock_st.session_state
        assert mock_st.session_state.page == "auth"
        mock_st.rerun.assert_called()


