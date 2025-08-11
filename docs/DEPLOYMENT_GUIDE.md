# 🚀 Guide de Déploiement - DnD AI GameMaster

## 🎯 Vue d'ensemble

Ce guide couvre tous les aspects du déploiement de DnD AI GameMaster, depuis l'installation locale jusqu'au déploiement en production avec Docker et Nginx.

## 📋 Prérequis

### **Système**
- **OS** : Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Python** : 3.8 ou supérieur
- **Docker** : 20.10+ (optionnel, pour déploiement containerisé)
- **Git** : Pour cloner le repository

### **Clés API** (au moins une requise)
- **OpenAI API Key** : Pour GPT-4, GPT-4o, DALL-E 3
- **Anthropic API Key** : Pour Claude 3.5 Sonnet  
- **DeepSeek API Key** : Pour modèle économique (optionnel)

## 🛠️ Installation Locale

### **1. Méthode Automatique (Recommandée)**

```bash
# Cloner le repository
git clone https://github.com/AFlo59/CompareModelPoc.git
cd CompareModelPoc

# Lancer l'installation automatique
python setup.py
```

Le script `setup.py` effectue automatiquement :
- ✅ Vérification de la version Python
- ✅ Installation des dépendances
- ✅ Création du fichier `.env`
- ✅ Initialisation de la base de données
- ✅ Tests de validation

### **2. Méthode Manuelle**

```bash
# 1. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 4. Initialiser la base de données
python -c \"from src.data.database import init_db; init_db()\"

# 5. Lancer l'application
python run_app.py
```

### **3. Configuration des Variables d'Environnement**

Créer le fichier `.env` basé sur `.env.example` :

```bash
# Clés API (au moins OPENAI_API_KEY requis)
OPENAI_API_KEY=sk-votre-cle-openai-ici
ANTHROPIC_API_KEY=sk-ant-votre-cle-anthropic-ici
DEEPSEEK_API_KEY=votre-cle-deepseek-ici

# Configuration optionnelle
DATABASE_PATH=database.db
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
```

### **4. Vérification de l'Installation**

```bash
# Tests unitaires
pytest tests/ -v

# Lancement de l'application
streamlit run app.py
# ou
python run_app.py
```

**Accès** : http://localhost:8501

## 🐳 Déploiement Docker

### **1. Déploiement Rapide**

```bash
# Mode développement
./deploy.sh dev

# Mode production avec Nginx
./deploy.sh prod
```

### **2. Déploiement Manuel Docker**

```bash
# Construction de l'image
docker build -t dnd-ai-gamemaster .

# Lancement du conteneur
docker run -d \\
  --name dnd-app \\
  -p 8501:8501 \\
  -e OPENAI_API_KEY=your_key \\
  -e ANTHROPIC_API_KEY=your_key \\
  -v $(pwd)/data:/app/data \\
  dnd-ai-gamemaster
```

### **3. Docker Compose**

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - \"8501:8501\"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

```bash
# Démarrage
docker-compose -f docker/docker-compose.yml up -d --remove-orphans

# Arrêt
docker-compose -f docker/docker-compose.yml down --remove-orphans
```

## 🌐 Déploiement Production

### **1. Architecture Production**

```
Internet → Nginx (80/443) → Streamlit App (8501)
              ↓
         [SSL/TLS]
         [Load Balancing]
         [Static Files]
```

### **2. Configuration Nginx**

Fichier `nginx/nginx.conf` inclus :

```nginx
upstream streamlit {
    server app:8501;
}

server {
    listen 80;
    server_name votre-domaine.com;

    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    # Configuration SSL
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Proxy vers Streamlit
    location / {
        proxy_pass http://streamlit;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Support WebSocket pour Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection \"upgrade\";
    }
}
```

### **3. Script de Déploiement Production**

```bash
# Déploiement production complet
./deploy.sh prod

# Actions disponibles
./deploy.sh stop     # Arrêter services
./deploy.sh logs     # Voir logs temps réel
./deploy.sh backup   # Sauvegarder données
./deploy.sh cleanup  # Nettoyage complet
```

### **4. Configuration SSL**

```bash
# Certificats Let's Encrypt (exemple)
certbot certonly --standalone -d votre-domaine.com

# Copier certificats
cp /etc/letsencrypt/live/votre-domaine.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/votre-domaine.com/privkey.pem nginx/ssl/key.pem

# Redémarrer Nginx
docker-compose -f docker/docker-compose.yml restart nginx
```

## ☁️ Déploiement Cloud

### **1. VPS/Serveur Dédié**

```bash
# Sur le serveur
git clone https://github.com/votre-username/CompareModelPoc.git
cd CompareModelPoc

# Configuration
cp .env.example .env
# Éditer .env avec vos clés

# Déploiement
./deploy.sh prod

# Configuration domaine/DNS
# Pointer A record vers IP serveur
```

### **2. Heroku** (Alternative)

```bash
# Procfile
echo \"web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0\" > Procfile

# Requirements
pip freeze > requirements.txt

# Déploiement
heroku create votre-app-name
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

### **3. Railway/Render/DigitalOcean App Platform**

Configuration via interface web avec :
- Repository GitHub
- Variables d'environnement
- Commande de démarrage : `streamlit run app.py`

## 📊 Monitoring & Maintenance

### **1. Logs**

```bash
# Logs application
./deploy.sh logs

# Logs spécifiques
docker logs dnd-app
docker logs nginx

# Logs système
tail -f /var/log/nginx/access.log
```

### **2. Monitoring Intégré**

L'application inclut un monitoring intégré :
- **Accès** : Interface → Performances → Monitoring Système
- **Métriques** : CPU, RAM, Disque, Réseau
- **Alertes** : Seuils configurables

### **3. Sauvegarde**

```bash
# Sauvegarde automatique
./deploy.sh backup

# Sauvegarde manuelle
cp data/database.db backup/database_$(date +%Y%m%d).db
tar -czf backup/app_$(date +%Y%m%d).tar.gz data/ logs/
```

### **4. Mise à jour**

```bash
# Mise à jour application
git pull origin main
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d --remove-orphans

# Migration base de données (automatique)
# La migration s'exécute au démarrage
```

## 🔧 Optimisations Performance

### **1. Configuration Streamlit**

```toml
# .streamlit/config.toml
[server]
maxUploadSize = 50
maxMessageSize = 50
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### **2. Configuration Nginx**

```nginx
# Optimisations dans nginx.conf
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# Cache statique
location /static/ {
    expires 1y;
    add_header Cache-Control \"public, immutable\";
}

# Limits
client_max_body_size 50M;
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

### **3. Limites Ressources Docker**

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

## 🚨 Dépannage

### **Problèmes Courants**

#### Erreur \"Module not found\"
```bash
# Réinstaller dépendances
pip install -r requirements.txt
```

#### Erreur base de données
```bash
# Réinitialiser base de données
rm database.db
python -c \"from database import init_db; init_db()\"
```

#### Erreur clés API
```bash
# Vérifier configuration
cat .env
# Tester clés
python -c \"from config import Config; print(Config.validate_api_keys())\"
```

#### Problème ports Docker
```bash
# Vérifier ports utilisés
netstat -tlnp | grep :8501
# Changer port si nécessaire
docker run -p 8502:8501 dnd-ai-gamemaster
```

### **Logs de Debug**

```bash
# Mode debug
export LOG_LEVEL=DEBUG
streamlit run app.py

# Logs détaillés Docker
docker-compose -f docker/docker-compose.yml logs -f app
```

## 📈 Surveillance

### **1. Health Checks**

```bash
# Health check intégré
curl -f http://localhost:8501/health

# Dans Docker Compose
healthcheck:
  test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:8501\"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### **2. Alertes**

Configuration optionnelle avec tools externes :
- **Uptime Robot** : Monitoring uptime
- **Grafana** : Dashboards métriques
- **Sentry** : Monitoring erreurs

## 📚 Ressources Supplémentaires

- **Documentation Streamlit** : https://docs.streamlit.io/
- **Docker Documentation** : https://docs.docker.com/
- **Nginx Guide** : https://nginx.org/en/docs/
- **Let's Encrypt** : https://letsencrypt.org/

---

**Support** : Pour toute question, ouvrez une issue sur GitHub ou consultez les logs d'application.
