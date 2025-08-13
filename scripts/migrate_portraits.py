#!/usr/bin/env python3
"""
Script de migration pour télécharger les images DALL-E existantes 
et les stocker localement au lieu des URLs temporaires.
"""

import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.data.database import get_db_path


def is_dalle_url(url: str) -> bool:
    """Vérifie si l'URL est une URL DALL-E temporaire."""
    return url and "oaidalleapiprodscus.blob.core.windows.net" in url


def download_image(url: str, local_path: Path) -> bool:
    """
    Télécharge une image depuis une URL et la sauvegarde localement.

    Returns:
        True si le téléchargement a réussi, False sinon
    """
    try:
        print(f"  Téléchargement: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Créer le dossier parent s'il n'existe pas
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Sauvegarder l'image
        with open(local_path, "wb") as f:
            f.write(response.content)

        print(f"  ✅ Sauvegardé: {local_path}")
        return True

    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def migrate_character_portraits():
    """Migre les portraits de personnages."""
    print("\n🎭 Migration des portraits de personnages...")

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Récupérer tous les personnages avec des URLs DALL-E
    cursor.execute(
        """
        SELECT id, name, portrait_url 
        FROM characters 
        WHERE portrait_url IS NOT NULL 
        AND portrait_url LIKE '%oaidalleapiprodscus.blob.core.windows.net%'
    """
    )

    characters = cursor.fetchall()
    print(f"📊 {len(characters)} personnages avec URLs DALL-E trouvés")

    migrated = 0
    failed = 0

    for char_id, name, portrait_url in characters:
        print(f"\n🔄 Migration personnage: {name} (ID: {char_id})")

        # Définir le chemin local
        local_filename = f"character_{char_id}.png"
        local_path = Path("static/portraits/characters") / local_filename
        relative_path = f"static/portraits/characters/{local_filename}"

        # Télécharger l'image
        if download_image(portrait_url, local_path):
            # Mettre à jour la base de données
            cursor.execute("UPDATE characters SET portrait_url = ? WHERE id = ?", (relative_path, char_id))
            migrated += 1
            print(f"  ✅ BDD mise à jour: {relative_path}")
        else:
            failed += 1
            print(f"  ❌ Échec migration personnage {name}")

    conn.commit()
    conn.close()

    print(f"\n📊 Résultats personnages: {migrated} migrés, {failed} échecs")
    return migrated, failed


def migrate_gm_portraits():
    """Migre les portraits de Maîtres du Jeu."""
    print("\n🧙‍♂️ Migration des portraits de MJ...")

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Récupérer toutes les campagnes avec des URLs DALL-E
    cursor.execute(
        """
        SELECT id, name, gm_portrait 
        FROM campaigns 
        WHERE gm_portrait IS NOT NULL 
        AND gm_portrait LIKE '%oaidalleapiprodscus.blob.core.windows.net%'
    """
    )

    campaigns = cursor.fetchall()
    print(f"📊 {len(campaigns)} campagnes avec URLs DALL-E trouvées")

    migrated = 0
    failed = 0

    for campaign_id, name, gm_portrait in campaigns:
        print(f"\n🔄 Migration campagne: {name} (ID: {campaign_id})")

        # Définir le chemin local
        local_filename = f"gm_{campaign_id}.png"
        local_path = Path("static/portraits/gm") / local_filename
        relative_path = f"static/portraits/gm/{local_filename}"

        # Télécharger l'image
        if download_image(gm_portrait, local_path):
            # Mettre à jour la base de données
            cursor.execute("UPDATE campaigns SET gm_portrait = ? WHERE id = ?", (relative_path, campaign_id))
            migrated += 1
            print(f"  ✅ BDD mise à jour: {relative_path}")
        else:
            failed += 1
            print(f"  ❌ Échec migration campagne {name}")

    conn.commit()
    conn.close()

    print(f"\n📊 Résultats MJ: {migrated} migrés, {failed} échecs")
    return migrated, failed


def main():
    """Script principal de migration."""
    print("🚀 Script de migration des portraits DALL-E vers stockage local")
    print("=" * 60)

    # Vérifier que la base de données existe
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        print("💡 Lancez d'abord l'application pour créer la base de données")
        return 1

    # Créer les dossiers de destination
    portraits_dir = Path("static/portraits")
    gm_dir = portraits_dir / "gm"
    characters_dir = portraits_dir / "characters"

    for directory in [portraits_dir, gm_dir, characters_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 Dossier créé/vérifié: {directory}")

    # Migrer les portraits
    char_migrated, char_failed = migrate_character_portraits()
    gm_migrated, gm_failed = migrate_gm_portraits()

    # Résumé final
    total_migrated = char_migrated + gm_migrated
    total_failed = char_failed + gm_failed

    print("\n" + "=" * 60)
    print("🎉 MIGRATION TERMINÉE")
    print(f"✅ Total migrés: {total_migrated}")
    print(f"❌ Total échecs: {total_failed}")

    if total_failed == 0:
        print("🎊 Tous les portraits ont été migrés avec succès !")
    else:
        print(f"⚠️ {total_failed} portraits n'ont pas pu être migrés (URLs expirées ?)")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
