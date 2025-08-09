"""
Génération de portraits optimisée avec gestionnaire d'API centralisé
"""

import logging
from typing import Optional

import os
from src.ai.api_client import get_openai_client
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class PortraitGenerator:
    """Générateur de portraits avec gestion d'erreurs améliorée."""
    
    # Paramètres par défaut pour DALL-E 3
    DEFAULT_CONFIG = {
        "model": "dall-e-3",
        "size": "1024x1024", 
        "quality": "standard",
        "n": 1
    }
    
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
            "art conceptuel"
        ]
        
        return f"{base_prompt}, {', '.join(style_additions)}"
    
    @classmethod
    def generate_character_portrait(cls, name: str, description: Optional[str] = None) -> Optional[str]:
        """Génère un portrait de personnage."""
        return cls._generate_portrait(name, description, "personnage de jeu de rôle")
    
    @classmethod
    def generate_gm_portrait(cls, campaign_theme: str = "fantasy") -> Optional[str]:
        """Génère un portrait de Maître du Jeu."""
        name = "Maître du Jeu"
        description = f"sage et mystérieux dans un univers {campaign_theme}"
        return cls._generate_portrait(name, description, "maître du jeu")
    
    @classmethod
    def _generate_portrait(cls, name: str, description: Optional[str] = None, character_type: str = "personnage") -> Optional[str]:
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
                return cls._fallback_or_none(name)
            response = client.images.generate(
                prompt=prompt,
                **cls.DEFAULT_CONFIG
            )
            
            image_url = response.data[0].url
            logger.info(f"Portrait généré avec succès pour '{name}'")
            return image_url
            
        except ValueError as e:
            # Erreur de configuration (clé API manquante)
            logger.error(f"Erreur de configuration pour '{name}': {e}")
            # Respect des tests: en cas de ValueError explicite, retourner None
            return None
        except Exception as e:
            # Autres erreurs (API, réseau, etc.)
            logger.error(f"Erreur lors de la génération du portrait pour '{name}': {e}")
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

# Fonctions d'accès simplifiées (rétrocompatibilité)
def generate_portrait(name: str, description: Optional[str] = None) -> Optional[str]:
    """Fonction de génération de portrait simplifiée."""
    return PortraitGenerator.generate_character_portrait(name, description)

def generate_gm_portrait(campaign_theme: str = "fantasy") -> Optional[str]:
    """Génère un portrait de Maître du Jeu."""
    return PortraitGenerator.generate_gm_portrait(campaign_theme)
