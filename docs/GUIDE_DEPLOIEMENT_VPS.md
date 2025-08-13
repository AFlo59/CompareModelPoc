# 🚀 Guide de Déploiement - DnD AI GameMaster sur VPS OVH

Ce guide détaille les étapes complètes pour déployer l'application DnD AI GameMaster sur un serveur VPS OVH avec Docker.

## 📋 Prérequis

### Serveur VPS
- **IP**: 51.210.243.134
- **OS**: Debian 12 (Bookworm)
- **Utilisateur**: debian
- **Accès**: SSH avec mot de passe

### Local
- Python 3.10+
- Git
- Docker (optionnel pour tests locaux)

## 🔧 Étape 1 : Préparation Locale

### 1.1 Vérification des prérequis
```bash
# Vérifier la structure du projet
python scripts/deploy.py check
```

### 1.2 Validation des tests
```bash
# Exécuter la suite de tests complète
python -m pytest --tb=short

# Vérifier la qualité du code
isort --check-only --diff src/ tests/ --skip-gitignore
black --check src/ tests/
```

### 1.3 Création du package de production
```bash
# Créer le package de déploiement
python scripts/deploy.py package
```

## 🌐 Étape 2 : Configuration du Serveur VPS

### 2.1 Test de connectivité
```bash
# Tester la connexion SSH
ssh -o ConnectTimeout=10 debian@51.210.243.134 "echo 'Connexion SSH réussie au VPS OVH'"
```

### 2.2 Copie du package sur le serveur
```bash
# Copier le package de déploiement (remplacer par le nom de votre package)
scp dist/dnd-gamemaster-YYYYMMDD-HHMMSS.zip debian@51.210.243.134:~/
```

### 2.3 Installation des outils sur le serveur
```bash
ssh debian@51.210.243.134 "
# Mise à jour du système
sudo apt update

# Installation des outils nécessaires
sudo apt install -y unzip curl git docker.io docker-compose

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker debian

# Démarrer et activer Docker
sudo systemctl start docker
sudo systemctl enable docker

echo 'Outils installés avec succès'
"
```

## 📦 Étape 3 : Déploiement de l'Application

### 3.1 Décompression et configuration
```bash
ssh debian@51.210.243.134 "
# Décompresser le package (remplacer par le nom de votre fichier)
cd ~/
unzip -o dnd-gamemaster-YYYYMMDD-HHMMSS.zip

# Créer le fichier .env avec les configurations
cat > .env << 'EOF'
OPENAI_API_KEY=votre_cle_openai_ici
ANTHROPIC_API_KEY=votre_cle_anthropic_ici
DEEPSEEK_API_KEY=votre_cle_deepseek_ici

# === CONFIGURATION PRODUCTION ===
DEBUG=false
LOG_LEVEL=INFO
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
DATABASE_PATH=./database.db
PORTRAIT_PRIMARY_IMAGE_MODEL=dall-e-3
PORTRAIT_FALLBACK_IMAGE_MODEL=dall-e-2
PORTRAIT_FALLBACK=true
AI_AUTO_FALLBACK=true
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
EOF

echo 'Configuration terminée'
"
```

### 3.2 Lancement avec Docker Compose
```bash
ssh debian@51.210.243.134 "
# Accéder aux permissions Docker (nécessite une nouvelle session)
newgrp docker << 'SCRIPT'

# Aller dans le dossier docker
cd ~/docker

# Copier le fichier .env dans le dossier docker
cp ../.env .

# Construire et lancer l'application
docker-compose up --build -d

echo 'Application déployée avec succès!'
SCRIPT
"
```

## 🔍 Étape 4 : Vérification du Déploiement

### 4.1 Vérification des conteneurs
```bash
ssh debian@51.210.243.134 "
# Vérifier le statut des conteneurs
docker ps

# Vérifier les logs de l'application
docker logs docker_app_1 --tail 20
"
```

### 4.2 Test de santé de l'application
```bash
ssh debian@51.210.243.134 "
# Tester l'accès local à l'application
curl -f http://localhost:8501/_stcore/health

# Vérifier que le port est ouvert
ss -tuln | grep 8501
"
```

### 4.3 Configuration du pare-feu (si nécessaire)
```bash
ssh debian@51.210.243.134 "
# Pour les systèmes avec iptables
sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

# Ou pour les systèmes avec ufw
sudo ufw allow 8501
"
```

## 🌍 Étape 5 : Accès à l'Application

### 5.1 Test d'accès externe
```bash
# Depuis votre machine locale
curl -f -m 10 http://51.210.243.134:8501/
```

### 5.2 Accès via navigateur
Ouvrez votre navigateur et allez à :
```
http://51.210.243.134:8501
```

## 🔧 Étape 6 : Gestion de l'Application

### 6.1 Commandes de base Docker Compose
```bash
ssh debian@51.210.243.134 "
cd ~/docker

# Arrêter l'application
docker-compose down

# Redémarrer l'application
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f

# Reconstruire et redémarrer
docker-compose up --build -d
"
```

### 6.2 Mise à jour de l'application
```bash
# 1. Créer un nouveau package localement
python scripts/deploy.py package

# 2. Copier sur le serveur
scp dist/nouveau-package.zip debian@51.210.243.134:~/

# 3. Déployer sur le serveur
ssh debian@51.210.243.134 "
cd ~/docker
docker-compose down

cd ~/
unzip -o nouveau-package.zip

cd ~/docker
docker-compose up --build -d
"
```

## 📊 Étape 7 : Monitoring et Maintenance

### 7.1 Surveillance des logs
```bash
ssh debian@51.210.243.134 "
# Logs de l'application
docker logs docker_app_1 --tail 50

# Logs système Docker
sudo journalctl -u docker.service --tail 20

# Utilisation des ressources
docker stats
"
```

### 7.2 Sauvegarde de la base de données
```bash
ssh debian@51.210.243.134 "
# Créer une sauvegarde de la base de données
docker exec docker_app_1 cp /app/database.db /app/data/backup_\$(date +%Y%m%d_%H%M%S).db

# Ou copier depuis le volume Docker
docker cp docker_app_1:/app/database.db ~/backup_database_\$(date +%Y%m%d_%H%M%S).db
"
```

## ⚠️ Limitations Connues

### Page Performance - Évolution Temporelle

#### Problème identifié
La section "Évolution temporelle" de la page Performance présente des limitations :

- **Coûts** : ✅ Fonctionnent correctement
- **Tokens** : ❌ Graphique vide (problème d'agrégation)
- **Latence** : ❌ Graphique vide (problème d'agrégation)

#### Pourquoi le graphique Tokens pose problème
```bash
# Les tokens dépassent souvent la limite d'affichage
Limite maximum: 300 tokens
Utilisation réelle à l'initialisation: 500-1000+ tokens
```

#### Solutions temporaires
1. **Voir uniquement les coûts** dans l'évolution temporelle
2. **Utiliser les métriques globales** pour les tokens totaux
3. **Vérifier les données détaillées** dans l'expander pour les vraies valeurs

#### Impact sur l'utilisation
- **Aucun impact fonctionnel** sur l'application
- **Métriques principales disponibles** (résumé, comparaison modèles)
- **Données correctes** dans les sections autres que l'évolution temporelle

## 🚨 Dépannage

### Problèmes courants et solutions

#### L'application ne démarre pas
```bash
# Vérifier les logs
docker logs docker_app_1

# Vérifier la configuration
cat ~/docker/.env

# Reconstruire complètement
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Variables d'environnement non chargées
```bash
# Vérifier que le fichier .env est au bon endroit
ls -la ~/docker/.env

# Redémarrer avec les variables explicites
docker-compose --env-file .env up -d
```

#### Port non accessible
```bash
# Vérifier que le port est ouvert
ss -tuln | grep 8501

# Vérifier les règles pare-feu
sudo iptables -L | grep 8501

# Ouvrir le port si nécessaire
sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
```

#### Page Performance affiche des graphiques vides
```bash
# Problème connu - Évolution temporelle
# Solution 1: Utiliser les autres métriques
Utiliser les sections "Résumé" et "Comparaison des modèles"

# Solution 2: Vérifier les données détaillées
Ouvrir l'expander "Données détaillées" pour voir les valeurs exactes

# Solution 3: Attendre plus de données
Les graphiques temporels nécessitent plusieurs jours de données
```

#### Problèmes de permissions Docker
```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker debian

# Se reconnecter pour appliquer les changements
exit
ssh debian@51.210.243.134
```

## 📝 Variables d'Environnement

### Variables requises dans `.env`
```bash
# API Keys (obligatoires)
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...

# Configuration de base
DEBUG=false
LOG_LEVEL=INFO
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
DATABASE_PATH=./database.db

# Configuration des portraits
PORTRAIT_PRIMARY_IMAGE_MODEL=dall-e-3
PORTRAIT_FALLBACK_IMAGE_MODEL=dall-e-2
PORTRAIT_FALLBACK=true

# Configuration IA
AI_AUTO_FALLBACK=true
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

## 🔐 Sécurité

### Recommandations de sécurité
1. **Changez les mots de passe par défaut**
2. **Configurez SSH avec des clés au lieu de mots de passe**
3. **Mettez à jour régulièrement le système**
4. **Surveillez les logs d'accès**
5. **Sauvegardez régulièrement la base de données**

### Configuration SSH avec clés
```bash
# Sur votre machine locale, générer une clé SSH
ssh-keygen -t rsa -b 4096 -C "votre_email@example.com"

# Copier la clé publique sur le serveur
ssh-copy-id debian@51.210.243.134

# Tester la connexion sans mot de passe
ssh debian@51.210.243.134
```

## 📞 Support

### Commandes utiles pour le diagnostic
```bash
# État général du système
ssh debian@51.210.243.134 "
echo '=== État des conteneurs ==='
docker ps -a

echo '=== Utilisation des ressources ==='
df -h
free -h

echo '=== Logs récents ==='
docker logs docker_app_1 --tail 10

echo '=== Configuration réseau ==='
ss -tuln | grep 8501
"
```

### Logs et fichiers importants
- **Logs de l'application**: `docker logs docker_app_1`
- **Configuration**: `~/docker/.env`
- **Base de données**: Volume Docker `docker_app_data`
- **Logs Docker**: `sudo journalctl -u docker.service`

---

## 📚 Annexes

### Structure des fichiers sur le serveur
```
/home/debian/
├── .env                          # Variables d'environnement
├── dnd-gamemaster-*.zip         # Package de déploiement
├── docker/                      # Configuration Docker
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env                     # Copie locale
│   └── nginx/
├── src/                         # Code source
├── requirements/                # Dépendances Python
└── docs/                        # Documentation
```

### Commandes de déploiement rapide
```bash
# Script complet de déploiement (à adapter)
#!/bin/bash
PACKAGE_NAME="dnd-gamemaster-$(date +%Y%m%d-%H%M%S).zip"

# 1. Créer le package
python scripts/deploy.py package

# 2. Copier sur le serveur
scp dist/$PACKAGE_NAME debian@51.210.243.134:~/

# 3. Déployer
ssh debian@51.210.243.134 "
cd ~/docker && docker-compose down
cd ~/ && unzip -o $PACKAGE_NAME
cd ~/docker && docker-compose up --build -d
echo 'Déploiement terminé!'
"
```

---

**Date de création**: 13 août 2025  
**Version**: 1.0  
**Auteur**: Assistant AI  
**Projet**: DnD AI GameMaster
