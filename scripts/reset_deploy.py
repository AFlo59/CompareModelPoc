#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 Full reset & redeploy helper

Effectue un reset complet de l'environnement Docker du projet puis relance un déploiement propre:
- down -v --remove-orphans
- suppression explicite des volumes nommés (app_data, app_logs)
- prune (builder + images) optionnel
- build --no-cache
- up --force-recreate --renew-anon-volumes
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    print(f"▶️  {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return e


def get_compose_command() -> str:
    try:
        res = subprocess.run("docker compose version", shell=True, check=False, capture_output=True, text=True)
        if res.returncode == 0:
            return "docker compose"
    except Exception:
        pass
    return "docker-compose"


def main():
    # Toujours exécuter depuis la racine du projet
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    parser = argparse.ArgumentParser(
        description="Reset complet des conteneurs/volumes et redeploy propre",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    env_group = parser.add_mutually_exclusive_group()
    env_group.add_argument("--staging", action="store_true", help="Utiliser l'environnement staging")
    env_group.add_argument("--production", action="store_true", help="Utiliser l'environnement production")
    parser.add_argument("--no-prune", action="store_true", help="Ne pas exécuter les prunes Docker")
    args = parser.parse_args()

    environment = "development"
    if args.staging:
        environment = "staging"
    elif args.production:
        environment = "production"

    compose = get_compose_command()
    # Utiliser le bon chemin vers docker-compose.yml dans le dossier docker/
    compose_file = "docker/docker-compose.yml"
    project_name = f"comparemodelpoc_{environment}"

    # Vérifier que le fichier docker-compose.yml existe
    if not Path(compose_file).exists():
        print(f"❌ Fichier {compose_file} introuvable!")
        print("💡 Assurez-vous que le fichier docker-compose.yml est dans le dossier docker/")
        sys.exit(1)

    # down -v
    print("\n🧹 Stopping containers and removing volumes (down -v)...")
    run(f"{compose} -p {project_name} -f {compose_file} down -v --remove-orphans", check=False)

    # suppression explicite des volumes nommés
    print("\n🧽 Removing named volumes if present...")
    run(f"docker volume rm {project_name}_app_data", check=False)
    run(f"docker volume rm {project_name}_app_logs", check=False)

    # prune optionnel
    if not args.no_prune:
        print("\n🧺 Pruning builder cache and dangling images...")
        run("docker builder prune -af", check=False)
        run("docker image prune -af", check=False)

    # build --no-cache
    print("\n🐳 Building images (no-cache)...")
    env_file_arg = ""
    if Path(".env").exists():
        env_file_arg = "--env-file .env"
        print("✅ Using .env for compose")
    else:
        print("⚠️  Fichier .env non trouvé à la racine du projet")

    run(f"{compose} -p {project_name} -f {compose_file} {env_file_arg} build --no-cache")

    # up forcé
    print("\n🚀 Starting services (force recreate, renew anon volumes)...")
    run(
        f"{compose} -p {project_name} -f {compose_file} {env_file_arg} up -d --force-recreate --renew-anon-volumes --remove-orphans"
    )

    print("\n✅ Reset & redeploy completed!")
    print("🌐 App: http://localhost:8501")
    print(f"📋 Logs: {compose} -f {compose_file} logs -f")
    print(f"🛑 Stop: {compose} -p {project_name} -f {compose_file} down --remove-orphans")


if __name__ == "__main__":
    main()
