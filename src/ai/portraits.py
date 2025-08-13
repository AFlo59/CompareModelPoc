"""
Génération de portraits optimisée avec gestionnaire d'API centralisé et stockage local
"""

import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

import requests

from ..data.models import update_campaign_portrait, update_character_portrait
from .api_client import get_openai_client

logger = logging.getLogger(__name__)


class PortraitGenerator:
    """Générateur de portraits avec gestion d'erreurs améliorée et stockage local."""

    # Paramètres par défaut images
    DEFAULT_CONFIG = {"size": "1024x1024", "n": 1}

    # Priorité des modèles selon votre demande :
    # 1. dall-e-3 - primaire (modèle le plus récent avec quota, équivalent "gen-image-1")
    # 2. dall-e-2 - secondaire (fallback)
    # 3. template URL - fallback final
    PRIMARY_IMAGE_MODEL = "dall-e-3"  # modèle primaire (le plus récent)
    SECONDARY_IMAGE_MODEL = "dall-e-2"  # modèle secondaire

    # Dossiers de stockage local
    STATIC_DIR = Path("static/portraits")
    GM_DIR = STATIC_DIR / "gm"
    CHARACTERS_DIR = STATIC_DIR / "characters"

    # Configurations spécifiques par modèle pour éviter les erreurs 400
    MODEL_CONFIGS = {
        "dall-e-3": {"size": "1024x1024", "quality": "standard", "n": 1},  # DALL-E 3: quality=standard/hd
        "dall-e-2": {"size": "1024x1024", "n": 1},  # DALL-E 2: pas de paramètre quality
    }

    # Drapeau runtime: si quota/429 détecté sur dall-e-3, on évite de le retenter pendant la session
    _primary_disabled_due_to_quota: bool = False

    @classmethod
    def _ensure_directories(cls):
        """Crée les dossiers de stockage s'ils n'existent pas."""
        cls.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        cls.GM_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _download_and_save_image(cls, image_url: str, filename: str, subdirectory: str) -> Optional[str]:
        """
        Télécharge une image DALL-E et la sauvegarde localement.

        Args:
            image_url: URL temporaire de l'image DALL-E
            filename: Nom du fichier (sans extension)
            subdirectory: 'gm' ou 'characters'

        Returns:
            Chemin relatif de l'image sauvegardée ou None en cas d'erreur
        """
        try:
            cls._ensure_directories()

            # Déterminer le dossier de destination
            if subdirectory == "gm":
                target_dir = cls.GM_DIR
            elif subdirectory == "characters":
                target_dir = cls.CHARACTERS_DIR
            else:
                logger.error(f"Sous-dossier invalide: {subdirectory}")
                return None

            # Télécharger l'image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Sauvegarder avec extension .png
            file_path = target_dir / f"{filename}.png"
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Retourner le chemin relatif pour la BDD
            relative_path = f"static/portraits/{subdirectory}/{filename}.png"
            logger.info(f"Image sauvegardée: {relative_path}")
            return relative_path

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'image {filename}: {e}")
            return None

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
        return os.getenv(
            "PORTRAIT_FALLBACK_IMAGE_MODEL", cls.SECONDARY_IMAGE_MODEL
        )  # Changed from TERTIARY_IMAGE_MODEL to SECONDARY_IMAGE_MODEL

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
    def generate_character_portrait_with_save(
        cls,
        name: str,
        character_id: int,
        race: str,
        char_class: str,
        level: int = 1,
        gender: Optional[str] = None,
        description: Optional[str] = None,
        art_style: str = "Fantasy Réaliste",
        mood: str = "Neutre",
        campaign_context: Optional[str] = None,
    ) -> Optional[str]:
        """Génère un portrait de personnage avec toutes les infos du formulaire et le sauvegarde en BDD."""

        # Construction d'une description enrichie
        full_description_parts = []

        # Informations de base
        full_description_parts.append(f"{race} de niveau {level}")
        if gender:
            full_description_parts.append(f"de genre {gender}")
        full_description_parts.append(f"classe {char_class}")

        # Description personnalisée
        if description and description.strip():
            full_description_parts.append(description.strip())

        # Contexte de campagne
        if campaign_context:
            full_description_parts.append(f"dans un contexte de {campaign_context}")

        # Style et mood
        style_mapping = {
            "Fantasy Réaliste": "style fantasy réaliste, détaillé",
            "Anime/Manga": "style anime/manga, expressif",
            "Art Conceptuel": "style art conceptuel, artistique",
            "Peinture Classique": "style peinture classique, noble",
            "Illustration Moderne": "style illustration moderne, dynamique",
        }

        mood_mapping = {
            "Neutre": "expression neutre et équilibrée",
            "Déterminé": "regard déterminé et volontaire",
            "Mystérieux": "aura mystérieuse et énigmatique",
            "Jovial": "expression joyeuse et amicale",
            "Sombre": "expression sombre et intense",
            "Heroïque": "posture héroïque et noble",
            "Sage": "sagesse et sérénité dans le regard",
        }

        full_description_parts.append(style_mapping.get(art_style, "style fantasy réaliste"))
        full_description_parts.append(mood_mapping.get(mood, "expression équilibrée"))

        full_description = ", ".join(full_description_parts)

        portrait_url = cls._generate_portrait(name, full_description, "personnage de jeu de rôle")

        if portrait_url and not portrait_url.startswith("https://api.dicebear.com"):
            # Si c'est une URL DALL-E temporaire, la télécharger et la sauvegarder localement
            if portrait_url.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
                filename = f"character_{character_id}"
                local_path = cls._download_and_save_image(portrait_url, filename, "characters")
                if local_path:
                    portrait_url = local_path

            try:
                update_character_portrait(character_id, portrait_url)
                logger.info(f"Portrait personnage sauvegardé en BDD pour character_id={character_id}")
            except Exception as e:
                logger.error(f"Erreur sauvegarde portrait personnage: {e}")
        return portrait_url

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
    def generate_gm_portrait_with_save(
        cls,
        campaign_id: int,
        campaign_name: str,
        campaign_theme: str = "fantasy",
        secondary_themes: Optional[List[str]] = None,
        language: str = "Français",
        ai_model: str = "GPT-4o",
        art_style: str = "Fantasy Réaliste",
        expression: str = "Sage",
        campaign_description: Optional[str] = None,
    ) -> Optional[str]:
        """Génère un portrait de Maître du Jeu avec toutes les infos du formulaire et le sauvegarde en BDD."""

        # Construction d'une description enrichie du MJ
        gm_description_parts = []

        # Informations de base
        gm_description_parts.append(f"Maître du Jeu expérimenté pour la campagne '{campaign_name}'")
        gm_description_parts.append(f"spécialisé dans l'univers {campaign_theme}")

        # Thèmes secondaires
        if secondary_themes and len(secondary_themes) > 0:
            themes_str = ", ".join(secondary_themes)
            gm_description_parts.append(f"avec expertise en {themes_str}")

        # Langue et modèle IA (influence le style)
        gm_description_parts.append(f"maîtrisant parfaitement le {language}")
        if ai_model:
            gm_description_parts.append(f"utilisant l'IA {ai_model}")

        # Description de campagne
        if campaign_description and campaign_description.strip():
            gm_description_parts.append(campaign_description.strip())

        # Style artistique
        style_mapping = {
            "Fantasy Réaliste": "style fantasy réaliste, majestueux et détaillé",
            "Anime/Manga": "style anime/manga, expressif et charismatique",
            "Art Conceptuel": "style art conceptuel, mystique et artistique",
            "Peinture Classique": "style peinture classique, noble et intemporel",
            "Illustration Moderne": "style illustration moderne, dynamique et contemporain",
        }

        # Expression/humeur du MJ
        expression_mapping = {
            "Neutre": "expression bienveillante et équilibrée",
            "Déterminé": "regard déterminé et autoritaire",
            "Mystérieux": "aura mystérieuse et énigmatique de sage",
            "Jovial": "expression joviale et accueillante",
            "Sombre": "expression sombre et intense de mentor",
            "Heroïque": "posture héroïque et inspirante",
            "Sage": "sagesse profonde et sérénité dans le regard",
        }

        gm_description_parts.append(style_mapping.get(art_style, "style fantasy réaliste"))
        gm_description_parts.append(expression_mapping.get(expression, "sagesse et sérénité"))

        full_description = ", ".join(gm_description_parts)

        portrait_url = cls._generate_portrait("Maître du Jeu", full_description, "maître du jeu expérimenté")

        if portrait_url and not portrait_url.startswith("https://api.dicebear.com"):
            # Si c'est une URL DALL-E temporaire, la télécharger et la sauvegarder localement
            if portrait_url.startswith("https://oaidalleapiprodscus.blob.core.windows.net"):
                filename = f"gm_{campaign_id}"
                local_path = cls._download_and_save_image(portrait_url, filename, "gm")
                if local_path:
                    portrait_url = local_path

            try:
                update_campaign_portrait(campaign_id, portrait_url)
                logger.info(f"Portrait MJ sauvegardé en BDD pour campaign_id={campaign_id}")
            except Exception as e:
                logger.error(f"Erreur sauvegarde portrait MJ: {e}")
        return portrait_url

    @classmethod
    def _generate_portrait(
        cls, name: str, description: Optional[str] = None, character_type: str = "personnage"
    ) -> Optional[str]:
        """Génère un portrait avec gestion d'erreurs robuste.

        - Utilise dall-e-3 en primaire (modèle le plus récent avec quota)
        - Fallback vers dall-e-2 si échec
        - Fallback final vers template URL si tous les modèles échouent
        - Sauvegarde uniquement les portraits générés par IA (pas les templates)
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

            # 1) Tentative via modèle dall-e-3 (primaire)
            if not cls._primary_disabled_due_to_quota:
                try:
                    primary_config = cls.MODEL_CONFIGS.get(cls.PRIMARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                    response = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **primary_config)
                    image_url = response.data[0].url
                    logger.info(f"[Portraits] Succès {cls.PRIMARY_IMAGE_MODEL}")
                    return image_url
                except Exception as primary_err:
                    logger.warning(f"[Portraits] Échec {cls.PRIMARY_IMAGE_MODEL}: {primary_err}")
                    # Si l'erreur est un quota/429, désactiver dall-e-3 pour le reste de la session
                    if cls._is_quota_error(primary_err):
                        cls._primary_disabled_due_to_quota = True
                        logger.info(f"[Portraits] {cls.PRIMARY_IMAGE_MODEL} désactivé pour la session (quota dépassé)")

            # 2) Fallback vers dall-e-2
            try:
                dalle2_config = cls.MODEL_CONFIGS.get(cls.SECONDARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                response = client.images.generate(prompt=prompt, model=cls.SECONDARY_IMAGE_MODEL, **dalle2_config)
                image_url = response.data[0].url
                logger.info(f"[Portraits] Succès {cls.SECONDARY_IMAGE_MODEL}")
                return image_url
            except Exception as dalle2_err:
                logger.warning(f"[Portraits] Échec {cls.SECONDARY_IMAGE_MODEL}: {dalle2_err}")

            # 3) Tous les modèles ont échoué, utiliser le fallback template URL
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

            # 1) Tentative via dall-e-3 (primaire)
            if not cls._primary_disabled_due_to_quota:
                try:
                    primary_config = cls.MODEL_CONFIGS.get(cls.PRIMARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                    resp = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **primary_config)
                    return resp.data[0].url, cls.PRIMARY_IMAGE_MODEL
                except Exception as primary_err:
                    if cls._is_quota_error(primary_err):
                        cls._primary_disabled_due_to_quota = True

            # 2) Fallback vers dall-e-2
            try:
                dalle2_config = cls.MODEL_CONFIGS.get(cls.SECONDARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                resp = client.images.generate(prompt=prompt, model=cls.SECONDARY_IMAGE_MODEL, **dalle2_config)
                return resp.data[0].url, cls.SECONDARY_IMAGE_MODEL
            except Exception:
                pass

            # 3) Tous les modèles ont échoué
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

            # 1) Tentative via dall-e-3 (primaire)
            if not cls._primary_disabled_due_to_quota:
                try:
                    primary_config = cls.MODEL_CONFIGS.get(cls.PRIMARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                    resp = client.images.generate(prompt=prompt, model=cls.PRIMARY_IMAGE_MODEL, **primary_config)
                    return resp.data[0].url, cls.PRIMARY_IMAGE_MODEL
                except Exception as primary_err:
                    if cls._is_quota_error(primary_err):
                        cls._primary_disabled_due_to_quota = True

            # 2) Fallback vers dall-e-2
            try:
                dalle2_config = cls.MODEL_CONFIGS.get(cls.SECONDARY_IMAGE_MODEL, cls.DEFAULT_CONFIG)
                resp = client.images.generate(prompt=prompt, model=cls.SECONDARY_IMAGE_MODEL, **dalle2_config)
                return resp.data[0].url, cls.SECONDARY_IMAGE_MODEL
            except Exception:
                pass

            # 3) Tous les modèles ont échoué
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
