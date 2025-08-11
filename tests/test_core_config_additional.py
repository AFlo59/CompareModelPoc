"""
Tests additionnels pour src.core.config sur lignes manquantes
"""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestCoreConfigAdditional:
    @patch.dict(os.environ, {"OPENAI_API_KEY": "x", "ANTHROPIC_API_KEY": "y", "DEEPSEEK_API_KEY": "z"}, clear=True)
    def test_get_available_models_all(self):
        import importlib

        import src.core.config as cfg

        cfg = importlib.reload(cfg)
        # Toutes les clés présentes -> tous les modèles disponibles
        models = cfg.Config.get_available_models()
        # Au moins 4 modèles spécifiés
        assert set(["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"]).issubset(set(models))

    @patch.dict(os.environ, {}, clear=True)
    def test_get_model_config_and_lists(self):
        import importlib

        import src.core.config as cfg

        cfg = importlib.reload(cfg)
        # get_model_config retourne un dict, get_all_model_names retourne une liste
        gpt4 = cfg.Config.get_model_config("GPT-4")
        assert isinstance(gpt4, dict) and gpt4.get("provider") == "openai"
        names = cfg.Config.get_all_model_names()
        assert "GPT-4o" in names and "DeepSeek" in names
