#!/bin/bash

# Script de déploiement pour DnD AI GameMaster
# Usage: ./deploy.sh [dev|prod|stop|logs]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
}

# Vérifier les variables d'environnement
check_env() {
    if [ -f .env ]; then
        log_info ".env détecté – variables chargées"
        set -a; . ./.env; set +a
    else
        log_warning ".env absent – variables attendues dans l'environnement système"
    fi
}

# Créer les répertoires nécessaires
setup_directories() {
    log_info "Création des répertoires nécessaires..."
    mkdir -p data logs nginx/ssl
    log_success "Répertoires créés"
}

compose_cmd() {
    # Utiliser 'docker compose' si disponible, sinon 'docker-compose'
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

COMPOSE=$(compose_cmd)
COMPOSE_FILE="docker/docker-compose.yml"

# Déploiement en développement
deploy_dev() {
    log_info "🚀 Déploiement en mode développement..."
    
    check_docker
    check_env
    setup_directories
    
    local PROJECT_NAME="comparemodelpoc_dev"
    
    # Down d'abord pour éviter les conflits avec d'anciens conteneurs
    log_info "🧹 Arrêt des conteneurs existants (down --remove-orphans)"
    $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down --remove-orphans || true

    # Build et démarrage
    log_info "Construction de l'image Docker..."
    if [ -f .env ]; then
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file .env build
    else
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" build
    fi
    
    log_info "Démarrage des services..."
    if [ -f .env ]; then
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file .env up -d --remove-orphans
    else
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d --remove-orphans
    fi
    
    log_success "✅ Application déployée en mode développement!"
    log_info "🌐 Accès: http://localhost:8501"
    log_info "📊 Monitoring: http://localhost:8501 → onglet Performances → Monitoring Système"
}

# Déploiement en production
deploy_prod() {
    log_info "🚀 Déploiement en mode production..."
    
    check_docker
    check_env
    setup_directories
    
    # Vérifier la configuration SSL
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        log_warning "Certificats SSL non trouvés. Déploiement HTTP uniquement."
        log_warning "Pour HTTPS, placez cert.pem et key.pem dans nginx/ssl/"
    fi
    
    local PROJECT_NAME="comparemodelpoc_prod"
    # Down d'abord pour éviter les conflits
    log_info "🧹 Arrêt des conteneurs existants (down --remove-orphans)"
    $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down --remove-orphans || true

    # Build et démarrage avec profil production
    log_info "Construction de l'image Docker..."
    if [ -f .env ]; then
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file .env build
    else
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" build
    fi
    
    log_info "Démarrage des services en mode production..."
    if [ -f .env ]; then
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --env-file .env --profile production up -d --remove-orphans
    else
        $COMPOSE -p "$PROJECT_NAME" -f "$COMPOSE_FILE" --profile production up -d --remove-orphans
    fi
    
    log_success "✅ Application déployée en mode production!"
    log_info "🌐 Accès: http://localhost (ou votre domaine)"
    log_info "🔧 Proxy: Nginx reverse proxy actif"
}

# Arrêter les services
stop_services() {
    log_info "🛑 Arrêt des services..."
    local PROJECT_NAME_DEV="comparemodelpoc_dev"
    local PROJECT_NAME_PROD="comparemodelpoc_prod"
    $COMPOSE -p "$PROJECT_NAME_DEV" -f "$COMPOSE_FILE" down --remove-orphans || true
    $COMPOSE -p "$PROJECT_NAME_PROD" -f "$COMPOSE_FILE" down --remove-orphans || true
    log_success "✅ Services arrêtés"
}

# Afficher les logs
show_logs() {
    log_info "📋 Logs des services:"
    $COMPOSE -f "$COMPOSE_FILE" logs -f
}

# Nettoyage complet
cleanup() {
    log_info "🧹 Nettoyage complet..."
    local PROJECT_NAME_DEV="comparemodelpoc_dev"
    local PROJECT_NAME_PROD="comparemodelpoc_prod"
    $COMPOSE -p "$PROJECT_NAME_DEV" -f "$COMPOSE_FILE" down -v --remove-orphans || true
    $COMPOSE -p "$PROJECT_NAME_PROD" -f "$COMPOSE_FILE" down -v --remove-orphans || true
    docker system prune -f
    log_success "✅ Nettoyage terminé"
}

# Sauvegarde des données
backup() {
    log_info "💾 Sauvegarde des données..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backup_$timestamp"
    mkdir -p "$backup_dir"
    
    if [ -d "data" ]; then
        cp -r data "$backup_dir/"
    fi
    
    if [ -d "logs" ]; then
        cp -r logs "$backup_dir/"
    fi
    
    tar -czf "${backup_dir}.tar.gz" "$backup_dir"
    rm -rf "$backup_dir"
    
    log_success "✅ Sauvegarde créée: ${backup_dir}.tar.gz"
}

# Menu d'aide
show_help() {
    echo -e "${BLUE}🎲 DnD AI GameMaster - Script de déploiement${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev       Déployer en mode développement (port 8501)"
    echo "  prod      Déployer en mode production (avec Nginx)"
    echo "  stop      Arrêter tous les services"
    echo "  logs      Afficher les logs en temps réel"
    echo "  cleanup   Nettoyage complet (attention: supprime les volumes)"
    echo "  backup    Sauvegarder les données"
    echo "  help      Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 dev     # Démarrage rapide pour développement"
    echo "  $0 prod    # Déploiement production avec Nginx"
    echo "  $0 logs    # Surveiller les logs"
    echo ""
}

# Menu principal
case "${1:-help}" in
    "dev")
        deploy_dev
        ;;
    "prod")
        deploy_prod
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup
        ;;
    "help"|*)
        show_help
        ;;
esac
