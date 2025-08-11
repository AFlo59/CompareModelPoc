"""
Tests supplémentaires pour src.auth.auth.login_enhanced et fonctions associées
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


class TestLoginEnhanced:
    @patch("src.auth.auth.st")
    def test_login_missing_fields(self, mock_st):
        from src.auth.auth import login_enhanced

        # Form context
        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["", ""]
        mock_st.form_submit_button.return_value = True
        res = login_enhanced()
        assert res is None
        mock_st.error.assert_called()

    @patch("src.auth.auth.st")
    def test_login_invalid_email(self, mock_st):
        from src.auth.auth import login_enhanced

        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["bad email", "Password123"]
        mock_st.form_submit_button.return_value = True
        res = login_enhanced()
        assert res is None
        mock_st.error.assert_called()

    @patch("src.auth.auth.LoginAttemptTracker.is_locked_out", return_value=(True, 125))
    @patch("src.auth.auth.st")
    def test_login_locked_out(self, mock_st, _mock_lock):
        from src.auth.auth import login_enhanced

        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123"]
        mock_st.form_submit_button.return_value = True
        res = login_enhanced()
        assert res is None
        # message avec minutes/seconds
        assert mock_st.error.called

    @patch("src.auth.auth.bcrypt.checkpw", return_value=True)
    @patch("src.auth.auth.SessionManager.update_activity")
    @patch("src.auth.auth.LoginAttemptTracker.reset_attempts")
    @patch("src.auth.auth.get_connection")
    @patch("src.auth.auth.st")
    def test_login_success(self, mock_st, mock_get_conn, _reset, _upd, _check):
        from src.auth.auth import login_enhanced

        # Setup DB fetch
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (99, b"hash")
        mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = Mock(return_value=None)

        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123"]
        mock_st.form_submit_button.return_value = True

        res = login_enhanced()
        assert res == {"id": 99, "email": "user@test.com"}
        mock_st.success.assert_called()

    @patch("src.auth.auth.bcrypt.checkpw", return_value=False)
    @patch("src.auth.auth.LoginAttemptTracker.record_failed_attempt")
    @patch("src.auth.auth.get_connection")
    @patch("src.auth.auth.st")
    def test_login_wrong_credentials(self, mock_st, mock_get_conn, _record, _check):
        from src.auth.auth import login_enhanced

        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = (99, b"hash")
        mock_get_conn.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = Mock(return_value=None)

        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123"]
        mock_st.form_submit_button.return_value = True

        res = login_enhanced()
        assert res is None
        mock_st.error.assert_called()

    @patch("src.auth.auth.get_connection", side_effect=Exception("db down"))
    @patch("src.auth.auth.st")
    def test_login_db_exception(self, mock_st, _get_conn):
        from src.auth.auth import login_enhanced

        mock_st.form.return_value = _FormCtx()
        mock_st.text_input.side_effect = ["user@test.com", "Password123"]
        mock_st.form_submit_button.return_value = True
        res = login_enhanced()
        assert res is None
        mock_st.error.assert_called()
