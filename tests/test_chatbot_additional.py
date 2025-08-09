"""
Tests supplémentaires pour couvrir les branches manquantes du module chatbot
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestChatbotAdditional:
    """Tests additionnels pour améliorer la couverture de src.ai.chatbot."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"})
    @patch("src.ai.chatbot.get_anthropic_client")
    def test_call_anthropic_model_exception(self, mock_client):
        """Couvre l'exception dans call_anthropic_model (lignes 89-91)."""
        from src.ai.models_config import get_model_config
        from src.ai.chatbot import call_ai_model, ChatbotError

        # Forcer le client Anthropic à lever une exception
        mock_client.return_value = Mock()
        mock_client.return_value.messages.create.side_effect = Exception("Anthropic down")

        with pytest.raises(ChatbotError) as exc:
            call_ai_model("Claude 3.5 Sonnet", [{"role": "user", "content": "Hi"}])

        assert "Erreur Anthrop".lower() in str(exc.value).lower() or "inattendue" in str(exc.value).lower()

    @patch("src.ai.chatbot.get_connection")
    @patch("src.ai.chatbot.st.warning")
    def test_store_message_optimized_error(self, mock_warning, mock_get_connection):
        """Couvre l'exception dans store_message_optimized (lignes 137-140)."""
        from src.ai.chatbot import store_message

        mock_get_connection.side_effect = Exception("DB error")

        # Ne doit pas lever d'exception et doit appeler st.warning
        store_message(1, "user", "content", 123)
        mock_warning.assert_called_once()

    @patch("src.ai.chatbot.get_connection")
    def test_store_performance_optimized_error(self, mock_get_connection):
        """Couvre le bloc except de store_performance_optimized (lignes 165-168)."""
        from src.ai.chatbot import store_performance

        mock_get_connection.side_effect = Exception("DB error")

        # Ne doit pas lever
        store_performance(1, "GPT-4", 1.0, 10, 5, 321)

    @patch("src.ai.chatbot.st.rerun")
    @patch("src.ai.chatbot.st.button")
    @patch("src.ai.chatbot.st.error")
    def test_launch_chat_interface_no_campaign(self, mock_error, mock_button, mock_rerun):
        """Couvre le early return quand aucune campagne (lignes 173-179)."""
        from src.ai.chatbot import launch_chat_interface
        import streamlit as st

        # Préparer un session_state vide
        st.session_state.clear()
        mock_button.return_value = False

        # Appel: doit afficher une erreur et retourner sans rerun
        launch_chat_interface(1)
        mock_error.assert_called_once()
        mock_rerun.assert_not_called()

    @patch("src.ai.chatbot.st.rerun")
    @patch("src.ai.chatbot.st.button")
    @patch("src.ai.chatbot.st.error")
    def test_launch_chat_interface_no_campaign_navigate(self, mock_error, mock_button, mock_rerun):
        """Couvre le bouton de navigation quand aucune campagne (lignes 175-177)."""
        from src.ai.chatbot import launch_chat_interface
        import streamlit as st

        st.session_state.clear()
        mock_button.return_value = True

        launch_chat_interface(1)
        # Doit avoir tenté une navigation
        assert st.session_state.get("page") == "campaign_or_resume"
        mock_rerun.assert_called_once()

    def test_alias_functions_forwarding(self):
        """Couvre les alias pour la rétrocompatibilité (lignes 269-283, 277-279)."""
        with patch("src.ai.chatbot.store_message_optimized") as sm, patch(
            "src.ai.chatbot.store_performance_optimized"
        ) as sp, patch("src.ai.chatbot.launch_chat_interface_optimized") as lci, patch(
            "src.ai.chatbot.call_ai_model_optimized"
        ) as cam:
            from src.ai.chatbot import store_message, store_performance, launch_chat_interface, call_ai_model

            store_message(1, "user", "hello", 1)
            sm.assert_called_once()

            store_performance(1, "GPT-4", 1.0, 10, 5, 1)
            sp.assert_called_once()

            launch_chat_interface(1)
            lci.assert_called_once_with(1)

            call_ai_model("GPT-4", [{"role": "user", "content": "hi"}], 0.5)
            cam.assert_called_once()

    @patch("src.data.models.get_campaign_messages", side_effect=Exception("boom"))
    def test_get_previous_history_exception(self, _mock_get_msgs):
        """Couvre la voie d'exception de get_previous_history (lignes 297-300)."""
        from src.ai.chatbot import get_previous_history

        result = get_previous_history(1, 2)
        assert result == []
