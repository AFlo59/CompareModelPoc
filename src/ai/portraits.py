"""
Génération de portraits optimisée avec gestionnaire d'API centralisé
"""

import logging
import os
from typing import List, Optional
from urllib.parse import quote_plus

from src.ai.api_client import get_openai_client

logger = logging.getLogger(__name__)


class PortraitGenerator:
    """Générateur de portraits avec gestion d'erreurs améliorée."""

    # Paramètres par défaut images (sans 'quality' pour éviter les doublons)
    DEFAULT_CONFIG = {"size": "1024x1024", "n": 1}
    PRIMARY_IMAGE_MODEL = "gpt-image-1"  # tentative prioritaire
    FALLBACK_IMAGE_MODEL = "dall-e-3"  # fallback si échec de la primaire

    @staticmethod
    def _build_prompt(name: str, description: Optional[str] = None, character_type: str = "personnage") -> str:
        """Construit un prompt optimisé pour DALL-E 3."""
        base_prompt = f"Portrait fantastique d'un {character_type} nommé {name.strip()}"

        if description and description.strip():
            base_prompt += f", {description.strip()}"
        else:
            base_prompt += ", apparence mystérieuse et charismatique"

        # Ajout de style et qualité
        style_additions = [
            "style artistique numérique",
            "haute qualité",
            "éclairage dramatique",
            "background flou",
            "art conceptuel",
        ]

        return f"{base_prompt}, {', '.join(style_additions)}"

    @classmethod
    def generate_character_portrait(cls, name: str, description: Optional[str] = None) -> Optional[str]:
        """Génère un portrait de personnage."""
        return cls._generate_portrait(name, description, "personnage de jeu de rôle")

    @classmethod
    def generate_gm_portrait(
        cls,
        campaign_theme: str = "fantasy",
        campaign_name: Optional[str] = None,
        secondary_themes: Optional[List[str]] = None,
        tone: Optional[str] = None,
        language: Optional[str] = None,
        model_name: Optional[str] = None,
        expression: Optional[str] = None,
        art_style: Optional[str] = None,
        campaign_description: Optional[str] = None,
    ) -> Optional[str]:
        """Génère un portrait de Maître du Jeu en tenant compte des métadonnées de la campagne.

        Tous les paramètres sont optionnels pour préserver la rétrocompatibilité avec les tests existants.
        """
        name = "Maître du Jeu"
        parts: List[str] = [f"sage et mystérieux dans un univers {campaign_theme}"]
        if campaign_name:
            parts.append(f"pour la campagne '{campaign_name}'")
        if secondary_themes:
            parts.append(f"thèmes secondaires: {', '.join(secondary_themes)}")
        if tone:
            parts.append(f"ton: {tone}")
        if language:
            parts.append(f"langue: {language}")
        if model_name:
            parts.append(f"modèle IA: {model_name}")
        if expression:
            parts.append(f"expression/humeur: {expression}")
        if art_style:
            parts.append(f"style artistique: {art_style}")
        if campaign_description:
            parts.append(f"contexte: {campaign_description}")

        description = ", ".join(parts)
        return cls._generate_portrait(name, description, "maître du jeu")

    @classmethod
    def _generate_portrait(
        cls, name: str, description: Optional[str] = None, character_type: str = "personnage"
    ) -> Optional[str]:
        """Génère un portrait avec gestion d'erreurs robuste.

        - Utilise DALL·E 3 si disponible
        - Fallback optionnel vers un avatar Dicebear (PNG) si l'API OpenAI n'est pas configurée ou échoue
        """
        if not name or not name.strip():
            logger.warning("Nom manquant pour la génération du portrait")
            return None

        try:
            prompt = cls._build_prompt(name, description, character_type)
            logger.info(f"Génération portrait pour '{name}' avec prompt: {prompt[:100]}...")

            client = get_openai_client()
            if client is None:
                logger.warning("[Portraits] Client OpenAI indisponible – fallback/placeholder")
                return cls._fallback_or_none(name)
            # 1) tentative via modèle gpt-image-1 (quality=high)
            try:
                response = client.images.generate(
                    prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, quality="high", **cls.DEFAULT_CONFIG
                )
                image_url = response.data[0].url
                logger.info("[Portraits] Succès gpt-image-1")
                return image_url
            except Exception as primary_err:
                logger.warning(f"[Portraits] Échec gpt-image-1: {primary_err}")
                # 2) fallback DALL·E 3 (quality=standard)
                response = client.images.generate(
                    prompt=prompt, model=cls.FALLBACK_IMAGE_MODEL, quality="standard", **cls.DEFAULT_CONFIG
                )
                image_url = response.data[0].url
                logger.info("[Portraits] Succès dall-e-3")
                return image_url

        except ValueError as e:
            # Erreur de configuration (clé API manquante)
            logger.error(f"Erreur de configuration pour '{name}': {e}")
            # Respect des tests: en cas de ValueError explicite, retourner None
            return None
        except Exception as e:
            # Autres erreurs (API, réseau, etc.) après tentative primaire + DALL·E
            logger.error(f"Erreur lors de la génération du portrait pour '{name}': {e}")
            message = str(e).lower()

            # Mode strict: placeholder toujours en DERNIER RECOURS si les deux modèles échouent
            # Activez via PORTRAIT_STRICT_LAST_RESORT=true
            strict_last_resort = os.getenv("PORTRAIT_STRICT_LAST_RESORT", "").lower() in ("1", "true", "on", "yes")

            # Heuristique par défaut: placeholder si quota/limite, sinon fallback contrôlé par env
            quota_signals = (
                "insufficient_quota",
                "too many requests",
                "429",
                "billing_hard_limit_reached",
                "billing",
            )

            if strict_last_resort:
                logger.warning("[Portraits] Strict last resort activé → placeholder")
                return cls._placeholder_portrait_url(name)

            if any(sig in message for sig in quota_signals):
                return cls._placeholder_portrait_url(name)

            return cls._fallback_or_none(name)

    @staticmethod
    def _placeholder_portrait_url(name: str) -> str:
        """Retourne une URL d'avatar de secours (Dicebear PNG) basée sur le nom."""
        seed = quote_plus(name.strip())
        return f"https://api.dicebear.com/7.x/adventurer/png?seed={seed}&size=256"

    @staticmethod
    def _fallback_or_none(name: str) -> Optional[str]:
        """Retourne une URL d'avatar seulement si le fallback est activé via env.

        Activez avec PORTRAIT_FALLBACK=true (ou 1/on/yes).
        """
        flag = os.getenv("PORTRAIT_FALLBACK", "").lower()
        if flag in ("1", "true", "on", "yes"):  # fallback activé explicitement
            return PortraitGenerator._placeholder_portrait_url(name)
        return None

    # Variantes qui retournent aussi le modèle utilisé (utile pour le tracking)
    @classmethod
    def generate_character_portrait_with_meta(
        cls, name: str, description: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str]]:
        if not name or not str(name).strip():
            return None, None
        prompt = cls._build_prompt(name, description, "personnage de jeu de rôle")
        try:
            client = get_openai_client()
            if client is None:
                return cls._fallback_or_none(name), None
            try:
                resp = client.images.generate(
                    prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, quality="high", **cls.DEFAULT_CONFIG
                )
                return resp.data[0].url, cls.PRIMARY_IMAGE_MODEL
            except Exception:
                resp = client.images.generate(
                    prompt=prompt, model=cls.FALLBACK_IMAGE_MODEL, quality="standard", **cls.DEFAULT_CONFIG
                )
                return resp.data[0].url, cls.FALLBACK_IMAGE_MODEL
        except Exception as e:
            msg = str(e).lower()
            if any(
                sig in msg
                for sig in ("insufficient_quota", "too many requests", "429", "billing_hard_limit_reached", "billing")
            ):
                return cls._placeholder_portrait_url(name), None
            return cls._fallback_or_none(name), None

    @classmethod
    def generate_gm_portrait_with_meta(
        cls,
        campaign_theme: str = "fantasy",
        campaign_name: Optional[str] = None,
        secondary_themes: Optional[List[str]] = None,
        tone: Optional[str] = None,
        language: Optional[str] = None,
        model_name: Optional[str] = None,
        expression: Optional[str] = None,
        art_style: Optional[str] = None,
        campaign_description: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        name = "Maître du Jeu"
        parts: List[str] = [f"sage et mystérieux dans un univers {campaign_theme}"]
        if campaign_name:
            parts.append(f"pour la campagne '{campaign_name}'")
        if secondary_themes:
            parts.append(f"thèmes secondaires: {', '.join(secondary_themes)}")
        if tone:
            parts.append(f"ton: {tone}")
        if language:
            parts.append(f"langue: {language}")
        if model_name:
            parts.append(f"modèle IA: {model_name}")
        if expression:
            parts.append(f"expression/humeur: {expression}")
        if art_style:
            parts.append(f"style artistique: {art_style}")
        if campaign_description:
            parts.append(f"contexte: {campaign_description}")
        prompt = cls._build_prompt(name, ", ".join(parts), "maître du jeu")
        try:
            client = get_openai_client()
            if client is None:
                return cls._fallback_or_none(name), None
            try:
                resp = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **cls.DEFAULT_CONFIG)
                return resp.data[0].url, cls.PRIMARY_IMAGE_MODEL
            except Exception:
                resp = client.images.generate(prompt=prompt, model=cls.FALLBACK_IMAGE_MODEL, **cls.DEFAULT_CONFIG)
                return resp.data[0].url, cls.FALLBACK_IMAGE_MODEL
        except Exception as e:
            msg = str(e).lower()
            if any(
                sig in msg
                for sig in ("insufficient_quota", "too many requests", "429", "billing_hard_limit_reached", "billing")
            ):
                return cls._placeholder_portrait_url(name), None
            return cls._fallback_or_none(name), None


# Fonctions d'accès simplifiées (rétrocompatibilité)
def generate_portrait(name: str, description: Optional[str] = None) -> Optional[str]:
    """Fonction de génération de portrait simplifiée."""
    return PortraitGenerator.generate_character_portrait(name, description)


def generate_gm_portrait(campaign_theme: str = "fantasy") -> Optional[str]:
    """Génère un portrait de Maître du Jeu."""
    return PortraitGenerator.generate_gm_portrait(campaign_theme)


# Fonctions avec métadonnées (URL, modèle utilisé)
def generate_portrait_with_meta(name: str, description: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    return PortraitGenerator.generate_character_portrait_with_meta(name, description)


def generate_gm_portrait_with_meta(
    campaign_theme: str = "fantasy",
    campaign_name: Optional[str] = None,
    secondary_themes: Optional[List[str]] = None,
    tone: Optional[str] = None,
    language: Optional[str] = None,
    model_name: Optional[str] = None,
    expression: Optional[str] = None,
    art_style: Optional[str] = None,
    campaign_description: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    return PortraitGenerator.generate_gm_portrait_with_meta(
        campaign_theme,
        campaign_name,
        secondary_themes,
        tone,
        language,
        model_name,
        expression,
        art_style,
        campaign_description,
    )
