"""
Compléments pour src.ui.views.character_page
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _mk_col():
    c = Mock(); c.__enter__=Mock(return_value=c); c.__exit__=Mock(return_value=None); return c


class TestCharacterLeftovers:
    @patch('src.ui.views.character_page.require_auth', return_value=True)
    @patch('src.ui.views.character_page.get_user_campaigns')
    @patch('src.ui.views.character_page.get_user_characters')
    def test_existing_character_play_button(self, mock_get_chars, mock_get_camps, _auth):
        from src.ui.views.character_page import show_character_page
        mock_get_camps.return_value = [{"id":1,"name":"C1","themes":[]}]
        mock_get_chars.return_value = [{"id":10,"name":"H","char_class":"Guerrier","race":"Humain","campaign_id":1}]
        with patch('src.ui.views.character_page.st') as st:
            class S(dict):
                def __contains__(self,k): return dict.__contains__(self,k) or hasattr(self,k)
            st.session_state = S(); st.session_state.user={"id":1}
            st.columns.side_effect = lambda spec: [_mk_col() for _ in range(len(spec) if isinstance(spec, list) else spec)]
            # Simuler le clic sur le bouton "Jouer"
            st.button.side_effect = lambda label, **kw: '🎮 Jouer' in label
            show_character_page()
            # Vérifier rendu global (titre affiché) pour la page Personnages
            st.title.assert_called()


