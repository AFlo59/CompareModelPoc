#!/usr/bin/env python3
"""
Script d'installation et de vérification pour CompareModelPoc.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# S'assurer qu'on travaille depuis la racine du projet
script_dir = Path(__file__).parent
project_root = script_dir.parent
os.chdir(project_root)


def check_python_version() -> bool:
    """Vérifie que Python 3.8+ est installé."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} détecté")
        return True
    else:
        print(f"❌ Python 3.8+ requis, {version.major}.{version.minor}.{version.micro} détecté")
        return False


def check_required_files() -> Tuple[bool, List[str]]:
    """Vérifie la présence des fichiers requis."""
    required_files = [
        "run_app.py",
        "src/ui/app.py",
        "src/data/database.py",
        "src/auth/auth.py",
        "src/data/models.py",
        "src/ai/chatbot.py",
        "src/ai/portraits.py",
        "src/analytics/performance.py",
        "requirements/requirements.txt",
        "src/core/config.py",
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if not missing_files:
        print("✅ Tous les fichiers requis sont présents")
        return True, []
    else:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        return False, missing_files


def check_env_file() -> bool:
    """Vérifie la présence et signale l'utilisation du .env sans le modifier."""
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env détecté – il sera utilisé par l'application et docker compose")
        return True
    else:
        print("ℹ️ Aucun .env présent – vous pouvez en ajouter un pour vos clés API")
        return True


def install_dependencies() -> bool:
    """Installe les dépendances Python."""
    try:
        print("📦 Installation des dépendances...")
        req = "requirements/requirements.txt" if Path("requirements/requirements.txt").exists() else "requirements.txt"
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req], check=True, capture_output=True)
        print("✅ Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur installation dépendances: {e}")
        return False


def check_database() -> bool:
    """Vérifie et initialise la base de données."""
    try:
        # Ajouter le répertoire racine au PYTHONPATH
        import sys

        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from src.data.database import get_connection, init_db

        print("🗃️  Initialisation de la base de données...")
        init_db()

        # Test de connexion
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_tables = {"users", "model_choices", "campaigns", "characters", "messages", "performance_logs"}
        if expected_tables.issubset(set(tables)):
            print("✅ Base de données initialisée correctement")
            return True
        else:
            print("❌ Tables manquantes dans la base de données")
            return False

    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False


def run_tests() -> bool:
    """Exécute les tests unitaires."""
    try:
        print("🧪 Exécution des tests...")
        # Définir les variables d'environnement pour les tests
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], capture_output=True, text=True, env=env
        )

        if result.returncode == 0:
            print("✅ Tous les tests passent")
            return True
        else:
            print("❌ Certains tests échouent:")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("⚠️  pytest non trouvé, tests ignorés")
        return True
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False


def display_usage_info():
    """Affiche les informations d'utilisation."""
    print("\n" + "=" * 60)
    print("📋 INFORMATIONS D'UTILISATION")
    print("=" * 60)
    print("Pour démarrer l'application :")
    print("  python run_app.py")
    print("  ou")
    print("  streamlit run app.py")
    print("\nAccès à l'application :")
    print("  http://localhost:8501")
    print("\nPour exécuter les tests :")
    print("  pytest tests/")
    print("\nFichiers de configuration :")
    print("  .env - Clés API (OBLIGATOIRE)")
    print("  config.py - Configuration application")
    print("=" * 60)


def main():
    """Fonction principale du script d'installation."""
    print("🚀 INSTALLATION ET VÉRIFICATION - CompareModelPoc")
    print("=" * 60)

    all_checks_passed = True

    # Vérifications préalables
    checks = [
        ("Version Python", check_python_version),
        ("Fichiers requis", lambda: check_required_files()[0]),
        ("Fichier .env", check_env_file),
    ]

    for check_name, check_func in checks:
        print(f"\n🔍 Vérification: {check_name}")
        if not check_func():
            all_checks_passed = False

    # Installation des dépendances
    print(f"\n📦 Installation des dépendances")
    if not install_dependencies():
        all_checks_passed = False

    # Vérification de la base de données
    print(f"\n🗃️  Vérification base de données")
    if not check_database():
        all_checks_passed = False

    # Tests (optionnels)
    print(f"\n🧪 Tests unitaires")
    run_tests()  # Ne bloque pas même si les tests échouent

    # Résumé final
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ INSTALLATION RÉUSSIE!")
        print("L'application est prête à être utilisée.")
        display_usage_info()
    else:
        print("❌ INSTALLATION INCOMPLÈTE")
        print("Veuillez corriger les erreurs ci-dessus avant de continuer.")
        print("\nActions suggérées:")
        print("1. Vérifiez que tous les fichiers sont présents")
        print("2. Configurez vos clés API dans le fichier .env")
        print("3. Installez les dépendances manquantes")

    print("=" * 60)


if __name__ == "__main__":
    main()
