"""
Tests d'intégration pour les APIs IA
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ai.chatbot import (
    APIManager,
    call_ai_model_optimized,
    ChatbotError,
    store_message_optimized,
    store_performance_optimized,
    launch_chat_interface_optimized,
)
from src.ai.portraits import PortraitGenerator


class TestAPIManagerIntegration:
    """Tests d'intégration pour le gestionnaire d'API."""

    @patch("src.ai.chatbot.get_openai_client")
    def test_call_openai_model_success(self, mock_get_client):
        """Test d'appel réussi à OpenAI."""
        # Configuration du mock
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock de la réponse OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Réponse de test"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_client.chat.completions.create.return_value = mock_response

        # Mock de la configuration du modèle
        from src.ai.models_config import ModelConfig

        model_config = ModelConfig(
            name="GPT-4",
            api_name="gpt-4",
            provider="openai",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            description="Test model",
        )

        messages = [{"role": "user", "content": "Hello"}]
        result = APIManager.call_openai_model(model_config, messages)

        assert result["content"] == "Réponse de test"
        assert result["tokens_in"] == 10
        assert result["tokens_out"] == 20
        assert result["model"] == "GPT-4"

        # Vérifier l'appel à l'API
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["messages"] == messages
        assert call_args.kwargs["temperature"] == 0.8
        assert call_args.kwargs["max_tokens"] == 1000

    @patch("src.ai.chatbot.get_openai_client")
    def test_call_openai_model_error(self, mock_get_client):
        """Test de gestion d'erreur OpenAI."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        from src.ai.models_config import ModelConfig

        model_config = ModelConfig(
            name="GPT-4",
            api_name="gpt-4",
            provider="openai",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            description="Test model",
        )

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(ChatbotError, match="Erreur OpenAI"):
            APIManager.call_openai_model(model_config, messages)

    @patch("src.ai.chatbot.get_anthropic_client")
    def test_call_anthropic_model_success(self, mock_get_client):
        """Test d'appel réussi à Anthropic."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock de la réponse Anthropic
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Réponse Claude"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        mock_client.messages.create.return_value = mock_response

        from src.ai.models_config import ModelConfig

        model_config = ModelConfig(
            name="Claude 3.5 Sonnet",
            api_name="claude-3-5-sonnet-20240620",
            provider="anthropic",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            description="Test model",
        )

        messages = [{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "Hello"}]

        result = APIManager.call_anthropic_model(model_config, messages)

        assert result["content"] == "Réponse Claude"
        assert result["tokens_in"] == 15
        assert result["tokens_out"] == 25
        assert result["model"] == "Claude 3.5 Sonnet"

        # Vérifier l'appel à l'API
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-5-sonnet-20240620"
        assert call_args.kwargs["system"] == "You are a helpful assistant"
        assert len(call_args.kwargs["messages"]) == 1  # Système séparé
        assert call_args.kwargs["messages"][0]["role"] == "user"

    @patch("src.ai.chatbot.get_anthropic_client")
    def test_call_anthropic_model_no_system_message(self, mock_get_client):
        """Test d'appel Anthropic sans message système."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Réponse sans système"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_client.messages.create.return_value = mock_response

        from src.ai.models_config import ModelConfig

        model_config = ModelConfig(
            name="Claude 3.5 Sonnet",
            api_name="claude-3-5-sonnet-20240620",
            provider="anthropic",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            description="Test model",
        )

        messages = [{"role": "user", "content": "Hello"}]

        result = APIManager.call_anthropic_model(model_config, messages)

        # Vérifier qu'un message système par défaut a été utilisé
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["system"] == "Tu es un assistant IA."

    @patch("src.ai.chatbot.get_anthropic_client")
    def test_call_anthropic_model_empty_messages(self, mock_get_client):
        """Test d'appel Anthropic avec messages vides."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Réponse par défaut"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 10
        mock_client.messages.create.return_value = mock_response

        from src.ai.models_config import ModelConfig

        model_config = ModelConfig(
            name="Claude 3.5 Sonnet",
            api_name="claude-3-5-sonnet-20240620",
            provider="anthropic",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            description="Test model",
        )

        messages = [{"role": "system", "content": "System prompt"}]

        result = APIManager.call_anthropic_model(model_config, messages)

        # Vérifier qu'un message utilisateur par défaut a été ajouté
        call_args = mock_client.messages.create.call_args
        assert len(call_args.kwargs["messages"]) == 1
        assert call_args.kwargs["messages"][0]["content"] == "Commençons l'aventure !"


class TestCallAIModelOptimized:
    """Tests pour la fonction principale d'appel IA optimisée."""

    @patch("src.ai.chatbot.APIManager.call_openai_model")
    @patch("src.ai.chatbot.get_model_config")
    def test_call_ai_model_optimized_openai(self, mock_get_config, mock_call_openai):
        """Test d'appel optimisé pour OpenAI."""
        from src.ai.models_config import ModelConfig, ModelProvider

        mock_config = ModelConfig(
            name="GPT-4",
            api_name="gpt-4",
            provider=ModelProvider.OPENAI.value,
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            description="Test",
        )
        mock_get_config.return_value = mock_config

        mock_call_openai.return_value = {"content": "OpenAI response", "tokens_in": 10, "tokens_out": 20, "model": "GPT-4"}

        messages = [{"role": "user", "content": "Test"}]
        result = call_ai_model_optimized("GPT-4", messages)

        assert result["content"] == "OpenAI response"
        mock_get_config.assert_called_once_with("GPT-4")
        mock_call_openai.assert_called_once_with(mock_config, messages, None)

    @patch("src.ai.chatbot.APIManager.call_anthropic_model")
    @patch("src.ai.chatbot.get_model_config")
    def test_call_ai_model_optimized_anthropic(self, mock_get_config, mock_call_anthropic):
        """Test d'appel optimisé pour Anthropic."""
        from src.ai.models_config import ModelConfig, ModelProvider

        mock_config = ModelConfig(
            name="Claude 3.5 Sonnet",
            api_name="claude-3-5-sonnet-20240620",
            provider=ModelProvider.ANTHROPIC.value,
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            description="Test",
        )
        mock_get_config.return_value = mock_config

        mock_call_anthropic.return_value = {
            "content": "Claude response",
            "tokens_in": 15,
            "tokens_out": 25,
            "model": "Claude 3.5 Sonnet",
        }

        messages = [{"role": "user", "content": "Test"}]
        result = call_ai_model_optimized("Claude 3.5 Sonnet", messages, temperature=0.9)

        assert result["content"] == "Claude response"
        mock_call_anthropic.assert_called_once_with(mock_config, messages, 0.9)

    @patch("src.ai.chatbot.APIManager.call_openai_model")
    @patch("src.ai.chatbot.get_model_config")
    def test_call_ai_model_optimized_fallback(self, mock_get_config, mock_call_openai):
        """Test de fallback vers GPT-4 pour modèle non supporté."""
        from src.ai.models_config import ModelConfig

        # Premier appel : modèle non supporté
        unsupported_config = ModelConfig(
            name="UnsupportedModel",
            api_name="unsupported",
            provider="unknown",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.02,
            description="Unsupported",
        )

        # Deuxième appel : fallback vers GPT-4
        fallback_config = ModelConfig(
            name="GPT-4",
            api_name="gpt-4",
            provider="openai",
            max_tokens=1000,
            temperature_default=0.8,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            description="Fallback",
        )

        mock_get_config.side_effect = [unsupported_config, fallback_config]

        mock_call_openai.return_value = {"content": "Fallback response", "tokens_in": 10, "tokens_out": 20, "model": "GPT-4"}

        messages = [{"role": "user", "content": "Test"}]
        result = call_ai_model_optimized("UnsupportedModel", messages)

        assert result["content"] == "Fallback response"
        # get_model_config doit être appelé deux fois (modèle original + fallback)
        assert mock_get_config.call_count == 2
        mock_call_openai.assert_called_once_with(fallback_config, messages, None)

    @patch("src.ai.chatbot.APIManager.call_openai_model")
    @patch("src.ai.chatbot.get_model_config")
    def test_call_ai_model_optimized_unexpected_error(self, mock_get_config, mock_call_openai):
        """Test de gestion d'erreur inattendue."""
        # Configurer un modèle valide mais l'appel API échoue avec une erreur inattendue
        from src.ai.models_config import ModelConfig, ModelProvider

        mock_config = ModelConfig(
            name="GPT-4",
            api_name="gpt-4",
            provider=ModelProvider.OPENAI.value,
            max_tokens=4000,
            temperature_default=0.7,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            description="GPT-4 model for testing",
            supports_system_messages=True,
        )
        mock_get_config.return_value = mock_config
        mock_call_openai.side_effect = Exception("API connection failed")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(ChatbotError, match="Erreur inattendue"):
            call_ai_model_optimized("GPT-4", messages)


class TestPortraitGeneratorIntegration:
    """Tests d'intégration pour le générateur de portraits."""

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_character_portrait_success(self, mock_get_client):
        """Test de génération réussie de portrait de personnage."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock de la réponse DALL-E
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://example.com/portrait.jpg"
        mock_client.images.generate.return_value = mock_response

        result = PortraitGenerator.generate_character_portrait("Aragorn", "grand et noble")

        assert result == "https://example.com/portrait.jpg"

        # Vérifier l'appel à DALL-E
        mock_client.images.generate.assert_called_once()
        call_args = mock_client.images.generate.call_args
        assert "Aragorn" in call_args.kwargs["prompt"]
        assert "grand et noble" in call_args.kwargs["prompt"]
        assert call_args.kwargs["model"] == "dall-e-3"
        assert call_args.kwargs["size"] == "1024x1024"

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_gm_portrait_success(self, mock_get_client):
        """Test de génération de portrait de Maître du Jeu."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://example.com/gm_portrait.jpg"
        mock_client.images.generate.return_value = mock_response

        result = PortraitGenerator.generate_gm_portrait("horror")

        assert result == "https://example.com/gm_portrait.jpg"

        # Vérifier que le thème est dans le prompt
        call_args = mock_client.images.generate.call_args
        assert "horror" in call_args.kwargs["prompt"]
        assert "Maître du Jeu" in call_args.kwargs["prompt"]

    def test_generate_portrait_empty_name(self):
        """Test avec nom vide."""
        result = PortraitGenerator.generate_character_portrait("")
        assert result is None

        result = PortraitGenerator.generate_character_portrait("   ")
        assert result is None

        result = PortraitGenerator.generate_character_portrait(None)
        assert result is None

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_api_error(self, mock_get_client):
        """Test de gestion d'erreur API."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.images.generate.side_effect = Exception("DALL-E error")

        result = PortraitGenerator.generate_character_portrait("Test Character")
        assert result is None

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_no_description(self, mock_get_client):
        """Test de génération sans description."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://example.com/default_portrait.jpg"
        mock_client.images.generate.return_value = mock_response

        result = PortraitGenerator.generate_character_portrait("Hero")

        assert result == "https://example.com/default_portrait.jpg"

        # Vérifier que la description par défaut est utilisée
        call_args = mock_client.images.generate.call_args
        assert "apparence mystérieuse et charismatique" in call_args.kwargs["prompt"]


if __name__ == "__main__":
    pytest.main([__file__])
