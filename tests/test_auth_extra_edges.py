"""
Compléments de couverture pour src.auth.auth
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _Form:
    def __enter__(self): return self
    def __exit__(self, a,b,c): return False


def test_get_client_id_anonymous():
    from src.auth.auth import LoginAttemptTracker
    with patch('streamlit.session_state', {}):
        assert LoginAttemptTracker._get_client_id() == 'anonymous'


def test_is_locked_out_initial():
    from src.auth.auth import LoginAttemptTracker
    with patch('streamlit.session_state', {}):
        locked, rem = LoginAttemptTracker.is_locked_out('u@test')
        assert locked is False and rem is None


def test_session_valid_user_no_last_activity():
    from src.auth.auth import SessionManager
    sess = {'user': {'id': 1}}
    with patch('streamlit.session_state', sess):
        assert SessionManager.is_session_valid() is False


@patch('src.auth.auth.st')
def test_register_password_invalid(mock_st):
    from src.auth.auth import register_user_enhanced
    mock_st.form.return_value = _Form()
    # Email ok, mot de passe sans majuscule ni chiffre
    mock_st.text_input.side_effect = ['user@test.com', 'password', 'password']
    mock_st.form_submit_button.return_value = True
    register_user_enhanced()
    # Doit afficher une erreur de mot de passe invalide
    assert mock_st.error.called


