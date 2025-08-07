import os
import subprocess
import sys
from pathlib import Path

# Vérification des fichiers essentiels
required_files = [
    "app.py", "database.py", "auth.py", "models.py", "chatbot.py", "portraits.py", "performance.py", ".env"
]

missing_files = [f for f in required_files if not Path(f).exists()]
if missing_files:
    print("Fichiers manquants :", ", ".join(missing_files))
    sys.exit(1)

# Vérification des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("Erreur : la variable OPENAI_API_KEY est absente dans le fichier .env")
    sys.exit(1)

# Lancement de l'application Streamlit
try:
    print("✅ Démarrage de l'application Streamlit...")
    # Utilisation de python au lieu de python3 pour plus de compatibilité
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
except FileNotFoundError:
    print("❌ Streamlit n'est pas installé. Lancez `pip install -r requirements.txt`.")