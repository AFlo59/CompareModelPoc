"""
Compléments de couverture pour src.ui.views.chatbot_page
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _mk_col():
    c = Mock()
    c.__enter__ = Mock(return_value=c)
    c.__exit__ = Mock(return_value=None)
    return c


class TestChatbotPageComplements:
    @patch("src.ui.views.chatbot_page.require_auth", return_value=True)
    @patch("src.ui.views.chatbot_page.launch_chat_interface")
    @patch("src.ui.views.chatbot_page.st")
    def test_warnings_no_campaign_no_character(self, mock_st, _launch, _auth):
        from src.ui.views.chatbot_page import show_chatbot_page

        class S(dict):
            def __contains__(self, k):
                return dict.__contains__(self, k) or hasattr(self, k)

        s = S()
        s.user = {"id": 1}
        mock_st.session_state = s
        mock_st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.sidebar.__enter__ = Mock(return_value=mock_st)
        mock_st.sidebar.__exit__ = Mock(return_value=None)
        mock_st.tabs.return_value = [_mk_col(), _mk_col(), _mk_col()]
        with patch("src.analytics.performance.show_performance"):
            show_chatbot_page()
        # Deux warnings affichés
        assert mock_st.warning.call_count >= 2

    @patch("src.ui.views.chatbot_page.require_auth", return_value=True)
    @patch("src.ui.views.chatbot_page.launch_chat_interface")
    @patch("src.ui.views.chatbot_page.st")
    def test_character_portrait_display(self, mock_st, _launch, _auth):
        from src.ui.views.chatbot_page import show_chatbot_page

        class S(dict):
            def __contains__(self, k):
                return dict.__contains__(self, k) or hasattr(self, k)

        s = S()
        s.user = {"id": 1}
        s.campaign = {"id": 1, "name": "Camp", "language": "fr", "themes": []}
        s.character = {"id": 2, "name": "Hero", "portrait_url": "http://img/hero.png"}
        mock_st.session_state = s
        mock_st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.sidebar.__enter__ = Mock(return_value=mock_st)
        mock_st.sidebar.__exit__ = Mock(return_value=None)
        mock_st.tabs.return_value = [_mk_col(), _mk_col(), _mk_col()]
        with patch("src.analytics.performance.show_performance"):
            show_chatbot_page()
        mock_st.image.assert_called()
