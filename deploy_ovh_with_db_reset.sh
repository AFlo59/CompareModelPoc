#!/bin/bash
# Script de mise à jour VPS OVH avec RESET de la base de données
# ⚠️  ATTENTION : Ce script supprime complètement la base de données existante
# Basé sur update_vps.sh mais avec reset complet

set -e  # Arrêter en cas d'erreur

VPS_IP="51.210.243.134"
VPS_USER="debian"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Mise à jour VPS avec RESET de la base de données - $TIMESTAMP"
echo "📍 Serveur: $VPS_IP"
echo "👤 Utilisateur: $VPS_USER"
echo ""
echo "⚠️  ATTENTION : Ce déploiement va SUPPRIMER COMPLÈTEMENT la base de données existante !"
echo "⚠️  Tous les utilisateurs, campagnes et personnages seront perdus !"
echo "⚠️  Cette opération est IRRÉVERSIBLE !"
echo ""
read -p "Voulez-vous vraiment continuer ? (tapez 'RESET' pour confirmer): " confirm

if [ "$confirm" != "RESET" ]; then
    echo "❌ Déploiement annulé"
    exit 1
fi

echo ""
echo "🔥 Confirmation reçue - Procédure de reset en cours..."

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

# 3. Mise à jour sur le serveur avec RESET
echo ""
echo "🔥 Mise à jour sur le serveur avec RESET COMPLET des données..."

ssh ${VPS_USER}@${VPS_IP} << REMOTE_SCRIPT

set -e

echo ""
echo "🔥 === ARRÊT ET NETTOYAGE COMPLET ==="

# Arrêter l'application en supprimant TOUS les volumes
if [ -d ~/docker ]; then
    cd ~/docker
    if [ -f docker-compose.yml ]; then
        echo "🛑 Arrêt de l'application avec suppression des volumes..."
        docker-compose down -v --remove-orphans
        echo "✅ Application arrêtée et volumes supprimés"
    else
        echo "⚠️ docker-compose.yml non trouvé dans ~/docker"
    fi
else
    echo "⚠️ Dossier ~/docker non trouvé"
fi

# Supprimer complètement les volumes Docker persistants (nettoyage approfondi)
echo "🗑️ Suppression des volumes Docker existants..."
docker volume ls -q | grep -E "(docker_app|comparemodel)" | xargs -r docker volume rm || echo "ℹ️ Aucun volume à supprimer"
echo "✅ Volumes Docker nettoyés"

# Supprimer l'ancienne base de données et portraits
echo "🗑️ Suppression complète de l'ancienne base de données et portraits..."
rm -f ~/database.db
rm -rf ~/static/portraits
rm -rf ~/data  # Supprimer aussi le dossier data s'il existe
echo "✅ Ancienne base de données et portraits supprimés"

# Créer un log de reset pour traçabilité
mkdir -p ~/backups
echo "$(date): Reset complet effectué par deploy_ovh_with_db_reset.sh - TIMESTAMP=${TIMESTAMP}" >> ~/backups/reset_log.txt

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
echo "⚙️ === CONFIGURATION ENVIRONNEMENT ==="

# S'assurer que le fichier .env est présent et configuré
if [ -f ~/.env ]; then
    cp ~/.env ~/docker/.env
    echo "✅ Fichier .env copié depuis ~/.env"
elif [ -f ~/docker/.env ]; then
    echo "✅ Fichier .env déjà présent dans ~/docker"
else
    echo "⚠️ ATTENTION: Fichier .env non trouvé !"
    echo "💡 Vous devrez configurer manuellement les variables d'environnement"
    echo "📋 Variables requises: OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY"
fi

# Créer les dossiers nécessaires pour les portraits avec permissions correctes
echo "📁 Création de la structure des dossiers pour les portraits..."
mkdir -p ./static/portraits/gm
mkdir -p ./static/portraits/characters
chmod -R 755 ./static/portraits
echo "✅ Structure des dossiers créée avec permissions correctes"

echo ""
echo "🚀 === REDÉMARRAGE DE L'APPLICATION AVEC BASE VIERGE ==="

cd ~/docker
if [ -f docker-compose.yml ]; then
    echo "🔨 Construction et démarrage de l'application (base vierge)..."
    docker-compose up --build -d
    echo "✅ Application redémarrée avec base de données vierge"
else
    echo "❌ docker-compose.yml non trouvé dans ~/docker"
    exit 1
fi

echo ""
echo "🔍 === VÉRIFICATION DU DÉPLOIEMENT ==="

# Attendre que l'application démarre
echo "⏳ Attente du démarrage de l'application (30 secondes)..."
sleep 30

# Vérifier que l'application fonctionne
if docker ps | grep -q docker_app_1; then
    echo "✅ Conteneur démarré avec succès"
    
    # Test de santé
    if curl -f -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ Health check réussi - Application fonctionnelle"
    else
        echo "⚠️ Health check échoué - Application en cours de démarrage"
        echo "💡 Attendez quelques minutes et vérifiez http://${VPS_IP}:8501"
    fi
    
    # Afficher le statut des conteneurs
    echo "🔍 Statut des conteneurs:"
    docker-compose ps
    
else
    echo "❌ Erreur: Conteneur non démarré"
    echo "📋 Logs du conteneur:"
    docker logs docker_app_1 --tail 20 2>/dev/null || echo "Impossible d'accéder aux logs"
fi

echo ""
echo "📊 === RÉSUMÉ DU RESET ==="
echo "🕐 Timestamp: ${TIMESTAMP}"
echo "📦 Package: $PACKAGE_NAME"
echo "🔥 Action: RESET COMPLET (base de données + portraits + volumes)"
echo "💾 Sauvegarde: AUCUNE (reset intentionnel)"
echo "🎨 Portraits: Structure créée et prête pour stockage local"
echo "🌐 URL: http://${VPS_IP}:8501"
echo ""
echo "🎉 === RESET ET DÉPLOIEMENT TERMINÉS AVEC SUCCÈS ! ==="
echo "✅ Base de données : NEUVE (complètement réinitialisée)"
echo "✅ Portraits : Dossiers créés et configurés pour stockage local"
echo "✅ Volumes Docker : Recréés à neuf"
echo "✅ Application : Démarrée avec configuration propre"
echo ""
echo "📝 Notes importantes :"
echo "   • La base de données est complètement vierge"
echo "   • Tous les anciens comptes utilisateurs ont été supprimés"
echo "   • Les nouveaux portraits seront automatiquement stockés localement"
echo "   • Le fix de stockage local des portraits est actif"
echo "   • Aucune donnée précédente n'a été préservée"

REMOTE_SCRIPT

echo ""
echo "🎉 === MISE À JOUR VPS AVEC RESET TERMINÉE ==="
echo "🌐 Votre application est accessible à: http://${VPS_IP}:8501"
echo "✅ Base de données complètement réinitialisée"
echo "✅ Système de portraits configuré pour stockage local"
echo ""
echo "🔍 Pour vérifier que tout fonctionne:"
echo "   curl -f http://${VPS_IP}:8501/"
echo ""
echo "📋 Prochaines étapes recommandées :"
echo "   1. Accédez à l'application et créez un nouveau compte utilisateur"
echo "   2. Testez la création d'une campagne pour vérifier la génération du portrait MJ"
echo "   3. Testez la création d'un personnage pour vérifier la génération du portrait"
echo "   4. Vérifiez dans les logs que les portraits sont bien téléchargés et stockés localement"
echo ""
echo "📋 Pour voir les logs en temps réel:"
echo "   ssh ${VPS_USER}@${VPS_IP} 'cd ~/docker && docker-compose logs -f'"

# Nettoyer le package local
rm -f "$PACKAGE_FILE"
echo "🧹 Package local nettoyé"
