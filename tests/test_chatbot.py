import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Ajout du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot import (
    store_message,
    store_performance,
    get_last_model,
    get_previous_history
)


class TestChatbot:
    """Tests pour le module chatbot."""

    def test_store_message(self, sample_user, clean_db):
        """Test de stockage des messages avec campaign_id."""
        user_id = sample_user["id"]
        
        # Créer une campagne pour les tests
        from models import create_campaign
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")
        
        # Stocker un message
        store_message(user_id, "user", "Hello world!", campaign_id)
        
        # Vérifier en base
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, content, campaign_id FROM messages WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "user"
        assert result[1] == "Hello world!"
        assert result[2] == campaign_id

    def test_store_message_without_campaign(self, sample_user, clean_db):
        """Test de stockage des messages sans campaign_id."""
        user_id = sample_user["id"]
        
        # Stocker un message sans campaign_id
        store_message(user_id, "assistant", "Bonjour !")
        
        # Vérifier en base
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, content, campaign_id FROM messages WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "assistant"
        assert result[1] == "Bonjour !"
        assert result[2] is None

    def test_store_performance(self, sample_user, clean_db):
        """Test de stockage des performances avec campaign_id."""
        user_id = sample_user["id"]
        
        # Créer une campagne
        from models import create_campaign
        campaign_id = create_campaign(user_id, "Test Campaign", ["Fantasy"], "fr")
        
        # Stocker des données de performance
        store_performance(user_id, "GPT-4", 1.5, 100, 50, campaign_id)
        
        # Vérifier en base
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""SELECT model, latency, tokens_in, tokens_out, campaign_id 
                         FROM performance_logs WHERE user_id = ?""", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "GPT-4"
        assert result[1] == 1.5
        assert result[2] == 100
        assert result[3] == 50
        assert result[4] == campaign_id

    def test_get_last_model(self, sample_user, clean_db):
        """Test de récupération du dernier modèle choisi."""
        user_id = sample_user["id"]
        
        # Aucun modèle choisi - doit retourner GPT-4 par défaut
        model = get_last_model(user_id)
        assert model == "GPT-4"
        
        # Sauvegarder un modèle
        from models import save_model_choice
        save_model_choice(user_id, "Claude 3.5 Sonnet")
        
        # Vérifier la récupération
        model = get_last_model(user_id)
        assert model == "Claude 3.5 Sonnet"

    def test_get_previous_history(self, sample_user, clean_db):
        """Test de récupération de l'historique."""
        user_id = sample_user["id"]
        
        # Aucun historique au début
        history = get_previous_history(user_id)
        assert history == []
        
        # Ajouter quelques messages
        store_message(user_id, "user", "Message 1")
        store_message(user_id, "assistant", "Réponse 1")
        store_message(user_id, "user", "Message 2")
        
        # Récupérer l'historique
        history = get_previous_history(user_id)
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Message 1"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Réponse 1"
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "Message 2"

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-openai'})
    @patch('chatbot.get_openai_client')
    def test_call_ai_model_gpt4(self, mock_client):
        """Test d'appel du modèle GPT-4."""
        from chatbot import call_ai_model
        
        # Mock de la réponse OpenAI
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Appeler le modèle
        messages = [{"role": "user", "content": "Hello"}]
        result = call_ai_model("GPT-4", messages)
        
        # Vérifications
        assert result["content"] == "Test response"
        assert result["tokens_in"] == 10
        assert result["tokens_out"] == 20
        
        # Vérifier que le client a été appelé correctement
        mock_client_instance.chat.completions.create.assert_called_once()

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-anthropic'})
    @patch('chatbot.get_anthropic_client')
    def test_call_ai_model_claude(self, mock_client):
        """Test d'appel du modèle Claude."""
        from chatbot import call_ai_model
        
        # Mock de la réponse Anthropic
        mock_response = MagicMock()
        mock_response.content[0].text = "Claude response"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Appeler le modèle avec un message système
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        result = call_ai_model("Claude 3.5 Sonnet", messages)
        
        # Vérifications
        assert result["content"] == "Claude response"
        assert result["tokens_in"] == 15
        assert result["tokens_out"] == 25
        
        # Vérifier que le client a été appelé correctement
        mock_client_instance.messages.create.assert_called_once()

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-openai'})
    def test_call_ai_model_unsupported_fallback(self):
        """Test de fallback vers GPT-4 pour un modèle non supporté."""
        from chatbot import call_ai_model
        
        with patch('chatbot.get_openai_client') as mock_client:
            # Mock de la réponse OpenAI pour le fallback
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Fallback response"
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 10
            
            mock_client_instance = MagicMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # Appeler avec un modèle non supporté
            messages = [{"role": "user", "content": "Hello"}]
            result = call_ai_model("UnsupportedModel", messages)
            
            # Vérifications
            assert result["content"] == "Fallback response"
            assert result["tokens_in"] == 5
            assert result["tokens_out"] == 10


if __name__ == "__main__":
    pytest.main([__file__])
