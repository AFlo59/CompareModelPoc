# 🐳 Guide de Déploiement Docker

Ce guide vous explique comment déployer DnD AI GameMaster avec Docker pour un environnement de production ou de développement.

## 📋 Prérequis

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** pour cloner le repository

### Installation Docker (Ubuntu/Debian)

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER

# Installation Docker Compose
sudo apt install docker-compose-plugin

# Redémarrer pour appliquer les changements de groupe
newgrp docker
```

## 🚀 Déploiement Rapide

### 1. Cloner et configurer

```bash
git clone https://github.com/AFlo59/CompareModelPoc.git
cd CompareModelPoc
```

### 2. Configuration des variables d'environnement

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer avec vos clés API
nano .env
```

Configurez au minimum :
```env
OPENAI_API_KEY=sk-votre-cle-openai
ANTHROPIC_API_KEY=sk-ant-votre-cle-anthropic
```

### 3. Déploiement

#### Mode Développement (recommandé pour débuter)
```bash
./deploy.sh dev
```

#### Mode Production (avec Nginx)
```bash
./deploy.sh prod
```

## 🎛️ Commandes de Gestion

```bash
# Voir les logs en temps réel
./deploy.sh logs

# Arrêter tous les services
./deploy.sh stop

# Sauvegarder les données
./deploy.sh backup

# Nettoyage complet (⚠️ supprime tout)
./deploy.sh cleanup

# Aide
./deploy.sh help
```

## 📊 Accès à l'Application

### Mode Développement
- **Application** : http://localhost:8501
- **Monitoring Système** : Interface intégrée dans l'onglet "Performances"

### Mode Production
- **Application** : http://localhost (ou votre domaine)
- **Proxy** : Nginx reverse proxy actif

## 🔧 Configuration Avancée

### Variables d'Environnement Complètes

```env
# APIs (obligatoires)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key

# Base de données
DATABASE_PATH=/app/data/database.db

# Streamlit (optionnel)
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Configuration SSL (Production)

Pour activer HTTPS en production :

1. Placez vos certificats SSL :
```bash
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

2. Décommentez la configuration HTTPS dans `nginx/nginx.conf`

3. Redéployez :
```bash
./deploy.sh prod
```

### Personnalisation des Ports

Modifiez `docker-compose.yml` pour changer les ports :

```yaml
services:
  app:
    ports:
      - "8080:8501"  # Change le port external
  nginx:
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS
```

## 📈 Monitoring et Logs

### Monitoring Système Intégré

L'application inclut un monitoring système complet accessible via :
- **Interface Web** : Onglet "Performances" → "Monitoring Système"
- **Métriques** : CPU, RAM, Disque, Réseau, Process Streamlit

### Logs Docker

```bash
# Logs de l'application
docker-compose logs -f app

# Logs Nginx (production)
docker-compose logs -f nginx

# Logs avec timestamps
docker-compose logs -f -t
```

### Fichiers de Logs

Les logs sont persistants dans :
- `./logs/` : Logs applicatifs
- Docker logs : via `docker-compose logs`

## 🔄 Mise à Jour

```bash
# Arrêter les services
./deploy.sh stop

# Récupérer les dernières modifications
git pull origin main

# Reconstruire et redéployer
./deploy.sh dev  # ou prod
```

## 🛠️ Dépannage

### Problèmes Courants

**Port 8501 déjà utilisé**
```bash
# Vérifier les processus utilisant le port
sudo lsof -i :8501

# Arrêter Streamlit local si nécessaire
pkill -f streamlit
```

**Erreurs de permissions**
```bash
# Réassigner les permissions
sudo chown -R $USER:$USER data/ logs/

# Vérifier les groupes Docker
groups $USER
```

**Base de données corrompue**
```bash
# Sauvegarder d'abord
./deploy.sh backup

# Supprimer la base et redémarrer
rm data/database.db
./deploy.sh dev
```

### Logs de Debug

Activez les logs détaillés :

```yaml
# Dans docker-compose.yml
services:
  app:
    environment:
      - STREAMLIT_LOGGER_LEVEL=debug
```

## 📊 Monitoring de Production

### Health Checks

L'application inclut des health checks automatiques :
- **Docker** : Vérifie le port 8501
- **Nginx** : Endpoint `/health`

### Métriques Système

Via l'interface web :
1. Ouvrir l'application
2. Aller dans "Performances"
3. Onglet "Monitoring Système"

Métriques disponibles :
- ✅ CPU (global + par cœur)
- ✅ Mémoire RAM et Swap
- ✅ Stockage (tous les disques)
- ✅ Réseau (trafic entrant/sortant)
- ✅ Process Streamlit (PID, mémoire, threads)

## 🔐 Sécurité

### Bonnes Pratiques

1. **Variables d'environnement** : Ne jamais committer `.env`
2. **SSL** : Utilisez HTTPS en production
3. **Firewall** : Limitez l'accès aux ports nécessaires
4. **Mise à jour** : Maintenez Docker et l'app à jour

### Configuration Nginx Sécurisée

Le fichier `nginx/nginx.conf` inclut :
- Headers de sécurité
- Configuration SSL moderne
- Protection contre les attaques communes

## 💾 Sauvegarde et Restauration

### Sauvegarde Automatique

```bash
# Sauvegarde complète
./deploy.sh backup

# Sauvegarde manuelle
tar -czf backup_$(date +%Y%m%d).tar.gz data/ logs/
```

### Restauration

```bash
# Arrêter les services
./deploy.sh stop

# Restaurer les données
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz
cp -r backup_YYYYMMDD_HHMMSS/data/* data/

# Redémarrer
./deploy.sh dev
```

## 🎯 Optimisation Performance

### Ressources Recommandées

**Minimum :**
- CPU : 2 cœurs
- RAM : 2 GB
- Stockage : 5 GB

**Recommandé :**
- CPU : 4 cœurs
- RAM : 4 GB
- Stockage : 20 GB

### Configuration Docker

Limitez les ressources si nécessaire :

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 📞 Support

En cas de problème :

1. Vérifiez les logs : `./deploy.sh logs`
2. Consultez la documentation GitHub
3. Vérifiez les issues existantes
4. Créez une nouvelle issue avec les logs

---

**Bon déploiement ! 🚀**
