import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_portrait(name, description):
    prompt = f"Portrait fantastique d'un personnage nommé {name}, {description or 'aucune description'}, style artistique numérique, haute qualité."

    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        print("Erreur lors de la génération du portrait:", e)
        return None
