"""
Tests supplémentaires pour src.core.config afin d'augmenter la couverture
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestCoreConfig:
    def test_config_supported_models_structure(self):
        from src.core.config import Config

        models = Config.SUPPORTED_MODELS
        # Vérifier quelques clés essentielles
        for name in ["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"]:
            assert name in models
            cfg = models[name]
            assert "provider" in cfg and "model_name" in cfg and "cost_per_1k_tokens" in cfg

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_api_keys_none(self):
        # Dans certains environnements, un fichier .env peut être chargé.
        # On patch directement les attributs de Config pour contrôler le test.
        import src.core.config as cfg

        cfg.Config.OPENAI_API_KEY = None
        cfg.Config.ANTHROPIC_API_KEY = None
        cfg.Config.DEEPSEEK_API_KEY = None
        status = cfg.Config.validate_api_keys()
        assert status == {"openai": False, "anthropic": False, "deepseek": False}

    @patch.dict(os.environ, {"OPENAI_API_KEY": "x", "ANTHROPIC_API_KEY": "y"}, clear=True)
    def test_validate_api_keys_partial(self):
        import src.core.config as cfg

        # Forcer explicitement les attributs de classe pour ignorer des .env chargés
        cfg.Config.OPENAI_API_KEY = "x"
        cfg.Config.ANTHROPIC_API_KEY = "y"
        cfg.Config.DEEPSEEK_API_KEY = None
        status = cfg.Config.validate_api_keys()
        assert status["openai"] and status["anthropic"] and not status["deepseek"]

    @patch.dict(os.environ, {"OPENAI_API_KEY": "x", "ANTHROPIC_API_KEY": "y", "DEEPSEEK_API_KEY": "z"}, clear=True)
    def test_get_available_models_respects_keys(self):
        import importlib
        import src.core.config as cfg

        cfg = importlib.reload(cfg)
        names = cfg.Config.get_available_models()
        # Avec toutes les clés, tous les modèles doivent être disponibles
        assert set(names) == set(cfg.Config.SUPPORTED_MODELS.keys())
