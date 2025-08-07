"""
Configuration centralisée de l'application.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration de l'application."""
    
    # Base de données
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
    
    # APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    
    # Modèles supportés
    SUPPORTED_MODELS = {
        "GPT-4": {
            "provider": "openai",
            "model_name": "gpt-4",
            "description": "🚀 Le plus avancé, créatif et précis",
            "cost_per_1k_tokens": {"input": 0.03, "output": 0.06}
        },
        "GPT-4o": {
            "provider": "openai", 
            "model_name": "gpt-4o",
            "description": "⚡ Optimisé, rapide et économique",
            "cost_per_1k_tokens": {"input": 0.005, "output": 0.015}
        },
        "Claude 3.5 Sonnet": {
            "provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20240620",
            "description": "🎭 Excellent pour le roleplay et la narration", 
            "cost_per_1k_tokens": {"input": 0.003, "output": 0.015}
        },
        "DeepSeek": {
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "description": "💰 Le plus économique, bon rapport qualité/prix",
            "cost_per_1k_tokens": {"input": 0.00014, "output": 0.00028}
        }
    }
    
    # Paramètres de génération d'images
    IMAGE_CONFIG = {
        "model": "dall-e-3",
        "size": "1024x1024", 
        "quality": "standard"
    }
    
    # Paramètres de chat
    CHAT_CONFIG = {
        "max_tokens": 1000,
        "temperature": 0.8,
        "max_history_length": 50
    }
    
    # Interface utilisateur
    UI_CONFIG = {
        "page_title": "DnD AI GameMaster",
        "page_icon": "🎲",
        "layout": "wide",
        "themes": ["Fantasy", "Horreur", "Science-Fiction", "Mystère", "Aventure", "Politique", "Romance"],
        "classes": ["Guerrier", "Magicien", "Voleur", "Clerc", "Paladin", "Rôdeur", "Barde", "Barbare", "Sorcier", "Druide"],
        "races": ["Humain", "Elfe", "Nain", "Orc", "Demi-elfe", "Halfelin", "Tieffelin", "Gnome", "Dragonide"],
        "languages": [{"code": "fr", "name": "Français"}, {"code": "en", "name": "English"}]
    }
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Sécurité
    SECURITY_CONFIG = {
        "min_password_length": 8,
        "require_uppercase": True,
        "require_lowercase": True, 
        "require_digit": True,
        "bcrypt_rounds": 12
    }
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Récupère la configuration d'un modèle."""
        return cls.SUPPORTED_MODELS.get(model_name, {})
    
    @classmethod
    def get_all_model_names(cls) -> list:
        """Retourne tous les noms de modèles supportés."""
        return list(cls.SUPPORTED_MODELS.keys())
    
    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """Valide la présence des clés API."""
        return {
            "openai": bool(cls.OPENAI_API_KEY),
            "anthropic": bool(cls.ANTHROPIC_API_KEY),
            "deepseek": bool(cls.DEEPSEEK_API_KEY)
        }
    
    @classmethod
    def get_available_models(cls) -> list:
        """Retourne les modèles disponibles selon les clés API présentes."""
        api_status = cls.validate_api_keys()
        available = []
        
        for model_name, config in cls.SUPPORTED_MODELS.items():
            provider = config.get("provider")
            if api_status.get(provider, False):
                available.append(model_name)
        
        return available


# Instance globale de configuration
config = Config()
