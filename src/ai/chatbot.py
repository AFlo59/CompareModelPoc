"""
Chatbot optimisé avec gestion d'erreurs et performance améliorées
"""

import logging
import time
from typing import Any, Dict, List, Optional

import streamlit as st

from src.ai.api_client import get_anthropic_client, get_deepseek_client, get_openai_client
from src.ai.models_config import CHAT_DEFAULTS, ModelProvider, calculate_estimated_cost, get_model_config
from src.data.database import get_connection

logger = logging.getLogger(__name__)


class ChatbotError(Exception):
    """Exception personnalisée pour les erreurs de chatbot."""

    pass


class APIManager:
    """Gestionnaire optimisé des appels API avec retry et timeout."""

    @staticmethod
    def call_openai_model(model_config, messages: List[Dict], temperature: float = None) -> Dict[str, Any]:
        """Appelle un modèle OpenAI avec gestion d'erreurs."""
        client = get_openai_client()
        temperature = temperature or model_config.temperature_default

        try:
            response = client.chat.completions.create(
                model=model_config.api_name,
                messages=messages,
                temperature=temperature,
                max_tokens=model_config.max_tokens,
                timeout=CHAT_DEFAULTS["timeout"],
            )

            return {
                "content": response.choices[0].message.content,
                "tokens_in": response.usage.prompt_tokens,
                "tokens_out": response.usage.completion_tokens,
                "model": model_config.name,
            }
        except Exception as e:
            logger.error(f"Erreur OpenAI pour {model_config.name}: {e}")
            raise ChatbotError(f"Erreur OpenAI: {str(e)}")

    @staticmethod
    def call_anthropic_model(model_config, messages: List[Dict], temperature: float = None) -> Dict[str, Any]:
        """Appelle un modèle Anthropic avec gestion d'erreurs."""
        client = get_anthropic_client()
        temperature = temperature or model_config.temperature_default

        try:
            # Séparer le message système des autres messages
            system_msg = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)

            # S'assurer qu'il y a au moins un message utilisateur
            if not user_messages:
                user_messages = [{"role": "user", "content": "Commençons l'aventure !"}]

            response = client.messages.create(
                model=model_config.api_name,
                max_tokens=model_config.max_tokens,
                temperature=temperature,
                system=system_msg if system_msg else "Tu es un assistant IA.",
                messages=user_messages,
                timeout=CHAT_DEFAULTS["timeout"],
            )

            return {
                "content": response.content[0].text,
                "tokens_in": response.usage.input_tokens,
                "tokens_out": response.usage.output_tokens,
                "model": model_config.name,
            }
        except Exception as e:
            logger.error(f"Erreur Anthropic pour {model_config.name}: {e}")
            raise ChatbotError(f"Erreur Anthropic: {str(e)}")

    @staticmethod
    def call_deepseek_model(model_config, messages: List[Dict], temperature: float = None) -> Dict[str, Any]:
        """Appelle un modèle DeepSeek (API compatible OpenAI)."""
        client = get_deepseek_client()
        if client is None:
            raise ChatbotError("Clé API DeepSeek manquante")

        temperature = temperature or model_config.temperature_default

        try:
            response = client.chat.completions.create(
                model=model_config.api_name,
                messages=messages,
                temperature=temperature,
                max_tokens=model_config.max_tokens,
                timeout=CHAT_DEFAULTS["timeout"],
            )

            return {
                "content": response.choices[0].message.content,
                "tokens_in": response.usage.prompt_tokens,
                "tokens_out": response.usage.completion_tokens,
                "model": model_config.name,
            }
        except Exception as e:
            logger.error(f"Erreur DeepSeek pour {model_config.name}: {e}")
            raise ChatbotError(f"Erreur DeepSeek: {str(e)}")


def call_ai_model_optimized(model_name: str, messages: List[Dict], temperature: float = None) -> Dict[str, Any]:
    """
    Appelle le modèle d'IA approprié avec gestion optimisée.

    Args:
        model_name: Nom du modèle à utiliser
        messages: Liste des messages de conversation
        temperature: Température pour la génération (optionnel)

    Returns:
        Dict contenant 'content', 'tokens_in', 'tokens_out', 'model'

    Raises:
        ChatbotError: En cas d'erreur dans l'appel API
    """
    model_config = get_model_config(model_name)

    try:
        if model_config.provider == ModelProvider.OPENAI.value:
            return APIManager.call_openai_model(model_config, messages, temperature)
        elif model_config.provider == ModelProvider.ANTHROPIC.value:
            return APIManager.call_anthropic_model(model_config, messages, temperature)
        elif model_config.provider == ModelProvider.DEEPSEEK.value:
            return APIManager.call_deepseek_model(model_config, messages, temperature)
        else:
            # Fallback vers GPT-4 pour les modèles non supportés
            logger.warning(f"Modèle {model_name} non supporté, fallback vers GPT-4")
            fallback_config = get_model_config("GPT-4")
            return APIManager.call_openai_model(fallback_config, messages, temperature)

    except ChatbotError:
        raise  # Re-raise les erreurs de chatbot
    except Exception as e:
        logger.error(f"Erreur inattendue avec le modèle {model_name}: {e}")
        raise ChatbotError(f"Erreur inattendue: {str(e)}")


def store_message_optimized(user_id: int, role: str, content: str, campaign_id: Optional[int] = None) -> None:
    """Stocke un message avec gestion d'erreurs optimisée."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (user_id, role, content, campaign_id) VALUES (?, ?, ?, ?)",
                (user_id, role, content, campaign_id),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Erreur stockage message: {e}")
        # Ne pas propager l'erreur pour ne pas casser l'expérience utilisateur
        st.warning("Message non sauvegardé (erreur technique)")


def store_performance_optimized(
    user_id: int, model: str, latency: float, tokens_in: int, tokens_out: int, campaign_id: Optional[int] = None
) -> None:
    """Stocke les données de performance avec calcul de coût."""
    try:
        estimated_cost = calculate_estimated_cost(model, tokens_in, tokens_out)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO performance_logs 
                   (user_id, model, latency, tokens_in, tokens_out, campaign_id) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, model, latency, tokens_in, tokens_out, campaign_id),
            )
            conn.commit()

        logger.info(f"Performance enregistrée: {model}, {latency:.2f}s, coût estimé: ${estimated_cost:.4f}")
    except Exception as e:
        logger.error(f"Erreur stockage performance: {e}")
        # Ne pas propager l'erreur


def launch_chat_interface_optimized(user_id: int) -> None:
    """Interface de chat optimisée avec gestion d'erreurs améliorée."""

    # Vérification de la campagne
    if "campaign" not in st.session_state or not st.session_state.campaign:
        st.error("❌ Aucune campagne sélectionnée")
        if st.button("🏰 Choisir une campagne"):
            st.session_state.page = "campaign_or_resume"
            st.rerun()
        return

    campaign = st.session_state.campaign
    campaign_id = campaign.get("id")

    # Déterminer le modèle automatiquement (campagne -> préférence utilisateur -> défaut)
    try:
        from src.data.models import get_user_model_choice

        user_pref = get_user_model_choice(user_id)
    except Exception:
        user_pref = None

    model = campaign.get("ai_model") or user_pref or "GPT-4"
    model_config = get_model_config(model)
    # Afficher une métrique informative plutôt qu'un sélecteur
    info_col1, info_col2 = st.columns([3, 1])
    with info_col1:
        st.caption(f"🤖 Modèle actif: {model}")
    with info_col2:
        st.metric("💰 Coût/1K tokens", f"${model_config.cost_per_1k_input:.3f}")

    # Initialisation de l'historique
    if "history" not in st.session_state:
        st.session_state.history = []

    # Démarrage automatique si demandé (auto_start_intro)
    auto_trigger = False
    try:
        auto_trigger = bool(getattr(st.session_state, "auto_start_intro", False) or st.session_state.get("auto_start_intro"))
    except Exception:
        auto_trigger = False

    # Affichage de l'historique AVANT, champ de saisie APRÈS
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Champ de saisie (en bas)
    prompt = st.chat_input("Votre action ?")
    user_submitted = bool(prompt)

    if auto_trigger or user_submitted:
        if auto_trigger:
            # Retirer le flag pour ne pas boucler
            try:
                st.session_state.auto_start_intro = False
            except Exception:
                try:
                    st.session_state["auto_start_intro"] = False
                except Exception:
                    pass
            # Si l'historique initial n'a pas été persisté (changement de page rapide), persister en tâche de fond
            try:
                from src.data.models import get_campaign_messages

                messages = get_campaign_messages(user_id, campaign_id, 2)
                if not messages:
                    # Reconstituer les deux premiers messages si absents
                    store_message_optimized(
                        user_id,
                        "system",
                        "Tu es un MJ immersif, concis quand nécessaire, et tu avances l'histoire scène par scène.",
                        campaign_id,
                    )
                    # Reprendre le dernier user prompt d'intro depuis le state si possible
                    try:
                        intro_msg = next((m["content"] for m in st.session_state.history if m["role"] == "user"), None)
                    except Exception:
                        intro_msg = None
                    if intro_msg:
                        store_message_optimized(user_id, "user", intro_msg, campaign_id)
            except Exception:
                pass
        else:
            # Afficher et stocker le message utilisateur saisi
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.history.append({"role": "user", "content": prompt})
            store_message_optimized(user_id, "user", prompt, campaign_id)

        # Générer la réponse
        with st.spinner("🎲 Le Maître du Jeu réfléchit..."):
            try:
                start_time = time.time()
                ai_response = call_ai_model_optimized(model, st.session_state.history)
                latency = time.time() - start_time

                reply = ai_response["content"]

                # Stocker les performances
                store_performance_optimized(
                    user_id, model, latency, ai_response["tokens_in"], ai_response["tokens_out"], campaign_id
                )

                # Afficher des métriques en temps réel
                cost = calculate_estimated_cost(model, ai_response["tokens_in"], ai_response["tokens_out"])
                st.caption(f"⚡ {latency:.2f}s | 🎫 {ai_response['tokens_out']} tokens | 💰 ${cost:.4f}")

            except ChatbotError as e:
                reply = f"❌ **Erreur technique :** {str(e)}\n\nVeuillez réessayer ou changer de modèle."
                logger.error(f"Erreur ChatbotError: {e}")
            except Exception as e:
                reply = f"❌ **Erreur inattendue :** Une erreur s'est produite.\n\nVeuillez réessayer."
                logger.error(f"Erreur inattendue dans chat: {e}")

        # Afficher la réponse et sauvegarder
        with st.chat_message("assistant"):
            st.markdown(reply)

        st.session_state.history.append({"role": "assistant", "content": reply})
        store_message_optimized(user_id, "assistant", reply, campaign_id)

        # Forcer un rerun pour ré-afficher l'historique AU-DESSUS du champ d'entrée
        # (sinon, la première réponse peut apparaître sous la zone input lors du déclenchement auto)
        try:
            st.rerun()
        except Exception:
            pass


# ========================================
# ALIASES POUR RÉTROCOMPATIBILITÉ TESTS
# ========================================


def store_message(user_id: int, role: str, content: str, campaign_id: Optional[int] = None) -> None:
    """Alias pour rétrocompatibilité avec les tests."""
    return store_message_optimized(user_id, role, content, campaign_id)


def store_performance(
    user_id: int, model: str, latency: float, tokens_in: int, tokens_out: int, campaign_id: Optional[int] = None
) -> None:
    """Alias pour rétrocompatibilité avec les tests."""
    return store_performance_optimized(user_id, model, latency, tokens_in, tokens_out, campaign_id)


def launch_chat_interface(user_id: int) -> None:
    """Alias pour rétrocompatibilité avec les tests."""
    return launch_chat_interface_optimized(user_id)


def call_ai_model(model: str, messages: List[Dict], temperature: float = 0.8) -> Dict[str, Any]:
    """Alias pour rétrocompatibilité avec les tests."""
    return call_ai_model_optimized(model, messages, temperature)


# Fonctions manquantes pour les tests (implémentations simples)
def get_last_model(user_id: int) -> Optional[str]:
    """Récupère le dernier modèle utilisé par l'utilisateur."""
    try:
        from src.data.models import get_user_model_choice

        return get_user_model_choice(user_id)
    except:
        return "GPT-4"


def get_previous_history(user_id: int, campaign_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """Récupère l'historique des messages précédents."""
    try:
        from src.data.models import get_campaign_messages

        return get_campaign_messages(user_id, campaign_id, limit)
    except:
        return []
