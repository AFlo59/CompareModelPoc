"""
Configuration des modèles IA et paramètres
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

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

# Configuration des modèles disponibles
AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    "GPT-4": ModelConfig(
        name="GPT-4",
        api_name="gpt-4",
        provider=ModelProvider.OPENAI.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        description="Le plus avancé, excellent pour la créativité et le raisonnement complexe"
    ),
    "GPT-4o": ModelConfig(
        name="GPT-4o",
        api_name="gpt-4o",
        provider=ModelProvider.OPENAI.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        description="Version optimisée, plus rapide et économique que GPT-4"
    ),
    "Claude 3.5 Sonnet": ModelConfig(
        name="Claude 3.5 Sonnet",
        api_name="claude-3-5-sonnet-20240620",
        provider=ModelProvider.ANTHROPIC.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        description="Excellent pour le roleplay, la narration et l'analyse de texte"
    ),
    "DeepSeek": ModelConfig(
        name="DeepSeek",
        api_name="deepseek-chat",
        provider=ModelProvider.DEEPSEEK.value,
        max_tokens=1000,
        temperature_default=0.8,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0002,
        description="Alternative très économique avec de bonnes performances"
    )
}

def get_model_config(model_name: str) -> ModelConfig:
    """Retourne la configuration d'un modèle."""
    if model_name not in AVAILABLE_MODELS:
        # Fallback vers GPT-4
        return AVAILABLE_MODELS["GPT-4"]
    return AVAILABLE_MODELS[model_name]

def get_available_model_names() -> List[str]:
    """Retourne la liste des noms de modèles disponibles."""
    return list(AVAILABLE_MODELS.keys())

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
    "retry_delay": 1.0  # secondes
}
