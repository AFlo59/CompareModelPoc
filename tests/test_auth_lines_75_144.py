"""
Couvre les lignes 75 et 144 restantes dans src.auth.auth
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@patch("src.auth.auth.st")
def test_is_locked_out_warning_message(mock_st):
    from src.auth.auth import LoginAttemptTracker, SecurityConfig

    # provoquer lockout actif
    key = LoginAttemptTracker._get_attempt_key("u@test")
    mock_st.session_state = {key: {"count": SecurityConfig.MAX_LOGIN_ATTEMPTS, "last_attempt": 10**10}}
    locked, remaining = LoginAttemptTracker.is_locked_out("u@test")
    assert locked and remaining is not None


@patch("src.auth.auth.st")
def test_validate_email_enhanced_format_error_message(mock_st):
    from src.auth.auth import validate_email_enhanced

    ok, msg = validate_email_enhanced("bad@")
    assert not ok and "Format d'email invalide" in msg
