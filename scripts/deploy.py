#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚢 Script de déploiement automatisé - DnD AI GameMaster
Automatise le déploiement local, Docker et production.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# S'assurer qu'on travaille depuis la racine du projet
script_dir = Path(__file__).parent
project_root = script_dir.parent
os.chdir(project_root)


class Colors:
    """Couleurs pour les messages console."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Affiche un en-tête coloré."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}🚢 {text}{Colors.ENDC}")


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
            text=True,
            encoding="utf-8",
            errors="ignore",
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


def get_compose_command() -> str:
    """Retourne la commande docker compose disponible (plugin ou binaire legacy)."""
    # Préfère le plugin `docker compose` si disponible
    try:
        result = subprocess.run("docker compose version", shell=True, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            return "docker compose"
    except Exception:
        pass

    # Fallback vers l'ancien binaire docker-compose
    return "docker-compose"


def check_prerequisites():
    """Vérifie les prérequis pour le déploiement."""
    print_header("Vérification des prérequis")

    prerequisites = []

    # Python
    if sys.version_info >= (3, 10):
        print_success(f"Python {sys.version.split()[0]} ✓")
        prerequisites.append(True)
    else:
        print_error("Python 3.10+ requis")
        prerequisites.append(False)

    # Git
    try:
        result = run_command("git --version", check=False)
        if result.returncode == 0:
            print_success("Git ✓")
            prerequisites.append(True)
        else:
            print_warning("Git non trouvé (optionnel)")
            prerequisites.append(True)  # Non critique
    except:
        print_warning("Git non trouvé (optionnel)")
        prerequisites.append(True)

    # Docker (pour déploiement Docker)
    try:
        result = run_command("docker --version", check=False)
        if result.returncode == 0:
            print_success("Docker ✓")
            prerequisites.append(True)
        else:
            print_warning("Docker non trouvé (requis pour déploiement Docker)")
            prerequisites.append(False)
    except:
        print_warning("Docker non trouvé (requis pour déploiement Docker)")
        prerequisites.append(False)

    return all(prerequisites)


def validate_project_structure():
    """Valide la structure du projet."""
    print_header("Validation de la structure du projet")

    required_files = [
        "src/ui/app.py",
        "src/auth/auth.py",
        "src/ai/chatbot.py",
        "src/data/database.py",
        "requirements/requirements.txt",
    ]

    optional_files = ["docker/Dockerfile", "docker/docker-compose.yml", ".env", "docs/README.md"]

    missing_required = []
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path} ✓")
        else:
            print_error(f"{file_path} MANQUANT")
            missing_required.append(file_path)

    print(f"\n{Colors.OKBLUE}📁 Fichiers optionnels:{Colors.ENDC}")
    for file_path in optional_files:
        if Path(file_path).exists():
            print_success(f"{file_path} ✓")
        else:
            print_warning(f"{file_path} non trouvé")

    if missing_required:
        print_error(f"Fichiers manquants: {', '.join(missing_required)}")
        return False

    print_success("Structure du projet validée !")
    return True


def run_tests_before_deploy():
    """Lance les tests avant déploiement."""
    print_header("Tests avant déploiement")

    # Tests unitaires
    print("🧪 Lancement des tests unitaires...")
    result = run_command("python -m pytest tests/ -v --tb=short", check=False)
    if result.returncode != 0:
        print_error("Tests unitaires échoués - déploiement annulé")
        return False

    # Vérifications de qualité
    print("🔍 Vérifications de qualité du code...")
    quality_checks = [
        "python -m flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics",
        "python -m black --check src/ --quiet",
        "python -m isort --check-only src/ --quiet",
    ]

    for cmd in quality_checks:
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print_warning("Vérifications de qualité échouées - continuons quand même")
            break

    print_success("Tests réussis !")
    return True


def resolve_env_file(environment: str) -> str | None:
    """Détermine quel fichier d'environnement utiliser.

    Priorité: .env à la racine si présent. Sinon, aucun --env-file n'est passé
    (docker compose utilisera les variables d'environnement du shell).
    """
    root_env = Path(".env")
    if root_env.exists():
        print_success("Fichier .env détecté – utilisé pour le déploiement")
        return str(root_env)
    print_warning("Aucun fichier .env trouvé – les variables doivent provenir de l'environnement système")
    return None


def deploy_local(use_optimized: bool = False):
    """Déploiement local simple."""
    print_header("Déploiement local")

    if not validate_project_structure():
        return False

    # Installer/mettre à jour les dépendances
    print("📦 Installation des dépendances...")
    run_command("pip install -r requirements/requirements.txt")

    # Lancer l'application
    app_file = "src/ui/app.py"  # Version modulaire (ex-refactored)

    if not Path(app_file).exists():
        print_error(f"Fichier d'application non trouvé: {app_file}")
        return False

    print_success("Déploiement local prêt !")
    print(f"{Colors.OKBLUE}🚀 Pour démarrer: streamlit run {app_file}{Colors.ENDC}")
    return True


def deploy_docker(environment: str = "production", build_only: bool = False):
    """Déploiement avec Docker."""
    print_header(f"Déploiement Docker ({environment})")

    if not validate_project_structure():
        return False

    # Vérifier Docker
    try:
        run_command("docker --version")
    except:
        print_error("Docker n'est pas disponible")
        return False

    # Vérifier la structure Docker existante
    if not Path("docker/Dockerfile").exists():
        print_error("Dockerfile manquant dans docker/")
        return False

    if not Path("docker/docker-compose.yml").exists():
        print_error("docker-compose.yml manquant dans docker/")
        return False

    # Résoudre le fichier d'environnement
    env_file = resolve_env_file(environment)

    # Toujours arrêter proprement les éventuels conteneurs existants avant rebuild
    compose_file = "docker/docker-compose.yml"
    project_name = f"comparemodelpoc_{environment}"
    compose_cmd_base = get_compose_command()
    print("🧹 Arrêt des conteneurs existants (compose down)...")
    down_cmd = f"{compose_cmd_base} -p {project_name} -f {compose_file} down --remove-orphans"
    if env_file:
        down_cmd = f"{compose_cmd_base} -p {project_name} -f {compose_file} --env-file {env_file} down --remove-orphans"
    run_command(down_cmd, check=False)

    # Construction via docker compose pour utiliser le docker-compose.yml existant
    compose_cmd_base = get_compose_command()
    print("🐳 Construction des services (compose build)...")
    build_cmd = f"{compose_cmd_base} -p {project_name} -f {compose_file} build"
    if env_file:
        build_cmd = f"{compose_cmd_base} -p {project_name} -f {compose_file} --env-file {env_file} build"
    run_command(build_cmd)

    if build_only:
        print_success("Build compose terminé avec succès !")
        return True

    # Lancement avec Docker Compose
    print("🚀 Lancement de l'application avec Docker Compose...")
    # Up avec rebuild et suppression des orphelins pour éviter les conflits au redeploy
    up_cmd = f"{compose_cmd_base} -p {project_name} -f {compose_file} up -d --build --remove-orphans"
    if env_file:
        up_cmd = f"{compose_cmd_base} -p {project_name} -f {compose_file} --env-file {env_file} up -d --build --remove-orphans"
    run_command(up_cmd)

    print_success("Application déployée avec Docker !")
    print(f"{Colors.OKBLUE}🌐 Accessible sur: http://localhost:8501{Colors.ENDC}")
    print(f"{Colors.OKCYAN}📋 Logs: {compose_cmd_base} -f docker/docker-compose.yml logs -f{Colors.ENDC}")
    print(
        f"{Colors.OKCYAN}🛑 Arrêt: {compose_cmd_base} -p {project_name} -f docker/docker-compose.yml down --remove-orphans{Colors.ENDC}"
    )

    return True


def create_dockerfile():
    """Crée un Dockerfile optimisé."""
    dockerfile_content = """# 🐳 Dockerfile multi-stage optimisé - DnD AI GameMaster

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python depuis le dossier requirements/
COPY requirements/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Créer un utilisateur non-root
RUN useradd --create-home --shell /bin/bash dnduser

WORKDIR /app

# Copier les dépendances depuis le builder
COPY --from=builder /root/.local /home/dnduser/.local

# Copier le code source depuis le dossier src/
COPY src/ ./src/

# Copier le fichier .env à la racine (s'il existe)
COPY .env* ./

# Définir les permissions
RUN chown -R dnduser:dnduser /app
USER dnduser

# Variables d'environnement
ENV PATH=/home/dnduser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Port exposé
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande par défaut - utiliser le bon chemin vers l'app Streamlit
CMD ["streamlit", "run", "src/ui/app.py"]
"""

    # Créer le Dockerfile dans le dossier docker/
    dockerfile_path = Path("docker/Dockerfile")
    dockerfile_path.parent.mkdir(exist_ok=True)

    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    print_success(f"Dockerfile créé dans {dockerfile_path}")


def create_docker_compose():
    """Crée un fichier docker-compose.yml."""
    compose_content = """version: '3.8'

services:
  dnd-gamemaster:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./database.db:/app/database.db
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Service optionnel : reverse proxy nginx
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - dnd-gamemaster
    restart: unless-stopped
    profiles:
      - with-nginx

volumes:
  app-data:
"""

    # Créer le docker-compose.yml dans le dossier docker/
    compose_path = Path("docker/docker-compose.yml")
    compose_path.parent.mkdir(exist_ok=True)

    with open(compose_path, "w") as f:
        f.write(compose_content)

    print_success(f"docker-compose.yml créé dans {compose_path}")


def create_production_package():
    """Crée un package de production."""
    print_header("Création du package de production")

    # Créer un dossier temporaire
    package_name = f"dnd-gamemaster-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    package_path = Path(f"dist/{package_name}")
    package_path.mkdir(parents=True, exist_ok=True)

    # Fichiers à inclure selon la structure réelle du projet
    files_to_include = [
        "src/",
        "requirements/",
        "run_app.py",
        "README.md",
        "docs/",
        "docker/",
        ".env*",
    ]

    print("📦 Copie des fichiers...")
    for item in files_to_include:
        # Gestion spéciale pour les fichiers .env avec wildcard
        if item == ".env*":
            import glob

            env_files = glob.glob(".env*")
            if env_files:
                for env_file in env_files:
                    if Path(env_file).is_file():
                        shutil.copy2(env_file, package_path / env_file)
                        print_success(f"Copié: {env_file}")
            else:
                print_warning(f"Non trouvé: {item}")
        else:
            src_path = Path(item)
            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, package_path / item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, package_path / item)
                print_success(f"Copié: {item}")
            else:
                print_warning(f"Non trouvé: {item}")

    # Créer les scripts de déploiement
    create_deployment_scripts(package_path)

    # Créer l'archive
    archive_path = shutil.make_archive(f"dist/{package_name}", "zip", package_path)

    print_success(f"Package créé: {archive_path}")
    print(f"{Colors.OKBLUE}📦 Taille: {Path(archive_path).stat().st_size / 1024 / 1024:.1f} MB{Colors.ENDC}")

    return archive_path


def create_deployment_scripts(package_path: Path):
    """Crée les scripts de déploiement pour le package."""

    # Script de déploiement rapide
    quick_deploy = """#!/bin/bash
# 🚀 Script de déploiement rapide

echo "🎲 Déploiement DnD AI GameMaster..."

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

# Construire et lancer depuis le dossier docker/
cd docker
docker-compose up --build -d

echo "✅ Application déployée !"
echo "🌐 Accessible sur: http://localhost:8501"
echo "📋 Logs: docker-compose logs -f"
echo "🛑 Arrêt: docker-compose down"
"""

    with open(package_path / "deploy.sh", "w", encoding="utf-8") as f:
        f.write(quick_deploy)

    # Script Windows
    quick_deploy_bat = """@echo off
REM 🚀 Script de déploiement rapide Windows

echo 🎲 Déploiement DnD AI GameMaster...

REM Vérifier Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas installé
    pause
    exit /b 1
)

REM Construire et lancer depuis le dossier docker/
cd docker
docker-compose up --build -d

echo ✅ Application déployée !
echo 🌐 Accessible sur: http://localhost:8501
echo 📋 Logs: docker-compose logs -f
echo 🛑 Arrêt: docker-compose down
pause
"""

    with open(package_path / "deploy.bat", "w", encoding="utf-8") as f:
        f.write(quick_deploy_bat)

    print_success("Scripts de déploiement créés")


def stop_deployment(environment: str = "development"):
    """Arrête les déploiements en cours."""
    print_header("Arrêt des déploiements")

    # Arrêter Docker Compose (utilise le même fichier et projet que le déploiement)
    compose_file = "docker/docker-compose.yml"
    project_name = f"comparemodelpoc_{environment}"
    if Path(compose_file).exists():
        print("🐳 Arrêt de Docker Compose...")
        compose_cmd_base = get_compose_command()
        run_command(f"{compose_cmd_base} -p {project_name} -f {compose_file} down --remove-orphans", check=False)

    # Arrêter les processus Streamlit
    try:
        if os.name == "nt":  # Windows
            run_command("taskkill /f /im streamlit.exe", check=False)
        else:  # Linux/Mac
            run_command("pkill -f streamlit", check=False)
        print_success("Processus Streamlit arrêtés")
    except:
        print_warning("Aucun processus Streamlit trouvé")


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="🚢 Script de déploiement automatisé - DnD AI GameMaster",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python deploy.py check              # Vérifier les prérequis
  python deploy.py local              # Déploiement local simple
  python deploy.py local --optimized  # Utilise la version optimisée
  python deploy.py docker             # Déploiement Docker
  python deploy.py docker --staging   # Déploiement staging
  python deploy.py package            # Créer un package de production
  python deploy.py stop               # Arrêter tous les déploiements
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Commande check
    subparsers.add_parser("check", help="Vérifie les prérequis de déploiement")

    # Commande local
    local_parser = subparsers.add_parser("local", help="Déploiement local")
    local_parser.add_argument("--optimized", action="store_true", help="Utilise la version optimisée")
    local_parser.add_argument("--skip-tests", action="store_true", help="Ignore les tests")

    # Commande docker
    docker_parser = subparsers.add_parser("docker", help="Déploiement Docker")
    docker_parser.add_argument("--staging", action="store_true", help="Environnement staging")
    docker_parser.add_argument("--production", action="store_true", help="Environnement production")
    docker_parser.add_argument("--build-only", action="store_true", help="Construit seulement l'image")

    # Autres commandes
    subparsers.add_parser("package", help="Crée un package de production")
    subparsers.add_parser("stop", help="Arrête tous les déploiements")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print(f"{Colors.HEADER}🚢 DnD AI GameMaster - Script de déploiement{Colors.ENDC}")

    try:
        if args.command == "check":
            check_prerequisites()
            validate_project_structure()

        elif args.command == "local":
            if not args.skip_tests and not run_tests_before_deploy():
                return
            deploy_local(args.optimized)

        elif args.command == "docker":
            if args.staging:
                environment = "staging"
            elif args.production:
                environment = "production"
            else:
                environment = "development"

            deploy_docker(environment, args.build_only)

        elif args.command == "package":
            create_production_package()

        elif args.command == "stop":
            stop_deployment()

    except KeyboardInterrupt:
        print_warning("\nDéploiement interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print_error(f"Erreur de déploiement: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
