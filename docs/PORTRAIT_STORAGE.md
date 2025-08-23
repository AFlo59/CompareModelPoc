# 🎨 Système de Stockage Local des Portraits

## 📋 Vue d'ensemble

Le système de portraits a été mis à jour pour **télécharger et stocker localement** les images générées par DALL-E au lieu de s'appuyer sur les URLs temporaires qui expirent après ~1 heure.

## 🏗️ Architecture

### Structure des dossiers
```
static/
└── portraits/
    ├── gm/              # Portraits des Maîtres du Jeu
    │   ├── gm_1.png     # campagne_id = 1
    │   ├── gm_2.png     # campagne_id = 2
    │   └── ...
    └── characters/      # Portraits des personnages
        ├── character_1.png  # character_id = 1
        ├── character_2.png  # character_id = 2
        └── ...
```

### Nomenclature
- **Portraits GM** : `gm_{campaign_id}.png`
- **Portraits personnages** : `character_{character_id}.png`
- **Stockage BDD** : Chemin relatif `static/portraits/gm/gm_123.png`

## 🔄 Fonctionnement

### 1. Génération de portrait
1. **DALL-E génère** une image → URL temporaire
2. **Téléchargement immédiat** de l'image vers `/static/portraits/`
3. **Sauvegarde locale** avec nom basé sur l'ID
4. **BDD mise à jour** avec le chemin local au lieu de l'URL temporaire

### 2. Affichage dans l'interface
- Les vues utilisent `display_portrait()` pour gérer URLs externes et fichiers locaux
- Fallback automatique si une image locale est manquante
- Support des URLs Dicebear (permanentes)

## 🐳 Docker

### Volumes persistants
Le `docker-compose.yml` inclut maintenant un volume pour les portraits :
```yaml
volumes:
  - app_static:/app/static
```

### Backup VPS
Le script `update_vps.sh` sauvegarde et restaure :
- Base de données : `database_backup_TIMESTAMP.db`
- Portraits : `portraits_backup_TIMESTAMP/`

## 🧪 Tests

Nouveaux tests dans `test_portrait_local_storage.py` :
- Téléchargement et sauvegarde d'images
- Gestion des erreurs de téléchargement
- Logique de stockage pour GM et personnages
- Utilitaires d'affichage d'images

## 🔧 Migration

### Script de migration automatique
```bash
python scripts/migrate_portraits.py
```

Ce script :
1. **Identifie** les URLs DALL-E temporaires dans la BDD
2. **Télécharge** les images encore accessibles
3. **Met à jour** la BDD avec les chemins locaux
4. **Rapport** de migration avec statistiques

### Migration manuelle
Si certaines images ont déjà expiré, elles seront perdues. Les nouvelles générations utiliseront automatiquement le stockage local.

## 🚨 Bonnes pratiques

### Sauvegarde
- **Inclure** le dossier `static/portraits/` dans vos backups
- **Vérifier** l'espace disque disponible
- **Nettoyer** périodiquement les portraits orphelins

### Dépannage
- **Images manquantes** : Vérifier les permissions du dossier `static/`
- **Erreurs de téléchargement** : Vérifier la connectivité réseau
- **Espace disque** : Surveiller la taille du dossier portraits

## 📊 Avantages

✅ **Persistance** : Les images survivent aux redémarrages VPS  
✅ **Performance** : Pas de requêtes externes pour afficher les images  
✅ **Fiabilité** : Plus de dépendance aux URLs temporaires  
✅ **Backup** : Images incluses dans les sauvegardes système  

## 🔮 Améliorations futures

- [ ] Compression automatique des images (WebP)
- [ ] Nettoyage automatique des portraits orphelins
- [ ] Cache intelligent pour éviter les re-téléchargements
- [ ] Support de formats d'image multiples (JPEG, PNG, WebP)
