"""
Tests pour la configuration des modèles IA
"""

import os
import sys

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ai.models_config import (
    ModelConfig,
    ModelProvider,
    AVAILABLE_MODELS,
    get_model_config,
    get_available_model_names,
    calculate_estimated_cost,
    CHAT_DEFAULTS
)


class TestModelConfig:
    """Tests pour la classe ModelConfig."""

    def test_model_config_creation(self):
        """Test de création d'une configuration de modèle."""
        config = ModelConfig(
            name="Test Model",
            api_name="test-model",
            provider="test_provider",
            max_tokens=500,
            temperature_default=0.7,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.02,
            description="Un modèle de test"
        )
        
        assert config.name == "Test Model"
        assert config.api_name == "test-model"
        assert config.provider == "test_provider"
        assert config.max_tokens == 500
        assert config.temperature_default == 0.7
        assert config.cost_per_1k_input == 0.01
        assert config.cost_per_1k_output == 0.02
        assert config.description == "Un modèle de test"
        assert config.supports_system_messages is True  # Valeur par défaut

    def test_model_config_with_custom_system_support(self):
        """Test avec support système personnalisé."""
        config = ModelConfig(
            name="Test Model",
            api_name="test-model",
            provider="test_provider",
            max_tokens=500,
            temperature_default=0.7,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.02,
            description="Test",
            supports_system_messages=False
        )
        
        assert config.supports_system_messages is False


class TestModelProvider:
    """Tests pour l'énumération ModelProvider."""

    def test_model_providers(self):
        """Test des fournisseurs de modèles disponibles."""
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.DEEPSEEK.value == "deepseek"


class TestAvailableModels:
    """Tests pour les modèles disponibles."""

    def test_all_models_present(self):
        """Test que tous les modèles attendus sont présents."""
        expected_models = ["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"]
        assert set(AVAILABLE_MODELS.keys()) == set(expected_models)

    def test_gpt4_config(self):
        """Test de la configuration GPT-4."""
        config = AVAILABLE_MODELS["GPT-4"]
        assert config.name == "GPT-4"
        assert config.api_name == "gpt-4"
        assert config.provider == ModelProvider.OPENAI.value
        assert config.max_tokens == 1000
        assert config.temperature_default == 0.8
        assert config.cost_per_1k_input == 0.03
        assert config.cost_per_1k_output == 0.06

    def test_gpt4o_config(self):
        """Test de la configuration GPT-4o."""
        config = AVAILABLE_MODELS["GPT-4o"]
        assert config.name == "GPT-4o"
        assert config.api_name == "gpt-4o"
        assert config.provider == ModelProvider.OPENAI.value
        assert config.cost_per_1k_input == 0.005
        assert config.cost_per_1k_output == 0.015

    def test_claude_config(self):
        """Test de la configuration Claude."""
        config = AVAILABLE_MODELS["Claude 3.5 Sonnet"]
        assert config.name == "Claude 3.5 Sonnet"
        assert config.api_name == "claude-3-5-sonnet-20240620"
        assert config.provider == ModelProvider.ANTHROPIC.value
        assert config.cost_per_1k_input == 0.003
        assert config.cost_per_1k_output == 0.015

    def test_deepseek_config(self):
        """Test de la configuration DeepSeek."""
        config = AVAILABLE_MODELS["DeepSeek"]
        assert config.name == "DeepSeek"
        assert config.api_name == "deepseek-chat"
        assert config.provider == ModelProvider.DEEPSEEK.value
        assert config.cost_per_1k_input == 0.0001
        assert config.cost_per_1k_output == 0.0002


class TestModelConfigFunctions:
    """Tests pour les fonctions de configuration."""

    def test_get_model_config_existing(self):
        """Test de récupération d'une configuration existante."""
        config = get_model_config("GPT-4")
        assert config.name == "GPT-4"
        assert config.api_name == "gpt-4"

    def test_get_model_config_non_existing(self):
        """Test de récupération d'une configuration inexistante (fallback)."""
        config = get_model_config("ModelInexistant")
        # Doit retourner GPT-4 par défaut
        assert config.name == "GPT-4"
        assert config.api_name == "gpt-4"

    def test_get_available_model_names(self):
        """Test de récupération des noms de modèles disponibles."""
        names = get_available_model_names()
        expected = ["GPT-4", "GPT-4o", "Claude 3.5 Sonnet", "DeepSeek"]
        assert set(names) == set(expected)
        assert len(names) == 4

    def test_calculate_estimated_cost_gpt4(self):
        """Test de calcul de coût pour GPT-4."""
        cost = calculate_estimated_cost("GPT-4", 1000, 500)
        # 1000 * 0.03/1000 + 500 * 0.06/1000 = 0.03 + 0.03 = 0.06
        expected = 0.03 + 0.03
        assert cost == expected

    def test_calculate_estimated_cost_gpt4o(self):
        """Test de calcul de coût pour GPT-4o."""
        cost = calculate_estimated_cost("GPT-4o", 2000, 1000)
        # 2000 * 0.005/1000 + 1000 * 0.015/1000 = 0.01 + 0.015 = 0.025
        expected = 0.01 + 0.015
        assert cost == expected

    def test_calculate_estimated_cost_deepseek(self):
        """Test de calcul de coût pour DeepSeek (très économique)."""
        cost = calculate_estimated_cost("DeepSeek", 10000, 5000)
        # 10000 * 0.0001/1000 + 5000 * 0.0002/1000 = 0.001 + 0.001 = 0.002
        expected = 0.001 + 0.001
        assert cost == expected

    def test_calculate_estimated_cost_unknown_model(self):
        """Test de calcul de coût pour un modèle inconnu (fallback GPT-4)."""
        cost = calculate_estimated_cost("ModelInconnu", 1000, 500)
        # Doit utiliser les tarifs GPT-4
        expected = 0.03 + 0.03
        assert cost == expected

    def test_calculate_estimated_cost_zero_tokens(self):
        """Test avec zéro tokens."""
        cost = calculate_estimated_cost("GPT-4", 0, 0)
        assert cost == 0.0

    def test_calculate_estimated_cost_precision(self):
        """Test de précision des calculs."""
        cost = calculate_estimated_cost("Claude 3.5 Sonnet", 1500, 750)
        # 1500 * 0.003/1000 + 750 * 0.015/1000 = 0.0045 + 0.01125 = 0.01575
        expected = 0.0045 + 0.01125
        assert abs(cost - expected) < 1e-10  # Précision flottante


class TestChatDefaults:
    """Tests pour les paramètres par défaut."""

    def test_chat_defaults_present(self):
        """Test que tous les paramètres par défaut sont présents."""
        required_keys = ["temperature", "max_tokens", "timeout", "retry_attempts", "retry_delay"]
        for key in required_keys:
            assert key in CHAT_DEFAULTS

    def test_chat_defaults_values(self):
        """Test des valeurs par défaut."""
        assert CHAT_DEFAULTS["temperature"] == 0.8
        assert CHAT_DEFAULTS["max_tokens"] == 1000
        assert CHAT_DEFAULTS["timeout"] == 30
        assert CHAT_DEFAULTS["retry_attempts"] == 3
        assert CHAT_DEFAULTS["retry_delay"] == 1.0

    def test_chat_defaults_types(self):
        """Test des types des valeurs par défaut."""
        assert isinstance(CHAT_DEFAULTS["temperature"], (int, float))
        assert isinstance(CHAT_DEFAULTS["max_tokens"], int)
        assert isinstance(CHAT_DEFAULTS["timeout"], int)
        assert isinstance(CHAT_DEFAULTS["retry_attempts"], int)
        assert isinstance(CHAT_DEFAULTS["retry_delay"], (int, float))


if __name__ == "__main__":
    pytest.main([__file__])
