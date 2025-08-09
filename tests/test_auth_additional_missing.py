"""
Tests additionnels pour couvrir les lignes manquantes de src.auth.auth
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestAuthMissingBranches:
    @patch('src.auth.auth.st')
    def test_get_client_id_with_session_id(self, mock_st):
        from src.auth.auth import LoginAttemptTracker
        mock_st.session_state = Mock()
        mock_st.session_state._session_id = 'ABC'
        assert LoginAttemptTracker._get_client_id() == 'ABC'

    @patch('src.auth.auth.st')
    def test_is_locked_out_reset_after_duration(self, mock_st):
        from src.auth.auth import LoginAttemptTracker, SecurityConfig
        # Construire une entrée ancienne (au-delà du LOCKOUT_DURATION)
        key = LoginAttemptTracker._get_attempt_key('user@test.com')
        mock_st.session_state = {key: {'count': SecurityConfig.MAX_LOGIN_ATTEMPTS, 'last_attempt': 0}}
        locked, remaining = LoginAttemptTracker.is_locked_out('user@test.com')
        assert not locked and remaining is None
        assert key not in mock_st.session_state

    def test_get_session_info_no_user(self):
        from src.auth.auth import SessionManager
        with patch('streamlit.session_state', {}):
            assert SessionManager.get_session_info() == {}

    def test_require_special_in_password(self):
        from src.auth.auth import validate_password_enhanced, SecurityConfig
        # Forcer la règle speciale
        old = SecurityConfig.REQUIRE_SPECIAL
        SecurityConfig.REQUIRE_SPECIAL = True
        try:
            ok, msg = validate_password_enhanced('Password123')
            assert not ok and 'caractère spécial' in msg
        finally:
            SecurityConfig.REQUIRE_SPECIAL = old

    @patch('src.auth.auth.bcrypt.gensalt', side_effect=Exception('boom'))
    def test_hash_password_secure_error(self, _gensalt):
        from src.auth.auth import hash_password_secure
        with pytest.raises(Exception):
            hash_password_secure('abc')

    @patch('src.auth.auth.get_connection', side_effect=Exception('db down'))
    @patch('src.auth.auth.st')
    def test_register_user_enhanced_db_exception(self, mock_st, _get_conn):
        from src.auth.auth import register_user_enhanced
        # Remplir un formulaire valide
        class _Ctx:
            def __enter__(self): return self
            def __exit__(self, a,b,c): return False
        mock_st.form.return_value = _Ctx()
        mock_st.text_input.side_effect = ['user@test.com', 'Password123', 'Password123']
        mock_st.form_submit_button.return_value = True
        register_user_enhanced()
        mock_st.error.assert_called()

    @patch('src.auth.auth.logout_enhanced')
    @patch('src.auth.auth.SessionManager.is_session_valid', return_value=False)
    @patch('src.auth.auth.st')
    def test_require_auth_with_user_invalid(self, mock_st, _valid, mock_logout):
        from src.auth.auth import require_auth_enhanced
        class S(dict):
            def __getattr__(self,k): return self.get(k)
            def __setattr__(self,k,v): self[k]=v
        sess = S(); sess.user = {'id': 1}
        mock_st.session_state = sess
        res = require_auth_enhanced()
        assert res is False
        mock_logout.assert_called_once()
        assert sess.page == 'auth'

    @patch('src.auth.auth.st')
    def test_logout_clears_login_attempts(self, mock_st):
        from src.auth.auth import logout_enhanced
        class S(dict):
            def __getattr__(self,k): return self.get(k)
            def __setattr__(self,k,v): self[k]=v
        sess = S(); sess.user={'email':'e'}; sess['login_attempts_x']= {'count':1};
        mock_st.session_state = sess
        with patch('src.auth.auth.st.rerun') as _rr:
            logout_enhanced()
        assert 'login_attempts_x' not in sess

    def test_wrapper_functions(self):
        # Appeler les wrappers pour couvrir les alias
        import src.auth.auth as auth
        with patch.object(auth, 'register_user_enhanced') as r:
            auth.register_user(); r.assert_called()
        with patch.object(auth, 'login_enhanced', return_value={'id':1}) as l:
            assert auth.login() == {'id':1}
        with patch.object(auth, 'require_auth_enhanced', return_value=True) as ra:
            assert auth.require_auth() is True
        with patch.object(auth, 'logout_enhanced') as lo:
            auth.logout(); lo.assert_called()
        with patch.object(auth, 'get_current_user_enhanced', return_value={'id':2}) as gu:
            assert auth.get_current_user() == {'id':2}


