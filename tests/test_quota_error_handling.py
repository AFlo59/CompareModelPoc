"""
Tests pour la gestion des erreurs de quota OpenAI
"""

import os
from unittest.mock import Mock, patch

import pytest

from src.ai.chatbot import ChatbotError, call_ai_model_optimized
from src.ai.models_config import get_alternative_models, get_available_alternative_models


class TestQuotaErrorHandling:
    """Tests pour la gestion améliorée des erreurs de quota."""

    def test_get_alternative_models_openai(self):
        """Test des alternatives pour un modèle OpenAI."""
        alternatives = get_alternative_models("GPT-4")

        # Doit exclure les modèles OpenAI
        assert "GPT-4o" not in alternatives
        assert "GPT-4" not in alternatives

        # Doit inclure les modèles non-OpenAI
        expected_alternatives = ["Claude 3.5 Sonnet", "DeepSeek"]
        for alt in expected_alternatives:
            assert alt in alternatives

    def test_get_alternative_models_non_openai(self):
        """Test des alternatives pour un modèle non-OpenAI."""
        alternatives = get_alternative_models("Claude 3.5 Sonnet")

        # Doit inclure tous les autres modèles
        expected_alternatives = ["GPT-4", "GPT-4o", "DeepSeek"]
        for alt in expected_alternatives:
            assert alt in alternatives

        assert "Claude 3.5 Sonnet" not in alternatives

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", "DEEPSEEK_API_KEY": "test-key"}, clear=False)
    def test_get_available_alternative_models(self):
        """Test des alternatives disponibles avec clés API."""
        alternatives = get_available_alternative_models("GPT-4")

        # Avec les clés API mockées, doit inclure Claude et DeepSeek
        assert "Claude 3.5 Sonnet" in alternatives
        assert "DeepSeek" in alternatives
        assert "GPT-4" not in alternatives
        assert "GPT-4o" not in alternatives

    @patch.dict(os.environ, {}, clear=True)
    def test_get_available_alternative_models_no_keys(self):
        """Test des alternatives sans clés API."""
        alternatives = get_available_alternative_models("GPT-4")

        # Sans clés API, aucune alternative n'est disponible
        assert len(alternatives) == 0

    @patch("src.ai.chatbot.get_openai_client")
    def test_openai_quota_error_detection(self, mock_get_client):
        """Test de détection des erreurs de quota OpenAI."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simuler une erreur de quota
        quota_error = Exception(
            "Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}"
        )
        mock_client.chat.completions.create.side_effect = quota_error

        with pytest.raises(ChatbotError) as exc_info:
            call_ai_model_optimized("GPT-4", [{"role": "user", "content": "Hello"}])

        error_message = str(exc_info.value)
        assert "Quota OpenAI dépassé" in error_message

    @patch("src.ai.chatbot.get_openai_client")
    def test_openai_billing_limit_error_detection(self, mock_get_client):
        """Test de détection des erreurs de limite de facturation OpenAI."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simuler une erreur de limite de facturation
        billing_error = Exception(
            "Error code: 400 - {'error': {'message': 'Billing hard limit has been reached', 'type': 'image_generation_user_error', 'param': None, 'code': 'billing_hard_limit_reached'}}"
        )
        mock_client.chat.completions.create.side_effect = billing_error

        with pytest.raises(ChatbotError) as exc_info:
            call_ai_model_optimized("GPT-4", [{"role": "user", "content": "Hello"}])

        error_message = str(exc_info.value)
        assert "Quota OpenAI dépassé" in error_message

    @patch("src.ai.chatbot.get_openai_client")
    def test_openai_rate_limit_error_detection(self, mock_get_client):
        """Test de détection des erreurs de rate limit OpenAI."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simuler une erreur de rate limit
        rate_limit_error = Exception("Error code: 429 - Rate limit exceeded")
        mock_client.chat.completions.create.side_effect = rate_limit_error

        with pytest.raises(ChatbotError) as exc_info:
            call_ai_model_optimized("GPT-4", [{"role": "user", "content": "Hello"}])

        error_message = str(exc_info.value)
        assert "Rate limit OpenAI" in error_message
