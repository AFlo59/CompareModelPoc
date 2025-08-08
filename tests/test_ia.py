import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ai.portraits import generate_portrait, get_openai_client


class TestPortraitGeneration:
    """Tests pour la génération de portraits."""

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_success(self, mock_get_client):
        """Test de génération réussie d'un portrait."""
        # Configuration du mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].url = "https://mocked.url/portrait.png"
        mock_client.images.generate.return_value = mock_response

        # Test
        url = generate_portrait("Elric", "cheveux blancs, yeux dorés")

        # Vérifications
        assert url == "https://mocked.url/portrait.png"
        mock_client.images.generate.assert_called_once()

        # Vérifier les paramètres de l'appel
        call_args = mock_client.images.generate.call_args
        assert "dall-e-3" in str(call_args)
        assert "Elric" in str(call_args)

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_api_error(self, mock_get_client):
        """Test de gestion d'erreur API."""
        # Configuration du mock pour lever une exception
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.images.generate.side_effect = Exception("API error")

        # Test
        url = generate_portrait("Elric", "description inutile")

        # Vérifications
        assert url is None

    def test_generate_portrait_empty_name(self):
        """Test avec un nom vide."""
        url = generate_portrait("", "description")
        assert url is None

        url = generate_portrait("   ", "description")
        assert url is None

        url = generate_portrait(None, "description")
        assert url is None

    @patch("src.ai.portraits.get_openai_client")
    def test_generate_portrait_no_description(self, mock_get_client):
        """Test sans description."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].url = "https://example.com/image.png"
        mock_client.images.generate.return_value = mock_response

        url = generate_portrait("TestCharacter")
        assert url == "https://example.com/image.png"

    @patch("src.ai.api_client.os.getenv")
    def test_get_openai_client_no_api_key(self, mock_getenv):
        """Test d'initialisation du client sans clé API."""
        mock_getenv.return_value = None

        with pytest.raises(ValueError, match="OPENAI_API_KEY n'est pas définie"):
            get_openai_client()

    @patch("src.ai.api_client.os.getenv")
    @patch("src.ai.api_client.OpenAI")
    def test_get_openai_client_success(self, mock_openai, mock_getenv):
        """Test d'initialisation réussie du client."""
        mock_getenv.return_value = "test-api-key"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        client = get_openai_client()

        assert client == mock_client
        mock_openai.assert_called_once_with(api_key="test-api-key")


if __name__ == "__main__":
    pytest.main([__file__])
