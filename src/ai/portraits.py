"""
Génération de portraits optimisée avec gestionnaire d'API centralisé
"""

import logging
import os
from typing import List, Optional
from urllib.parse import quote_plus

from .api_client import get_openai_client

logger = logging.getLogger(__name__)


class PortraitGenerator:
    """Générateur de portraits avec gestion d'erreurs améliorée."""

    # Paramètres par défaut images (éviter les champs non supportés)
    # Nota: certains endpoints d'images n'acceptent pas 'n' → on le retire
    DEFAULT_CONFIG = {"size": "1024x1024"}
    
    # Priorité des modèles selon votre demande :
    # 1. gen-image-1 (limité par quota) - primaire
    # 2. dall-e-3 - secondaire  
    # 3. dall-e-2 - tertiaire
    # 4. template URL - fallback final
    PRIMARY_IMAGE_MODEL = "gen-image-1"  # modèle primaire (limité par quota)
    SECONDARY_IMAGE_MODEL = "dall-e-3"   # modèle secondaire
    TERTIARY_IMAGE_MODEL = "dall-e-2"    # modèle tertiaire
    
    # Configurations spécifiques par modèle pour éviter les erreurs 400
    MODEL_CONFIGS = {
        "gen-image-1": {"size": "1024x1024", "quality": "high"},  # gen-image-1: quality=high supporté
        "dall-e-3": {"size": "1024x1024", "quality": "standard"},  # DALL-E 3: quality=standard uniquement
        "dall-e-2": {"size": "1024x1024"},  # DALL-E 2: pas de paramètre quality
    }
    
    # Drapeau runtime: si quota/429 détecté sur gen-image-1, on évite de le retenter pendant la session
    _primary_disabled_due_to_quota: bool = False

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
    def _get_primary_model(cls) -> str:
        return os.getenv("PORTRAIT_PRIMARY_IMAGE_MODEL", cls.PRIMARY_IMAGE_MODEL)

    @classmethod
    def _get_fallback_model(cls) -> str:
        return os.getenv("PORTRAIT_FALLBACK_IMAGE_MODEL", cls.SECONDARY_IMAGE_MODEL) # Changed from TERTIARY_IMAGE_MODEL to SECONDARY_IMAGE_MODEL

    @staticmethod
    def _is_quota_error(error: Exception) -> bool:
        message = str(error).lower()
        return any(
            sig in message
            for sig in (
                "insufficient_quota",
                "too many requests",
                "429",
                "billing_hard_limit_reached",
                "billing",
            )
        )

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

        - Utilise gen-image-1 en primaire (limité par quota)
        - Fallback vers dall-e-3 puis dall-e-2 si échec
        - Fallback final vers template URL si tous les modèles échouent
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

            # 1) Tentative via modèle gen-image-1 (limité par quota)
            if not cls._primary_disabled_due_to_quota:
                try:
                    primary_config = cls.MODEL_CONFIGS.get(cls.PRIMARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                    response = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **primary_config)
                    image_url = response.data[0].url
                    logger.info(f"[Portraits] Succès {cls.PRIMARY_IMAGE_MODEL}")
                    return image_url
                except Exception as primary_err:
                    logger.warning(f"[Portraits] Échec {cls.PRIMARY_IMAGE_MODEL}: {primary_err}")
                    # Si l'erreur est un quota/429, désactiver gen-image-1 pour le reste de la session
                    if cls._is_quota_error(primary_err):
                        cls._primary_disabled_due_to_quota = True
                        logger.info(f"[Portraits] {cls.PRIMARY_IMAGE_MODEL} désactivé pour la session (quota dépassé)")

            # 2) Fallback vers dall-e-3
            try:
                dalle3_config = cls.MODEL_CONFIGS.get(cls.SECONDARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                response = client.images.generate(prompt=prompt, model=cls.SECONDARY_IMAGE_MODEL, **dalle3_config)
                image_url = response.data[0].url
                logger.info(f"[Portraits] Succès {cls.SECONDARY_IMAGE_MODEL}")
                return image_url
            except Exception as dalle3_err:
                logger.warning(f"[Portraits] Échec {cls.SECONDARY_IMAGE_MODEL}: {dalle3_err}")

            # 3) Fallback vers dall-e-2
            try:
                dalle2_config = cls.MODEL_CONFIGS.get(cls.TERTIARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                response = client.images.generate(prompt=prompt, model=cls.TERTIARY_IMAGE_MODEL, **dalle2_config)
                image_url = response.data[0].url
                logger.info(f"[Portraits] Succès {cls.TERTIARY_IMAGE_MODEL}")
                return image_url
            except Exception as dalle2_err:
                logger.warning(f"[Portraits] Échec {cls.TERTIARY_IMAGE_MODEL}: {dalle2_err}")

            # 4) Tous les modèles ont échoué, utiliser le fallback template URL
            logger.warning("[Portraits] Tous les modèles d'IA ont échoué, utilisation du template URL")
            return cls._placeholder_portrait_url(name)

        except ValueError as e:
            # Erreur de configuration (clé API manquante)
            logger.error(f"Erreur de configuration pour '{name}': {e}")
            # Respect des tests: en cas de ValueError explicite, retourner None
            return None
        except Exception as e:
            # Autres erreurs (API, réseau, etc.) après tentative de tous les modèles
            logger.error(f"Erreur lors de la génération du portrait pour '{name}': {e}")
            # Par défaut: utiliser UNIQUEMENT le fallback contrôlé par env; le placeholder n'est qu'en dernier recours explicite
            strict_last_resort = os.getenv("PORTRAIT_STRICT_LAST_RESORT", "").lower() in ("1", "true", "on", "yes")
            if strict_last_resort:
                logger.warning("[Portraits] Strict last resort activé → placeholder")
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
            
            # 1) Tentative via gen-image-1
            if not cls._primary_disabled_due_to_quota:
                try:
                    primary_config = cls.MODEL_CONFIGS.get(cls.PRIMARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                    resp = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **primary_config)
                    return resp.data[0].url, cls.PRIMARY_IMAGE_MODEL
                except Exception as primary_err:
                    if cls._is_quota_error(primary_err):
                        cls._primary_disabled_due_to_quota = True
            
            # 2) Fallback vers dall-e-3
            try:
                dalle3_config = cls.MODEL_CONFIGS.get(cls.SECONDARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                resp = client.images.generate(prompt=prompt, model=cls.SECONDARY_IMAGE_MODEL, **dalle3_config)
                return resp.data[0].url, cls.SECONDARY_IMAGE_MODEL
            except Exception:
                pass
            
            # 3) Fallback vers dall-e-2
            try:
                dalle2_config = cls.MODEL_CONFIGS.get(cls.TERTIARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                resp = client.images.generate(prompt=prompt, model=cls.TERTIARY_IMAGE_MODEL, **dalle2_config)
                return resp.data[0].url, cls.TERTIARY_IMAGE_MODEL
            except Exception:
                pass
            
            # 4) Tous les modèles ont échoué
            return cls._placeholder_portrait_url(name), None
            
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
            
            # 1) Tentative via gen-image-1
            if not cls._primary_disabled_due_to_quota:
                try:
                    primary_config = cls.MODEL_CONFIGS.get(cls.PRIMARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                    resp = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **primary_config)
                    return resp.data[0].url, cls.PRIMARY_IMAGE_MODEL
                except Exception as primary_err:
                    if cls._is_quota_error(primary_err):
                        cls._primary_disabled_due_to_quota = True
            
            # 2) Fallback vers dall-e-3
            try:
                dalle3_config = cls.MODEL_CONFIGS.get(cls.SECONDARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                resp = client.images.generate(prompt=prompt, model=cls.SECONDARY_IMAGE_MODEL, **dalle3_config)
                return resp.data[0].url, cls.SECONDARY_IMAGE_MODEL
            except Exception:
                pass
            
            # 3) Fallback vers dall-e-2
            try:
                dalle2_config = cls.MODEL_CONFIGS.get(cls.TERTIARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                resp = client.images.generate(prompt=prompt, model=cls.TERTIARY_IMAGE_MODEL, **dalle2_config)
                return resp.data[0].url, cls.TERTIARY_IMAGE_MODEL
            except Exception:
                pass
            
            # 4) Tous les modèles ont échoué
            return cls._placeholder_portrait_url(name), None
            
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
