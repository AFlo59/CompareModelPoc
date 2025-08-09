"""
Tests supplémentaires pour src.auth.auth.register_user_enhanced et require_auth_enhanced/session_info_widget
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _FormCtx:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False


class TestRegisterEnhanced:
    @patch('src.auth.auth.st')
    def test_register_missing_fields(self, mock_st):
        from src.auth.auth import register_user_enhanced
        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["", "", ""]
        mock_st.form_submit_button.return_value = True
        register_user_enhanced()
        mock_st.error.assert_called()

    @patch('src.auth.auth.st')
    def test_register_invalid_email(self, mock_st):
        from src.auth.auth import register_user_enhanced
        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["bad", "Password123", "Password123"]
        mock_st.form_submit_button.return_value = True
        register_user_enhanced()
        mock_st.error.assert_called()

    @patch('src.auth.auth.st')
    def test_register_password_mismatch(self, mock_st):
        from src.auth.auth import register_user_enhanced
        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123", "Password1234"]
        mock_st.form_submit_button.return_value = True
        register_user_enhanced()
        mock_st.error.assert_called()

    @patch('src.auth.auth.hash_password_secure', return_value=b'hash')
    @patch('src.auth.auth.get_connection')
    @patch('src.auth.auth.st')
    def test_register_user_exists(self, mock_st, mock_get_conn, _hash):
        from src.auth.auth import register_user_enhanced
        mock_conn = Mock(); mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (1,)  # user exists
        mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = Mock(return_value=None)
        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123", "Password123"]
        mock_st.form_submit_button.return_value = True
        register_user_enhanced()
        # Erreur "existe déjà"
        assert any("existe déjà" in str(c) for c in map(str, mock_st.error.call_args_list))

    @patch('src.auth.auth.hash_password_secure', return_value=b'hash')
    @patch('src.auth.auth.get_connection')
    @patch('src.auth.auth.st')
    def test_register_success(self, mock_st, mock_get_conn, _hash):
        from src.auth.auth import register_user_enhanced
        mock_conn = Mock(); mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None  # user not exists
        mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = Mock(return_value=None)
        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123", "Password123"]
        mock_st.form_submit_button.return_value = True
        register_user_enhanced()
        mock_st.success.assert_called()


class TestRequireSessionWidgets:
    @patch('src.auth.auth.SessionManager.is_session_valid', return_value=False)
    @patch('src.auth.auth.st')
    def test_require_auth_expired(self, mock_st, _is_valid):
        from src.auth.auth import require_auth_enhanced
        # Utiliser un session_state compatible attributs
        class SessionLike(dict):
            def __getattr__(self, k):
                return self.get(k)
            def __setattr__(self, k, v):
                self[k] = v
        sess = SessionLike()
        mock_st.session_state = sess
        res = require_auth_enhanced()
        assert res is False
        assert sess.get('page') == 'auth'

    @patch('src.auth.auth.SessionManager.get_session_info', return_value={'user': {'email': 'u@test'}, 'remaining_time': 60})
    @patch('src.auth.auth.st')
    def test_session_info_widget(self, mock_st, _info):
        from src.auth.auth import session_info_widget
        sess = {'user': {'email': 'u@test'}}
        mock_st.session_state = sess
        session_info_widget()
        mock_st.sidebar.markdown.assert_called()

