#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛠️ Script de développement automatisé - DnD AI GameMaster
Simplifie toutes les tâches de développement local.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import shutil
import webbrowser
import time


class Colors:
    """Couleurs pour les messages console."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Affiche un en-tête coloré."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}🚀 {text}{Colors.ENDC}")


def print_success(text: str):
    """Affiche un message de succès."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Affiche un avertissement."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str):
    """Affiche une erreur."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def run_command(cmd: str, cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Exécute une commande shell."""
    print(f"{Colors.OKCYAN}▶️  {cmd}{Colors.ENDC}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Commande échouée: {e}")
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Vérifie la version Python."""
    if sys.version_info < (3, 10):
        print_error("Python 3.10+ requis")
        sys.exit(1)
    print_success(f"Python {sys.version.split()[0]} ✓")


def check_venv():
    """Vérifie si l'environnement virtuel est actif."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Environnement virtuel actif ✓")
        return True
    else:
        print_warning("Environnement virtuel non détecté")
        return False


def setup_environment():
    """Configure l'environnement de développement."""
    print_header("Configuration de l'environnement")
    
    check_python_version()
    
    # Créer venv si nécessaire
    if not Path("venv").exists():
        print("Création de l'environnement virtuel...")
        run_command("python -m venv venv")
        print_success("Environnement virtuel créé")
    
    # Vérifier activation
    if not check_venv():
        if os.name == 'nt':  # Windows
            print("Pour activer l'environnement virtuel:")
            print(f"{Colors.OKCYAN}venv\\Scripts\\activate{Colors.ENDC}")
        else:  # Linux/Mac
            print("Pour activer l'environnement virtuel:")
            print(f"{Colors.OKCYAN}source venv/bin/activate{Colors.ENDC}")
        return False
    
    # Installer les dépendances
    print("Installation des dépendances...")
    run_command("pip install -r requirements.txt")
    
    # Installer les outils de développement
    if Path("dev-requirements.txt").exists():
        run_command("pip install -r dev-requirements.txt")
    else:
        print("Installation des outils de développement...")
        dev_tools = [
            "black>=23.0.0",
            "isort>=5.12.0", 
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pytest-cov>=4.0.0",
            "pre-commit>=3.0.0"
        ]
        run_command(f"pip install {' '.join(dev_tools)}")
    
    print_success("Environnement configuré avec succès !")
    return True


def run_tests(coverage: bool = True, verbose: bool = True):
    """Lance la suite de tests."""
    print_header("Exécution des tests")
    
    cmd = "python -m pytest tests/"
    if verbose:
        cmd += " -v"
    if coverage:
        cmd += " --cov=src --cov-report=html --cov-report=term-missing"
    
    result = run_command(cmd, check=False)
    
    if result.returncode == 0:
        print_success("Tous les tests passent !")
        if coverage and Path("htmlcov/index.html").exists():
            print(f"{Colors.OKBLUE}📊 Rapport de couverture: htmlcov/index.html{Colors.ENDC}")
    else:
        print_error(f"Tests échoués (code: {result.returncode})")


def run_quality_checks():
    """Lance les vérifications de qualité de code."""
    print_header("Vérifications de qualité")
    
    checks = [
        ("Black (formatage)", "black --check --diff src/ tests/"),
        ("isort (imports)", "isort --check-only --diff src/ tests/"),
        ("flake8 (linting)", "flake8 src/ tests/"),
        ("mypy (types)", "mypy src/ --ignore-missing-imports")
    ]
    
    results = []
    for name, cmd in checks:
        print(f"\n{Colors.OKBLUE}🔍 {name}...{Colors.ENDC}")
        result = run_command(cmd, check=False)
        results.append((name, result.returncode == 0))
    
    print(f"\n{Colors.BOLD}📋 Résumé des vérifications:{Colors.ENDC}")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    if all(success for _, success in results):
        print_success("Toutes les vérifications passent !")
    else:
        print_warning("Certaines vérifications ont échoué")


def fix_code_style():
    """Corrige automatiquement le style de code."""
    print_header("Correction automatique du style")
    
    print("Formatage avec Black...")
    run_command("black src/ tests/")
    
    print("Organisation des imports avec isort...")
    run_command("isort src/ tests/")
    
    print_success("Style de code corrigé !")


def run_app(mode: str = "legacy"):
    """Lance l'application."""
    print_header(f"Lancement de l'application ({mode})")
    
    # Vérifier les fichiers requis
    if Path(".env").exists():
        print_success("Fichier .env détecté – utilisation en local")
    else:
        print_warning("Fichier .env manquant – l'application peut fonctionner avec des fonctionnalités limitées")
    
    if mode == "refactored" or mode == "legacy":
        app_file = "src/ui/app_legacy.py" if mode == "legacy" else "src/ui/app.py"
    else:
        app_file = "src/ui/app.py"  # Version modulaire par défaut
    
    if not Path(app_file).exists():
        print_error(f"Fichier d'application manquant: {app_file}")
        return
    
    print(f"Démarrage de l'application: {app_file}")
    print(f"{Colors.OKCYAN}🌐 L'application va s'ouvrir dans votre navigateur...{Colors.ENDC}")
    
    # Ouvrir le navigateur après un délai
    def open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:8501")
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Lancer Streamlit
    run_command(f"streamlit run {app_file}")


def create_env_template():
    """Crée un template de fichier .env."""
    env_content = """# 🔑 Configuration des clés API
# Obtenez vos clés sur les sites des fournisseurs

# OpenAI (requis pour GPT-4, GPT-4o, DALL-E 3)
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic (requis pour Claude 3.5 Sonnet)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# DeepSeek (optionnel - modèle économique)
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# 🔧 Configuration optionnelle
# DATABASE_URL=sqlite:///database.db
# LOG_LEVEL=INFO
"""
    
    with open(".env.template", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print_success("Template .env.template créé")
    print(f"{Colors.OKBLUE}📝 Copiez .env.template vers .env et renseignez vos clés API{Colors.ENDC}")


def clean_project():
    """Nettoie les fichiers temporaires."""
    print_header("Nettoyage du projet")
    
    patterns_to_clean = [
        "__pycache__",
        "*.pyc", 
        "*.pyo",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".mypy_cache",
        "*.egg-info",
        "dist",
        "build"
    ]
    
    for pattern in patterns_to_clean:
        if "*" in pattern:
            # Utiliser find pour les patterns
            if os.name == 'nt':  # Windows
                run_command(f'for /r . %i in ({pattern}) do @if exist "%i" rmdir /s /q "%i" 2>nul || del /q "%i" 2>nul', check=False)
            else:  # Linux/Mac
                run_command(f"find . -name '{pattern}' -type f -delete", check=False)
        else:
            # Supprimer les dossiers/fichiers directs
            for path in Path(".").rglob(pattern):
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        path.unlink(missing_ok=True)
    
    print_success("Projet nettoyé !")


def show_status():
    """Affiche le statut du projet."""
    print_header("Statut du projet DnD AI GameMaster")
    
    # Informations générales
    print(f"{Colors.BOLD}📊 Informations générales:{Colors.ENDC}")
    print(f"  • Répertoire: {Path.cwd()}")
    print(f"  • Python: {sys.version.split()[0]}")
    print(f"  • Environnement virtuel: {'✅' if check_venv() else '❌'}")
    
    # Structure du projet
    print(f"\n{Colors.BOLD}📁 Structure du projet:{Colors.ENDC}")
    key_paths = [
        ("src/", "Code source principal"),
        ("tests/", "Suite de tests"),
        ("docs/", "Documentation"),
        (".env", "Configuration API"),
        ("requirements.txt", "Dépendances")
    ]
    
    for path, description in key_paths:
        exists = "✅" if Path(path).exists() else "❌"
        print(f"  {exists} {path:<20} {description}")
    
    # Tests récents
    if Path(".pytest_cache").exists():
        print(f"\n{Colors.BOLD}🧪 Tests:{Colors.ENDC}")
        result = run_command("pytest --collect-only -q", check=False)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines:
                last_line = lines[-1]
                print(f"  📋 {last_line}")
    
    # Couverture de code
    if Path("htmlcov/index.html").exists():
        print(f"  📊 Rapport de couverture disponible: htmlcov/index.html")


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="🛠️ Script de développement automatisé - DnD AI GameMaster",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python dev.py setup              # Configure l'environnement
  python dev.py run               # Lance l'app (version legacy)
  python dev.py run --refactored  # Lance l'app refactorisée
  python dev.py test              # Lance les tests
  python dev.py test --no-coverage # Tests sans couverture
  python dev.py check             # Vérifications qualité
  python dev.py fix               # Corrige le style automatiquement
  python dev.py clean             # Nettoie les fichiers temporaires
  python dev.py status            # Affiche le statut du projet
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")
    
    # Commande setup
    subparsers.add_parser("setup", help="Configure l'environnement de développement")
    
    # Commande run
    run_parser = subparsers.add_parser("run", help="Lance l'application")
    run_parser.add_argument("--refactored", action="store_true", help="Utilise la version refactorisée")
    
    # Commande test
    test_parser = subparsers.add_parser("test", help="Lance les tests")
    test_parser.add_argument("--no-coverage", action="store_true", help="Désactive la couverture de code")
    test_parser.add_argument("--quiet", action="store_true", help="Mode silencieux")
    
    # Autres commandes
    subparsers.add_parser("check", help="Vérifications de qualité de code")
    subparsers.add_parser("fix", help="Corrige automatiquement le style de code")
    subparsers.add_parser("clean", help="Nettoie les fichiers temporaires")
    subparsers.add_parser("status", help="Affiche le statut du projet")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print(f"{Colors.HEADER}🎲 DnD AI GameMaster - Script de développement{Colors.ENDC}")
    
    try:
        if args.command == "setup":
            setup_environment()
        elif args.command == "run":
            mode = "refactored" if args.refactored else "legacy"
            run_app(mode)
        elif args.command == "test":
            coverage = not args.no_coverage
            verbose = not args.quiet
            run_tests(coverage, verbose)
        elif args.command == "check":
            run_quality_checks()
        elif args.command == "fix":
            fix_code_style()
        elif args.command == "clean":
            clean_project()
        elif args.command == "status":
            show_status()
    
    except KeyboardInterrupt:
        print_warning("\nInterrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
