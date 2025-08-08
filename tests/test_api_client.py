"""
Tests pour le gestionnaire d'API centralisé
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ai.api_client import APIClientManager, get_openai_client, get_anthropic_client


class TestAPIClientManager:
    """Tests pour le gestionnaire d'API centralisé."""

    def setup_method(self):
        """Setup avant chaque test."""
        # Reset des clients pour chaque test
        APIClientManager._openai_client = None
        APIClientManager._anthropic_client = None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    @patch("src.ai.api_client.OpenAI")
    def test_get_openai_client_success(self, mock_openai):
        """Test de création réussie du client OpenAI."""
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Premier appel
        client1 = APIClientManager.get_openai_client()
        assert client1 == mock_client
        mock_openai.assert_called_once_with(api_key="test-openai-key")

        # Deuxième appel - doit utiliser le cache
        client2 = APIClientManager.get_openai_client()
        assert client2 == mock_client
        assert client1 is client2  # Même instance
        # OpenAI ne doit être appelé qu'une fois grâce au cache
        assert mock_openai.call_count == 1

    def test_get_openai_client_no_api_key(self):
        """Test de retour None quand la clé API OpenAI est manquante."""
        # Nettoyer le cache avant le test
        APIClientManager.get_openai_client.cache_clear()
        APIClientManager._openai_client = None
        
        # Supprimer explicitement toutes les clés API possibles
        env_clear = {key: "" for key in os.environ.keys() if 'API_KEY' in key}
        with patch.dict(os.environ, env_clear, clear=False):
            client = APIClientManager.get_openai_client()
            assert client is None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    @patch("src.ai.api_client.anthropic.Anthropic")
    def test_get_anthropic_client_success(self, mock_anthropic):
        """Test de création réussie du client Anthropic."""
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        client1 = APIClientManager.get_anthropic_client()
        assert client1 == mock_client
        mock_anthropic.assert_called_once_with(api_key="test-anthropic-key")

        # Test du cache
        client2 = APIClientManager.get_anthropic_client()
        assert client1 is client2
        assert mock_anthropic.call_count == 1

    def test_get_anthropic_client_no_api_key(self):
        """Test de retour None quand la clé API Anthropic est manquante."""
        # Nettoyer le cache avant le test
        APIClientManager.get_anthropic_client.cache_clear()
        APIClientManager._anthropic_client = None
        
        # Supprimer explicitement toutes les clés API possibles
        env_clear = {key: "" for key in os.environ.keys() if 'API_KEY' in key}
        with patch.dict(os.environ, env_clear, clear=False):
            client = APIClientManager.get_anthropic_client()
            assert client is None

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai",
        "ANTHROPIC_API_KEY": "test-anthropic",
        "DEEPSEEK_API_KEY": "test-deepseek"
    })
    def test_validate_api_keys_all_present(self):
        """Test de validation quand toutes les clés sont présentes."""
        status = APIClientManager.validate_api_keys()
        
        expected = {
            "openai": True,
            "anthropic": True,
            "deepseek": True
        }
        assert status == expected

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai"}, clear=True)
    def test_validate_api_keys_partial(self):
        """Test de validation avec seulement certaines clés."""
        status = APIClientManager.validate_api_keys()
        
        expected = {
            "openai": True,
            "anthropic": False,
            "deepseek": False
        }
        assert status == expected

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_api_keys_none(self):
        """Test de validation sans aucune clé."""
        status = APIClientManager.validate_api_keys()
        
        expected = {
            "openai": False,
            "anthropic": False,
            "deepseek": False
        }
        assert status == expected


class TestHelperFunctions:
    """Tests pour les fonctions d'aide."""

    @patch("src.ai.api_client.APIClientManager.get_openai_client")
    def test_get_openai_client_helper(self, mock_manager):
        """Test de la fonction helper get_openai_client."""
        mock_client = Mock()
        mock_manager.return_value = mock_client

        result = get_openai_client()
        assert result == mock_client
        mock_manager.assert_called_once()

    @patch("src.ai.api_client.APIClientManager.get_anthropic_client")
    def test_get_anthropic_client_helper(self, mock_manager):
        """Test de la fonction helper get_anthropic_client."""
        mock_client = Mock()
        mock_manager.return_value = mock_client

        result = get_anthropic_client()
        assert result == mock_client
        mock_manager.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
