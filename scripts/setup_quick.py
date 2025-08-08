#!/usr/bin/env python3
"""
⚡ Configuration rapide - DnD AI GameMaster
Script ultra-simplifié pour démarrer en 30 secondes.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Configuration express en une commande."""
    print("🎲 Configuration Express - DnD AI GameMaster")
    print("=" * 50)
    
    # Vérifications rapides
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ requis")
        return
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Configuration automatique
    print("\n📦 Installation automatique...")
    
    try:
        # Créer venv si nécessaire
        if not Path("venv").exists():
            print("Création de l'environnement virtuel...")
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        
        # Installer les dépendances
        pip_path = "venv\\Scripts\\pip.exe" if os.name == 'nt' else "venv/bin/pip"
        print("Installation des dépendances...")
        requirements_file = "requirements/requirements.txt" if os.path.exists("requirements/requirements.txt") else "requirements.txt"
        subprocess.run([pip_path, "install", "-r", requirements_file], check=True)
        
        # Créer .env si manquant
        if not Path(".env").exists():
            env_content = """# 🔑 Ajoutez vos clés API ici
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
"""
            with open(".env", "w") as f:
                f.write(env_content)
            print("✅ Fichier .env créé")
        
        print("\n🎉 Configuration terminée !")
        print("\n📋 Prochaines étapes :")
        print("1. Modifiez .env avec vos vraies clés API")
        print("2. Activez l'environnement virtuel :")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("3. Lancez l'application :")
        print("   python run_app.py")
        print("   OU")
        print("   python dev.py run")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("Utilisez: python dev.py setup")


if __name__ == "__main__":
    main()
