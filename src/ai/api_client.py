"""
Gestionnaire d'API centralisé pour tous les services IA
"""

import logging
import os
from typing import Optional
from functools import lru_cache

import anthropic
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)


class APIClientManager:
    """Gestionnaire centralisé des clients API avec mise en cache."""

    _openai_client: Optional[OpenAI] = None
    _anthropic_client: Optional[anthropic.Anthropic] = None

    @classmethod
    @lru_cache(maxsize=1)
    def get_openai_client(cls) -> Optional[OpenAI]:
        """Retourne un client OpenAI mis en cache, ou None si clé manquante."""
        if cls._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY n'est pas définie dans les variables d'environnement")
                return None
            cls._openai_client = OpenAI(api_key=api_key)
            logger.info("Client OpenAI initialisé")
        return cls._openai_client

    @classmethod
    @lru_cache(maxsize=1)
    def get_anthropic_client(cls) -> Optional[anthropic.Anthropic]:
        """Retourne un client Anthropic mis en cache, ou None si clé manquante."""
        if cls._anthropic_client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY n'est pas définie dans les variables d'environnement")
                return None
            cls._anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info("Client Anthropic initialisé")
        return cls._anthropic_client

    @classmethod
    def validate_api_keys(cls) -> dict:
        """Valide toutes les clés API disponibles."""
        status = {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
        }

        available_count = sum(status.values())
        logger.info(f"Clés API disponibles : {available_count}/3")

        return status


# Fonctions d'accès simplifiées (rétrocompatibilité)
def get_openai_client() -> Optional[OpenAI]:
    """Fonction d'accès simple au client OpenAI."""
    return APIClientManager.get_openai_client()


def get_anthropic_client() -> Optional[anthropic.Anthropic]:
    """Fonction d'accès simple au client Anthropic."""
    return APIClientManager.get_anthropic_client()
