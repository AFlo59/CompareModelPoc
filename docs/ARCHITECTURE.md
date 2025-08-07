# 🏗️ Architecture du Projet - DnD AI GameMaster

## Vue d'ensemble

DnD AI GameMaster est une application Streamlit modulaire qui permet de comparer les performances de différents modèles de langage (LLM) dans le contexte d'un jeu de rôle Donjons & Dragons.

## 📁 Structure du Projet

```
CompareModelPoc/
├── 📱 Interface & Navigation
│   ├── app.py                  # Application principale Streamlit
│   ├── run_app.py             # Script de lancement avec vérifications
│   └── setup.py               # Script d'installation automatique
│
├── 🔐 Authentification & Sécurité
│   └── auth.py                # Gestion utilisateurs & sécurité
│
├── 🤖 Intelligence Artificielle
│   ├── chatbot.py             # Interface de chat et gestion des modèles
│   └── portraits.py           # Génération de portraits IA (DALL-E)
│
├── 💾 Données & Persistance
│   ├── database.py            # Schéma et connexions SQLite
│   └── models.py              # Modèles de données et requêtes ORM
│
├── 📊 Analytics & Performance
│   ├── performance.py         # Analyse et visualisation des performances
│   └── system_monitoring.py   # Monitoring système temps réel
│
├── ⚙️ Configuration
│   ├── config.py              # Configuration centralisée
│   ├── requirements.txt       # Dépendances Python
│   └── pyproject.toml         # Configuration outils développement
│
├── 🐳 Déploiement
│   ├── Dockerfile             # Image Docker
│   ├── docker-compose.yml     # Orchestration multi-services
│   ├── deploy.sh              # Scripts de déploiement automatisé
│   └── nginx/                 # Configuration reverse proxy
│
├── 🧪 Tests & Qualité
│   ├── tests/                 # Tests unitaires et d'intégration
│   ├── pytest.ini            # Configuration pytest
│   └── .github/workflows/     # CI/CD GitHub Actions
│
└── 📚 Documentation
    └── docs/                  # Documentation technique
```

## 🎯 Architecture Modulaire

### 1. **Couche Présentation** (`app.py`)
- Interface utilisateur Streamlit
- Routage et navigation entre pages
- Gestion des sessions utilisateur
- Intégration des composants UI

### 2. **Couche Authentification** (`auth.py`)
- Validation des emails et mots de passe
- Hachage sécurisé (bcrypt)
- Gestion des sessions utilisateur
- Contrôle d'accès aux fonctionnalités

### 3. **Couche Intelligence Artificielle**
- **`chatbot.py`** : Interface conversationnelle
- **`portraits.py`** : Génération d'images via DALL-E
- Support multi-modèles (GPT-4, Claude, DeepSeek)
- Gestion des contextes et historiques

### 4. **Couche Données**
- **`database.py`** : Schéma SQLite et migrations
- **`models.py`** : ORM simplifié et requêtes métier
- Persistance des conversations et statistiques
- Gestion transactionnelle

### 5. **Couche Analytics**
- **`performance.py`** : Métriques et visualisations
- **`system_monitoring.py`** : Monitoring infrastructure
- Tableaux de bord interactifs (Plotly)
- Export et reporting

### 6. **Couche Configuration**
- **`config.py`** : Configuration centralisée
- Gestion des clés API et paramètres
- Support multi-environnements
- Validation des configurations

## 🔄 Flux de Données

### 1. **Authentification**
```
Utilisateur → auth.py → database.py → Session Streamlit
```

### 2. **Chat IA**
```
Interface → chatbot.py → API IA → database.py → performance.py
```

### 3. **Analytics**
```
database.py → performance.py → Visualisations Plotly → Interface
```

## 🗄️ Modèle de Données

### Tables Principales

#### `users`
```sql
id INTEGER PRIMARY KEY
email TEXT UNIQUE NOT NULL  
password TEXT NOT NULL (bcrypt hash)
```

#### `campaigns` 
```sql
id INTEGER PRIMARY KEY
user_id INTEGER FK
name TEXT
themes TEXT (JSON)
language TEXT
gm_portrait TEXT (URL)
```

#### `characters`
```sql
id INTEGER PRIMARY KEY  
user_id INTEGER FK
name TEXT
class TEXT
race TEXT
description TEXT
portrait_url TEXT
```

#### `messages`
```sql
id INTEGER PRIMARY KEY
user_id INTEGER FK
campaign_id INTEGER FK  
role TEXT (system/user/assistant)
content TEXT
timestamp DATETIME
```

#### `performance_logs`
```sql
id INTEGER PRIMARY KEY
user_id INTEGER FK
campaign_id INTEGER FK
model TEXT
latency REAL
tokens_in INTEGER
tokens_out INTEGER  
timestamp DATETIME
```

## 🔧 Patterns Architecturaux

### 1. **Repository Pattern** (`models.py`)
- Abstraction des accès aux données
- Encapsulation de la logique SQL
- Context managers pour les transactions

### 2. **Configuration Pattern** (`config.py`)
- Centralisation des paramètres
- Validation des configurations
- Support multi-environnements

### 3. **Factory Pattern** (APIs IA)
- Création dynamique des clients IA
- Abstraction des différences entre APIs
- Gestion uniforme des modèles

### 4. **Observer Pattern** (Performance)
- Enregistrement automatique des métriques
- Événements de performance
- Analytics en temps réel

## 🚀 Technologies & Stack

### **Frontend**
- **Streamlit** : Framework web Python
- **Plotly** : Visualisations interactives
- **CSS Custom** : Styles personnalisés

### **Backend**
- **Python 3.8+** : Langage principal
- **SQLite** : Base de données intégrée
- **bcrypt** : Hachage sécurisé

### **Intelligence Artificielle**
- **OpenAI API** : GPT-4, GPT-4o, DALL-E 3
- **Anthropic API** : Claude 3.5 Sonnet
- **DeepSeek API** : Modèle économique

### **Infrastructure**
- **Docker** : Containerisation
- **Nginx** : Reverse proxy (production)
- **GitHub Actions** : CI/CD

### **Développement**
- **pytest** : Tests unitaires
- **black** : Formatage du code
- **mypy** : Vérification de types

## 🔐 Sécurité

### **Authentification**
- Hachage bcrypt avec salt
- Validation stricte des mots de passe
- Sessions sécurisées Streamlit

### **Données**
- Validation des entrées utilisateur
- Requêtes SQL paramétrées
- Isolation des données par utilisateur

### **APIs**
- Gestion sécurisée des clés API
- Variables d'environnement
- Timeout et retry logic

## 📈 Performance & Scalabilité

### **Optimisations**
- Connexions SQLite poolées
- Cache des configurations
- Lazy loading des modules lourds

### **Monitoring**
- Métriques de performance automatiques
- Monitoring système intégré
- Alertes sur les erreurs

### **Limites Actuelles**
- SQLite : ~1000 utilisateurs concurrent
- Streamlit : Interface single-threaded
- APIs : Rate limiting selon fournisseurs

## 🔮 Évolutions Futures

### **Technique**
- Migration vers PostgreSQL
- Architecture microservices
- Cache Redis
- Load balancing

### **Fonctionnel**
- Support WebRTC pour le multijoueur
- Plugin system pour les modèles
- API REST publique
- Interface mobile native

---

Cette architecture modulaire permet une maintenance facile, des tests efficaces, et une évolutivité progressive du système.
