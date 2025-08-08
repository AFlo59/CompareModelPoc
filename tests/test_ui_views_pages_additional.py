"""
Tests supplémentaires pour les vues UI: campaign_page, character_page, chatbot_page
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


class TestCampaignPage:
    @patch('src.ui.views.campaign_page.require_auth', return_value=True)
    @patch('src.ui.views.campaign_page.get_user_campaigns')
    def test_campaign_page_success_no_submit(self, mock_get_campaigns, _auth):
        from src.ui.views.campaign_page import show_campaign_page

        mock_get_campaigns.return_value = [
            {"id": 1, "name": "Camp 1", "themes": ["Fantasy"], "language": "fr"}
        ]

        with patch('src.ui.views.campaign_page.st') as st:
            class SessionLike(dict):
                def __contains__(self, key):
                    return dict.__contains__(self, key) or hasattr(self, key)
            st.session_state = SessionLike()
            st.session_state.user = {"id": 1}
            st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
            st.button.return_value = False
            st.form.return_value.__enter__ = Mock(return_value=_mk_col())
            st.form.return_value.__exit__ = Mock(return_value=None)
            st.form_submit_button.return_value = False

            show_campaign_page()
            st.title.assert_called()

    @patch('time.sleep', return_value=None)
    @patch('src.ui.views.campaign_page.update_campaign_portrait', return_value=True)
    @patch('src.ui.views.campaign_page.generate_gm_portrait', return_value='http://img/gm.png')
    @patch('src.ui.views.campaign_page.create_campaign', return_value=42)
    @patch('src.ui.views.campaign_page.require_auth', return_value=True)
    @patch('src.ui.views.campaign_page.get_user_campaigns')
    def test_campaign_page_submit_flow(self, mock_get_campaigns, _auth, _create, _gen, _update, _sleep):
        from src.ui.views.campaign_page import show_campaign_page

        mock_get_campaigns.return_value = []

        with patch('src.ui.views.campaign_page.st') as st:
            class SessionLike:
                pass
            st.session_state = SessionLike()
            st.session_state.user = {"id": 1}
            st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
            st.button.return_value = False
            st.form.return_value.__enter__ = Mock(return_value=_mk_col())
            st.form.return_value.__exit__ = Mock(return_value=None)

            # Inputs du formulaire
            st.text_input.return_value = "Ma Campagne"
            st.selectbox.side_effect = [
                "Fantasy",  # primary_theme
                "Français",  # language
                "GPT-4",     # ai_model
                "Épique"     # tone
            ]
            st.multiselect.return_value = []
            st.text_area.return_value = "Description"
            st.form_submit_button.return_value = True

            show_campaign_page()
            # compat dict-like and attr-like, éviter d'évaluer .get si non nécessaire
            if hasattr(st.session_state, 'selected_campaign'):
                selected = st.session_state.selected_campaign
            else:
                selected = st.session_state.get('selected_campaign')
            assert selected == 42


class TestCharacterPage:
    @patch('src.ui.views.character_page.require_auth', return_value=True)
    @patch('src.ui.views.character_page.get_user_campaigns', return_value=[])
    @patch('src.ui.views.character_page.get_user_characters', return_value=[])
    def test_character_page_no_campaigns(self, _chars, _camps, _auth):
        from src.ui.views.character_page import show_character_page
        with patch('src.ui.views.character_page.st') as st:
            class SessionLike(dict):
                def __contains__(self, key):
                    return dict.__contains__(self, key) or hasattr(self, key)
            st.session_state = SessionLike()
            st.session_state.user = {"id": 1}
            st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
            st.button.return_value = False
            show_character_page()
            st.warning.assert_called()

    @patch('time.sleep', return_value=None)
    @patch('src.ui.views.character_page.update_character_portrait', return_value=True)
    @patch('src.ui.views.character_page.generate_portrait', return_value='http://img/char.png')
    @patch('src.ui.views.character_page.create_character', return_value=7)
    @patch('src.ui.views.character_page.get_user_characters', return_value=[])
    @patch('src.ui.views.character_page.get_user_campaigns')
    @patch('src.ui.views.character_page.require_auth', return_value=True)
    def test_character_page_create_flow(self, _auth, mock_get_camps, _chars, _create, _gen, _update, _sleep):
        from src.ui.views.character_page import show_character_page

        mock_get_camps.return_value = [{"id": 1, "name": "Camp 1", "themes": ["Fantasy"]}]

        with patch('src.ui.views.character_page.st') as st:
            class SessionLike:
                pass
            st.session_state = SessionLike()
            st.session_state.user = {"id": 1}
            st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
            st.button.return_value = False
            st.form.return_value.__enter__ = Mock(return_value=_mk_col())
            st.form.return_value.__exit__ = Mock(return_value=None)
            # Plusieurs selectbox sont appelés: campaign, race, class, art_style, portrait_mood
            st.selectbox.side_effect = [
                1,               # selected campaign id via selectbox(options=list(keys))
                "Humain",       # race
                "Guerrier",     # class
                "Fantasy Réaliste",  # art_style
                "Neutre"        # portrait_mood
            ]
            st.number_input.return_value = 1
            st.text_input.return_value = "Personnage"
            st.text_area.return_value = "Desc"
            st.form_submit_button.return_value = True

            show_character_page()
            if hasattr(st.session_state, 'selected_character'):
                selected = st.session_state.selected_character
            else:
                selected = st.session_state.get('selected_character')
            assert selected == 7


class TestChatbotPage:
    @patch('src.ui.views.chatbot_page.require_auth', return_value=True)
    @patch('src.ui.views.chatbot_page.launch_chat_interface')
    @patch('src.ui.views.chatbot_page.get_user_campaigns', return_value=[])
    @patch('src.ui.views.chatbot_page.st')
    def test_chatbot_page_headers(self, mock_st, _camps, _launch, _auth):
        from src.ui.views.chatbot_page import show_chatbot_page

        # Préparer session: objet compatible accès attributs + mapping
        class SessionLike(dict):
            def __contains__(self, key):
                return dict.__contains__(self, key) or hasattr(self, key)
        s = SessionLike()
        s.user = {"id": 1, "email": "user@test"}
        s.campaign = {"id": 1, "name": "Camp", "language": "fr", "themes": ["Fantasy"], "ai_model": "GPT-4"}
        s.character = {"id": 2, "name": "Hero", "level": 1, "race": "Humain", "class": "Guerrier"}
        mock_st.session_state = s

        # Mock UI helpers
        mock_st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.sidebar.__enter__ = Mock(return_value=mock_st)
        mock_st.sidebar.__exit__ = Mock(return_value=None)
        mock_st.tabs.return_value = [_mk_col(), _mk_col(), _mk_col()]
        mock_st.button.return_value = False

        with patch('src.analytics.performance.show_performance') as mock_perf:
            show_chatbot_page()
            _launch.assert_called_once()
            mock_perf.assert_called_once_with(1)


