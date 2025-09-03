"""
Configuration des modèles IA et paramètres
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


@dataclass
class ModelConfig:
    """Configuration d'un modèle IA."""

    name: str
    api_name: str
    provider: str
    max_tokens: int
    temperature_default: float
    cost_per_1k_input: float
    cost_per_1k_output: float
    description: str
    supports_system_messages: bool = True


class ModelProvider(Enum):
    """Fournisseurs de modèles IA."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"


# Configuration des modèles disponibles - TARIFS 2025 ACTUELS
AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    "GPT-4": ModelConfig(
        name="GPT-4",
        api_name="gpt-4",
        provider=ModelProvider.OPENAI.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.030,  # $30.00 per 1M tokens
        cost_per_1k_output=0.060,  # $60.00 per 1M tokens
        description="Le plus avancé, excellent pour la créativité et le raisonnement complexe",
    ),
    "GPT-4o": ModelConfig(
        name="GPT-4o",
        api_name="gpt-4o",
        provider=ModelProvider.OPENAI.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.0025,  # $2.50 per 1M tokens
        cost_per_1k_output=0.010,  # $10.00 per 1M tokens
        description="Version optimisée, 90% moins cher que GPT-4, contexte 128k",
    ),
    "Claude 3.5 Sonnet": ModelConfig(
        name="Claude 3.5 Sonnet",
        api_name="claude-3-5-sonnet-20240620",
        provider=ModelProvider.ANTHROPIC.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.003,  # $3.00 per 1M tokens
        cost_per_1k_output=0.015,  # $15.00 per 1M tokens
        description="Excellent pour le roleplay, contexte 200k tokens, narrateur expert",
    ),
    "DeepSeek V3": ModelConfig(
        name="DeepSeek V3",
        api_name="deepseek-chat",
        provider=ModelProvider.DEEPSEEK.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.00014,  # $0.14 per 1M tokens
        cost_per_1k_output=0.00028,  # $0.28 per 1M tokens
        description="Ultra-économique, 50x moins cher que GPT-4o, idéal pour tests massifs",
    ),
}


def get_model_config(model_name: str) -> ModelConfig:
    """Retourne la configuration d'un modèle."""
    # Gestion de la rétrocompatibilité pour DeepSeek
    if model_name == "DeepSeek":
        model_name = "DeepSeek V3"

    if model_name not in AVAILABLE_MODELS:
        # Fallback vers GPT-4
        return AVAILABLE_MODELS["GPT-4"]
    return AVAILABLE_MODELS[model_name]


def get_available_model_names() -> List[str]:
    """Retourne la liste des noms de modèles disponibles."""
    return list(AVAILABLE_MODELS.keys())


def get_alternative_models(current_model: str) -> List[str]:
    """Retourne une liste de modèles alternatifs quand le modèle actuel a des problèmes."""
    alternatives = []
    current_config = get_model_config(current_model)

    # Si le modèle actuel est OpenAI, suggérer des alternatives non-OpenAI
    if current_config.provider == ModelProvider.OPENAI.value:
        for model_name, config in AVAILABLE_MODELS.items():
            if config.provider != ModelProvider.OPENAI.value and model_name != current_model:
                alternatives.append(model_name)
    else:
        # Sinon, suggérer tous les autres modèles
        for model_name in AVAILABLE_MODELS.keys():
            if model_name != current_model:
                alternatives.append(model_name)

    # Trier par coût (les plus économiques en premier)
    alternatives.sort(key=lambda x: AVAILABLE_MODELS[x].cost_per_1k_input)
    return alternatives


def get_available_alternative_models(current_model: str) -> List[str]:
    """Retourne les modèles alternatifs qui ont des clés API disponibles."""
    from src.ai.api_client import APIClientManager

    api_status = APIClientManager.validate_api_keys()
    alternatives = get_alternative_models(current_model)

    available_alternatives = []
    for model_name in alternatives:
        config = AVAILABLE_MODELS[model_name]
        provider = config.provider

        # Vérifier si la clé API est disponible pour ce fournisseur
        if (
            (provider == ModelProvider.OPENAI.value and api_status["openai"])
            or (provider == ModelProvider.ANTHROPIC.value and api_status["anthropic"])
            or (provider == ModelProvider.DEEPSEEK.value and api_status["deepseek"])
        ):
            available_alternatives.append(model_name)

    return available_alternatives


def calculate_estimated_cost(model_name: str, tokens_in: int, tokens_out: int) -> float:
    """Calcule le coût estimé d'une requête."""
    config = get_model_config(model_name)
    cost_input = (tokens_in / 1000) * config.cost_per_1k_input
    cost_output = (tokens_out / 1000) * config.cost_per_1k_output
    return cost_input + cost_output


# Paramètres par défaut pour les conversations
CHAT_DEFAULTS = {
    "temperature": 0.8,
    "max_tokens": 1000,
    "timeout": 30,  # secondes
    "retry_attempts": 3,
    "retry_delay": 1.0,  # secondes
}
