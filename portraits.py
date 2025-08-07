import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_openai_client():
    """Initialise et retourne un client OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY n'est pas définie dans les variables d'environnement")
    return OpenAI(api_key=api_key)

def generate_portrait(name: str, description: str = None) -> str | None:
    """
    Génère un portrait fantastique d'un personnage.
    
    Args:
        name: Nom du personnage
        description: Description physique optionnelle
        
    Returns:
        URL de l'image générée ou None en cas d'erreur
    """
    if not name or not name.strip():
        logger.warning("Nom du personnage manquant pour la génération du portrait")
        return None
        
    prompt = f"Portrait fantastique d'un personnage nommé {name.strip()}, {description or 'aucune description'}, style artistique numérique, haute qualité."

    try:
        client = get_openai_client()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard"
        )
        image_url = response.data[0].url
        logger.info(f"Portrait généré avec succès pour {name}")
        return image_url
    except Exception as e:
        logger.error(f"Erreur lors de la génération du portrait pour {name}: {e}")
        return None
