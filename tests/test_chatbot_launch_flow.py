"""
Tests de flux pour src.ai.chatbot.launch_chat_interface_optimized
"""

import os
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _ctx():
    c = Mock()
    c.__enter__ = Mock(return_value=c)
    c.__exit__ = Mock(return_value=None)
    return c


class SessionLike(dict):
    def __getattr__(self, k):
        if k in self:
            return self[k]
        raise AttributeError(k)

    def __setattr__(self, k, v):
        self[k] = v

    def __contains__(self, key):
        return dict.__contains__(self, key)


class TestChatbotLaunchFlow:
    @patch("src.ai.chatbot.st")
    @patch("src.data.models.get_user_model_choice", side_effect=Exception("boom"))
    def test_history_display_and_default_model_fallback(self, _mock_choice, mock_st):
        from src.ai.chatbot import launch_chat_interface

        # Préparer un historique existant pour couvrir l'affichage (lignes 215-216)
        sess = SessionLike()
        sess.campaign = {"id": 9}
        sess.history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        mock_st.session_state = sess

        # UI sans saisie utilisateur
        mock_st.columns.side_effect = lambda spec: [_ctx() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.selectbox.return_value = "GPT-4"  # peu importe ici
        mock_st.chat_input.return_value = None
        mock_st.chat_message.side_effect = lambda role: _ctx()

        # L'appel ne doit pas lever et doit parcourir l'historique
        launch_chat_interface(1)

    @patch("src.ai.chatbot.calculate_estimated_cost", return_value=0.1234)
    @patch("src.ai.chatbot.store_performance_optimized")
    @patch("src.ai.chatbot.store_message_optimized")
    @patch("src.ai.chatbot.call_ai_model_optimized")
    @patch("src.ai.chatbot.st")
    def test_launch_happy_path(self, mock_st, mock_call, mock_store_msg, mock_store_perf, _mock_cost):
        from src.ai.chatbot import launch_chat_interface

        # Préparer session_state avec une campagne sélectionnée
        sess = SessionLike()
        sess.campaign = {"id": 1, "name": "Camp"}
        mock_st.session_state = sess

        # UI mocks
        mock_st.columns.side_effect = lambda spec: [_ctx() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.selectbox.return_value = "GPT-4"
        mock_st.metric = Mock()
        mock_st.chat_input.return_value = "hello"
        mock_st.chat_message.side_effect = lambda role: _ctx()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=_ctx())
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)

        # Appel modèle IA simulé
        mock_call.return_value = {
            "content": "reply",
            "tokens_in": 10,
            "tokens_out": 5,
            "model": "GPT-4",
        }

        launch_chat_interface(123)

        # Vérifications principales
        assert mock_store_msg.call_count == 2  # user puis assistant
        mock_store_perf.assert_called_once()
        mock_st.caption.assert_called()

    @patch("src.ai.chatbot.store_message_optimized")
    @patch("src.ai.chatbot.call_ai_model_optimized")
    @patch("src.ai.chatbot.st")
    def test_launch_chatbot_error(self, mock_st, mock_call, mock_store_msg):
        from src.ai.chatbot import ChatbotError, launch_chat_interface

        sess = SessionLike()
        sess.campaign = {"id": 2}
        mock_st.session_state = sess
        mock_st.columns.side_effect = lambda spec: [_ctx() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.selectbox.return_value = "GPT-4"
        mock_st.chat_input.return_value = "hello"
        mock_st.chat_message.side_effect = lambda role: _ctx()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=_ctx())
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)

        mock_call.side_effect = ChatbotError("oops")

        launch_chat_interface(1)

        # La seconde sauvegarde (assistant) doit contenir un message d'erreur résumé
        args_list = mock_store_msg.call_args_list
        assert len(args_list) == 2
        assert "Erreur AI" in args_list[1].args[2]  # Message résumé d'erreur

    @patch("src.ai.chatbot.store_message_optimized")
    @patch("src.ai.chatbot.call_ai_model_optimized")
    @patch("src.ai.chatbot.st")
    def test_launch_generic_exception(self, mock_st, mock_call, mock_store_msg):
        from src.ai.chatbot import launch_chat_interface

        sess = SessionLike()
        sess.campaign = {"id": 3}
        mock_st.session_state = sess
        mock_st.columns.side_effect = lambda spec: [_ctx() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.selectbox.return_value = "GPT-4"
        mock_st.chat_input.return_value = "hello"
        mock_st.chat_message.side_effect = lambda role: _ctx()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=_ctx())
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)

        mock_call.side_effect = Exception("crash")

        launch_chat_interface(1)

        args_list = mock_store_msg.call_args_list
        assert len(args_list) == 2
        assert "Erreur AI" in args_list[1].args[2]  # Message résumé d'erreur
