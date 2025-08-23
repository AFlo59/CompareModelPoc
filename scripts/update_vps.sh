#!/bin/bash
# Script de mise à jour sécurisée sur VPS OVH
# Préserve la base de données et les volumes Docker

set -e  # Arrêter en cas d'erreur

VPS_IP="51.210.243.134"
VPS_USER="debian"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Début de la mise à jour VPS - $TIMESTAMP"
echo "📍 Serveur: $VPS_IP"
echo "👤 Utilisateur: $VPS_USER"

# 1. Créer le nouveau package localement
echo ""
echo "📦 Création du package de déploiement..."
python scripts/deploy.py package

# Trouver le dernier package créé
PACKAGE_FILE=$(ls -t dist/dnd-gamemaster-*.zip 2>/dev/null | head -n1)
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Erreur: Aucun package trouvé dans dist/"
    echo "💡 Assurez-vous que 'python scripts/deploy.py package' fonctionne"
    exit 1
fi

echo "✅ Package créé: $PACKAGE_FILE"
PACKAGE_NAME=$(basename "$PACKAGE_FILE")

# 2. Copier le package sur le serveur
echo ""
echo "📤 Copie du package sur le serveur..."
if ! scp "$PACKAGE_FILE" ${VPS_USER}@${VPS_IP}:~/; then
    echo "❌ Erreur lors de la copie du package"
    echo "💡 Vérifiez votre connexion SSH"
    exit 1
fi

echo "✅ Package copié: $PACKAGE_NAME"

# 3. Mise à jour sur le serveur avec sauvegarde
echo ""
echo "🔄 Mise à jour sur le serveur avec préservation des données..."

ssh ${VPS_USER}@${VPS_IP} << REMOTE_SCRIPT

set -e

echo ""
echo "🛡️ === SAUVEGARDE DE LA BASE DE DONNÉES ET PORTRAITS ==="

# Créer le dossier de sauvegarde s'il n'existe pas
mkdir -p ~/backups

# Sauvegarder la base de données depuis le conteneur (si le conteneur existe)
if docker ps -a | grep -q docker_app_1; then
    echo "📋 Sauvegarde depuis le conteneur Docker..."
    if docker cp docker_app_1:/app/database.db ~/backups/database_backup_${TIMESTAMP}.db 2>/dev/null; then
        echo "✅ Base de données sauvegardée: ~/backups/database_backup_${TIMESTAMP}.db"
    else
        echo "⚠️ Impossible de sauvegarder depuis le conteneur, tentative depuis le filesystem..."
        if [ -f ~/database.db ]; then
            cp ~/database.db ~/backups/database_backup_${TIMESTAMP}.db
            echo "✅ Base de données sauvegardée depuis le filesystem"
        else
            echo "⚠️ Aucune base de données trouvée - première installation ?"
        fi
    fi
    
    # Sauvegarder les portraits depuis le conteneur
    echo "🎨 Sauvegarde des portraits..."
    if docker exec docker_app_1 test -d /app/static/portraits 2>/dev/null; then
        docker cp docker_app_1:/app/static/portraits ~/backups/portraits_backup_${TIMESTAMP} 2>/dev/null && \
        echo "✅ Portraits sauvegardés: ~/backups/portraits_backup_${TIMESTAMP}" || \
        echo "⚠️ Erreur lors de la sauvegarde des portraits"
    else
        echo "ℹ️ Aucun dossier portraits trouvé dans le conteneur"
    fi
else
    echo "⚠️ Conteneur docker_app_1 non trouvé - tentative depuis le filesystem..."
    if [ -f ~/database.db ]; then
        cp ~/database.db ~/backups/database_backup_${TIMESTAMP}.db
        echo "✅ Base de données sauvegardée depuis le filesystem"
    else
        echo "⚠️ Aucune base de données trouvée - première installation ?"
    fi
    
    # Sauvegarder les portraits depuis le filesystem s'ils existent
    if [ -d ~/static/portraits ]; then
        cp -r ~/static/portraits ~/backups/portraits_backup_${TIMESTAMP}
        echo "✅ Portraits sauvegardés depuis le filesystem"
    else
        echo "ℹ️ Aucun dossier portraits trouvé"
    fi
fi

echo ""
echo "⏹️ === ARRÊT SÉCURISÉ DE L'APPLICATION ==="

# Arrêter l'application en préservant les volumes
if [ -d ~/docker ]; then
    cd ~/docker
    if [ -f docker-compose.yml ]; then
        echo "🛑 Arrêt de l'application (volumes préservés)..."
        docker-compose down
        echo "✅ Application arrêtée"
    else
        echo "⚠️ docker-compose.yml non trouvé dans ~/docker"
    fi
else
    echo "⚠️ Dossier ~/docker non trouvé"
fi

echo ""
echo "📦 === DÉPLOIEMENT DE LA NOUVELLE VERSION ==="

cd ~/
echo "📂 Décompression du nouveau package..."
if unzip -o "$PACKAGE_NAME"; then
    echo "✅ Package décompressé"
else
    echo "❌ Erreur lors de la décompression"
    exit 1
fi

echo ""
echo "💾 === RESTAURATION DE LA BASE DE DONNÉES ET PORTRAITS ==="

# Restaurer la base de données si elle existe
if [ -f ~/backups/database_backup_${TIMESTAMP}.db ]; then
    cp ~/backups/database_backup_${TIMESTAMP}.db ./database.db
    echo "✅ Base de données restaurée"
elif [ -f ~/database.db ]; then
    echo "✅ Base de données existante préservée"
else
    echo "ℹ️ Aucune base de données à restaurer - nouvelle installation"
fi

# Restaurer les portraits s'ils existent
if [ -d ~/backups/portraits_backup_${TIMESTAMP} ]; then
    mkdir -p ./static
    cp -r ~/backups/portraits_backup_${TIMESTAMP} ./static/portraits
    echo "✅ Portraits restaurés"
elif [ -d ~/static/portraits ]; then
    mkdir -p ./static
    cp -r ~/static/portraits ./static/
    echo "✅ Portraits existants préservés"
else
    echo "ℹ️ Aucun portrait à restaurer"
    # Créer la structure des dossiers portraits pour la nouvelle installation
    mkdir -p ./static/portraits/gm ./static/portraits/characters
    echo "📁 Structure des dossiers portraits créée"
fi

echo ""
echo "⚙️ === CONFIGURATION ENVIRONNEMENT ==="

# S'assurer que le fichier .env est présent
if [ -f ~/.env ]; then
    cp ~/.env ~/docker/.env
    echo "✅ Fichier .env copié"
elif [ -f ~/docker/.env ]; then
    echo "✅ Fichier .env déjà présent dans ~/docker"
else
    echo "⚠️ ATTENTION: Fichier .env non trouvé !"
    echo "💡 Vous devrez configurer manuellement les variables d'environnement"
fi

echo ""
echo "🚀 === REDÉMARRAGE DE L'APPLICATION ==="

cd ~/docker
if [ -f docker-compose.yml ]; then
    echo "🔨 Construction et démarrage de l'application..."
    docker-compose up --build -d
    echo "✅ Application redémarrée"
else
    echo "❌ docker-compose.yml non trouvé dans ~/docker"
    exit 1
fi

echo ""
echo "🔍 === VÉRIFICATION DU DÉPLOIEMENT ==="

# Attendre que l'application démarre
echo "⏳ Attente du démarrage de l'application (10 secondes)..."
sleep 10

# Vérifier que l'application fonctionne
if docker ps | grep -q docker_app_1; then
    echo "✅ Conteneur démarré avec succès"
    
    # Test de santé
    if curl -f -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ Health check réussi"
    else
        echo "⚠️ Health check échoué - vérifiez les logs"
    fi
else
    echo "❌ Erreur: Conteneur non démarré"
    echo "📋 Logs du conteneur:"
    docker logs docker_app_1 --tail 20 2>/dev/null || echo "Impossible d'accéder aux logs"
fi

echo ""
echo "📊 === RÉSUMÉ ==="
echo "🕐 Timestamp: ${TIMESTAMP}"
echo "📦 Package: $PACKAGE_NAME"
echo "💾 Sauvegarde DB: ~/backups/database_backup_${TIMESTAMP}.db"
echo "🎨 Sauvegarde portraits: ~/backups/portraits_backup_${TIMESTAMP}"
echo "🌐 URL: http://51.210.243.134:8501"

REMOTE_SCRIPT

echo ""
echo "🎉 === MISE À JOUR VPS TERMINÉE ==="
echo "🌐 Votre application est accessible à: http://${VPS_IP}:8501"
echo "💾 Sauvegarde créée: database_backup_${TIMESTAMP}.db + portraits_backup_${TIMESTAMP}"
echo ""
echo "🔍 Pour vérifier que tout fonctionne:"
echo "   curl -f http://${VPS_IP}:8501/"
echo ""
echo "📋 Pour voir les logs en cas de problème:"
echo "   ssh ${VPS_USER}@${VPS_IP} 'docker logs docker_app_1 --tail 50'"
