#!/bin/bash
# Script de déploiement OVH avec RESET de la base de données
# ⚠️  ATTENTION : Ce script supprime complètement la base de données existante

set -e  # Arrêter en cas d'erreur

VPS_IP="51.210.243.134"
VPS_USER="debian"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Déploiement OVH avec RESET de la base de données - $TIMESTAMP"
echo "📍 Serveur: $VPS_IP"
echo "👤 Utilisateur: $VPS_USER"
echo ""
echo "⚠️  ATTENTION : Ce déploiement va SUPPRIMER COMPLÈTEMENT la base de données existante !"
echo "⚠️  Tous les utilisateurs, campagnes et personnages seront perdus !"
echo ""
read -p "Voulez-vous vraiment continuer ? (tapez 'RESET' pour confirmer): " confirm

if [ "$confirm" != "RESET" ]; then
    echo "❌ Déploiement annulé"
    exit 1
fi

echo ""
echo "🔥 Confirmation reçue - Procédure de reset en cours..."

# 1. Créer le package localement
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

# 3. Déploiement avec reset sur le serveur
echo ""
echo "🔥 Déploiement avec RESET sur le serveur..."

ssh ${VPS_USER}@${VPS_IP} << 'REMOTE_SCRIPT'

set -e

echo ""
echo "🔥 === ARRÊT ET NETTOYAGE COMPLET ==="

# Arrêter l'application
if [ -d ~/docker ]; then
    cd ~/docker
    if [ -f docker-compose.yml ]; then
        echo "🛑 Arrêt de l'application..."
        docker-compose down -v  # -v pour supprimer aussi les volumes !
        echo "✅ Application arrêtée et volumes supprimés"
    fi
fi

# Supprimer complètement les volumes Docker persistants
echo "🗑️ Suppression des volumes Docker existants..."
docker volume ls -q | grep "docker_app" | xargs -r docker volume rm || echo "ℹ️ Aucun volume à supprimer"
echo "✅ Volumes Docker nettoyés"

# Supprimer l'ancienne base de données et portraits
echo "🗑️ Suppression de l'ancienne base de données et portraits..."
rm -f ~/database.db
rm -rf ~/static/portraits
echo "✅ Ancienne base de données et portraits supprimés"

# Créer sauvegarde de sécurité (juste au cas où)
mkdir -p ~/backups
echo "$(date): Reset complet effectué" >> ~/backups/reset_log.txt

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

# Créer les dossiers nécessaires pour les portraits
echo "📁 Création des dossiers pour les portraits..."
mkdir -p ./static/portraits/gm
mkdir -p ./static/portraits/characters
echo "✅ Structure des dossiers créée"

echo ""
echo "🚀 === DÉMARRAGE DE L'APPLICATION AVEC BASE VIERGE ==="

cd ~/docker
echo "🏗️ Construction et démarrage de l'application..."
if docker-compose up -d --build; then
    echo "✅ Application démarrée avec succès !"
    
    # Attendre que l'application soit prête
    echo "⏳ Attente que l'application soit prête..."
    sleep 30
    
    # Vérifier le statut
    echo "🔍 Vérification du statut..."
    docker-compose ps
    
    echo ""
    echo "🎉 === DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ! ==="
    echo "✅ Base de données : NEUVE (réinitialisée)"
    echo "✅ Portraits : Dossiers créés et prêts"
    echo "✅ Application : Démarrée sur http://localhost:8501"
    echo ""
    echo "📝 Notes importantes :"
    echo "   • La base de données est complètement vierge"
    echo "   • Tous les anciens comptes utilisateurs ont été supprimés"
    echo "   • Les nouveaux portraits seront stockés localement"
    echo "   • Les volumes Docker ont été recréés"
    
else
    echo "❌ Erreur lors du démarrage"
    echo "📋 Logs de débogage :"
    docker-compose logs --tail=20
    exit 1
fi

REMOTE_SCRIPT

echo ""
echo "🎉 === DÉPLOIEMENT AVEC RESET TERMINÉ ==="
echo "✅ Application déployée avec base de données vierge"
echo "✅ Système de portraits configuré pour stockage local"
echo ""
echo "🌐 Accès : http://$VPS_IP:8501"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. Créez un nouveau compte utilisateur"
echo "   2. Testez la création d'une campagne (portrait MJ)"
echo "   3. Testez la création d'un personnage (portrait character)"
echo "   4. Vérifiez que les portraits sont bien stockés localement"

# Nettoyer le package local
rm -f "$PACKAGE_FILE"
echo "🧹 Package local nettoyé"
