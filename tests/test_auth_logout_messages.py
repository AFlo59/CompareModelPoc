"""
Couvre les messages de logout (lignes 360-362) restants dans src.auth.auth
"""

import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@patch('src.auth.auth.st')
def test_logout_messages(mock_st):
    from src.auth.auth import logout_enhanced
    class S(dict):
        def __getattr__(self,k): return self.get(k)
        def __setattr__(self,k,v): self[k]=v
    s = S(); s.user={'email':'u@test'}
    mock_st.session_state = s
    mock_st.rerun = Mock()
    logout_enhanced()
    mock_st.success.assert_called()  # message succès

