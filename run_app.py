import os
import subprocess
import sys
from pathlib import Path

# Vérification des fichiers essentiels (sans .env pour Docker)
required_files = ["src/ui/app.py", "src/data/database.py", "src/auth/auth.py", "src/data/models.py", "src/ai/chatbot.py", "src/ai/portraits.py", "src/analytics/performance.py"]

missing_files = [f for f in required_files if not Path(f).exists()]
if missing_files:
    print("Fichiers manquants :", ", ".join(missing_files))
    sys.exit(1)

# Chargement des variables d'environnement (optionnel en local)
try:
    from dotenv import load_dotenv
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv()
        print("✅ Fichier .env chargé")
    else:
        print("ℹ️  Mode Docker : utilisation des variables d'environnement")
except Exception:
    print("ℹ️  python-dotenv non disponible, variables .env ignorées")

# Vérification de la clé API principale
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("⚠️  Avertissement : OPENAI_API_KEY non configurée")
    print("📝 Configurez vos clés API dans .env (local) ou via docker-compose.yml (Docker)")
    # Ne pas quitter car d'autres modèles peuvent fonctionner

# Lancement de l'application Streamlit
try:
    print("✅ Démarrage de l'application Streamlit...")
    # Utilisation de python au lieu de python3 pour plus de compatibilité
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/ui/app.py"])
except FileNotFoundError:
    print("❌ Streamlit n'est pas installé. Lancez `pip install -r requirements.txt`.")
