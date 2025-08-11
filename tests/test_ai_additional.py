"""
Tests additionnels pour améliorer la couverture des modules AI
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestChatbotModule:
    """Tests pour améliorer la couverture du module chatbot."""

    def test_chatbot_error_class(self):
        """Test de la classe d'erreur ChatbotError."""
        from src.ai.chatbot import ChatbotError

        error = ChatbotError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_api_manager_init(self):
        """Test initialisation APIManager."""
        from src.ai.chatbot import APIManager

        api_manager = APIManager()

        # Le manager devrait être créé sans erreur
        assert api_manager is not None

    @patch("src.ai.chatbot.get_openai_client")
    @patch("src.ai.models_config.get_model_config")
    def test_call_ai_model_basic_flow(self, mock_get_config, mock_get_client):
        """Test flux basique call_ai_model."""
        from src.ai.chatbot import call_ai_model

        # Mock de la config du modèle
        mock_config = Mock()
        mock_config.provider = "openai"
        mock_config.api_name = "gpt-4"
        mock_config.temperature_default = 0.8
        mock_config.max_tokens = 4000
        mock_config.name = "GPT-4"
        mock_get_config.return_value = mock_config

        # Mock du client OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = call_ai_model("gpt-4", [{"role": "user", "content": "Hello"}], 0.8)

        assert result["content"] == "Test response"
        assert result["tokens_in"] == 50
        assert result["tokens_out"] == 100
        assert result["model"] == "GPT-4"

    @patch("src.ai.chatbot.get_openai_client")
    @patch("src.ai.models_config.get_model_config")
    def test_call_ai_model_error_handling(self, mock_get_config, mock_get_client):
        """Test gestion d'erreur call_ai_model."""
        from src.ai.chatbot import ChatbotError, call_ai_model

        # Mock de la config du modèle
        mock_config = Mock()
        mock_config.provider = "openai"
        mock_config.name = "GPT-4"
        mock_get_config.return_value = mock_config

        mock_get_client.side_effect = Exception("API Error")

        # Devrait lever une ChatbotError
        with pytest.raises(ChatbotError) as exc_info:
            call_ai_model("gpt-4", [{"role": "user", "content": "Hello"}])

        assert "Erreur inattendue" in str(exc_info.value)

    @patch("src.data.models.get_campaign_messages")
    def test_get_previous_history(self, mock_get_messages):
        """Test récupération historique précédent."""
        from src.ai.chatbot import get_previous_history

        mock_get_messages.return_value = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01 10:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01 10:00:01"},
        ]

        result = get_previous_history(1, 1)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        mock_get_messages.assert_called_once_with(1, 1, 50)


class TestPortraitsModule:
    """Tests pour améliorer la couverture du module portraits."""

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_basic(self, mock_get_client):
        """Test génération portrait basique."""
        from src.ai.portraits import generate_portrait

        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "http://example.com/image.jpg"
        mock_client.images.generate.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = generate_portrait("Test character", "A brave warrior")

        assert result == "http://example.com/image.jpg"
        mock_client.images.generate.assert_called_once()

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_error(self, mock_get_client):
        """Test génération portrait - erreur.

        Avec PORTRAIT_FALLBACK=true, même en cas d'erreur API,
        un template Dicebear est retourné en fallback.
        """
        from src.ai.portraits import generate_portrait

        mock_get_client.side_effect = Exception("API Error")

        result = generate_portrait("Test", "Description")

        # Avec le fallback activé, un template est retourné
        assert result is not None
        assert "dicebear.com" in result

    def test_generate_portrait_empty_name(self):
        """Test génération portrait - nom vide."""
        from src.ai.portraits import generate_portrait

        result = generate_portrait("", "Description")

        assert result is None

    @patch.dict("os.environ", {}, clear=True)
    def test_generate_portrait_no_description(self):
        """Test génération portrait - pas de description.

        Avec le nouveau comportement, en cas d'erreur de quota/billing sur OpenAI,
        le module retourne un avatar Dicebear en fallback automatique.
        Ici on simule un environnement sans variables qui conduit à `get_openai_client()` None
        et donc à un fallback contrôlé par PORTRAIT_FALLBACK (non défini -> None).
        """
        from src.ai.portraits import generate_portrait

        result = generate_portrait("Name", "")

        assert result is None


class TestApiClientModule:
    """Tests pour améliorer la couverture du module api_client."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_api_client_manager_init(self):
        """Test initialisation APIClientManager."""
        from src.ai.api_client import APIClientManager

        manager = APIClientManager()
        assert manager is not None

    @patch.dict("os.environ", {}, clear=True)
    def test_api_client_no_keys(self):
        """Test APIClientManager sans clés."""
        from src.ai.api_client import APIClientManager

        manager = APIClientManager()
        keys = manager.validate_api_keys()

        # Devrait détecter l'absence de clés - toutes devraient être False
        expected_keys = {"openai": False, "anthropic": False, "deepseek": False}
        assert keys == expected_keys
        assert not any(keys.values())


if __name__ == "__main__":
    pytest.main([__file__])
