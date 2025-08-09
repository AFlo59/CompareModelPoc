"""
Couvre la branche d'import .env manquant (ligne 17) dans src.core.config
"""

import os
import sys
from io import StringIO
from unittest.mock import patch

import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_env_file_missing_prints_message():
    # Forcer Path.exists() -> False pour déclencher le print
    with patch('src.core.config.Path.exists', return_value=False):
        # Capturer stdout
        buf = StringIO()
        with patch('sys.stdout', buf):
            import src.core.config as cfg
            cfg = importlib.reload(cfg)
        out = buf.getvalue()
        assert "Fichier .env non trouvé" in out


