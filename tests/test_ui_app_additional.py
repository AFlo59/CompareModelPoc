"""
Tests supplémentaires pour src.ui.app afin de couvrir la navigation et erreurs
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestUIAppAdditional:
    @patch('src.ui.app.configure_page')
    @patch('src.ui.app.apply_custom_css')
    def test_main_unknown_page(self, mock_css, mock_cfg):
        from src.ui.app import main

        class SessionLike(dict):
            def __init__(self):
                super().__init__()
                self.page = "unknown_page"
                self["page"] = "unknown_page"

        with patch('src.ui.app.st') as mock_st:
            mock_st.session_state = SessionLike()
            mock_st.rerun = Mock()
            main()
            mock_st.error.assert_called()
            assert mock_st.session_state.page == "auth"

    @patch('src.ui.app.configure_page')
    @patch('src.ui.app.apply_custom_css')
    @patch('src.ui.app.initialize_app')
    def test_main_initialization_once(self, mock_init, _css, _cfg):
        from src.ui.app import main

        class SessionLike(dict):
            pass

        # Premier appel: doit initialiser
        with patch('src.ui.app.st') as mock_st:
            mock_st.session_state = SessionLike()
            main()
            assert hasattr(mock_st.session_state, 'app_initialized')

        # Second appel: ne doit pas rappeler initialize_app
        with patch('src.ui.app.st') as mock_st:
            mock_st.session_state = SessionLike()
            mock_st.session_state.app_initialized = True
            mock_st.session_state['app_initialized'] = True
            main()
        mock_init.assert_called_once()


