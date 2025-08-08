# 🎲 DnD AI GameMaster

Une application Streamlit innovante qui permet de comparer les performances de différents modèles de langage (LLM) dans le contexte d'un jeu de rôle Donjons & Dragons. L'application vous permet de créer des personnages, des campagnes, et d'interagir avec un Maître du Jeu IA alimenté par différents modèles d'IA.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-v1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Fonctionnalités

### 🤖 Modèles IA Supportés
- **GPT-4** : Le plus avancé, créatif et précis
- **GPT-4o** : Optimisé, rapide et économique  
- **Claude 3.5 Sonnet** : Excellent pour le roleplay et la narration
- **DeepSeek** : Le plus économique, bon rapport qualité/prix

### ⚡ Fonctionnalités Clés
- 🔐 **Authentification renforcée** avec protection force brute & session timeout
- 🎭 **Création de personnages** avec génération de portraits IA optimisée
- 📚 **Gestion de campagnes** multi-thèmes et multi-langues
- 💬 **Interface de chat** immersive avec historique persistant
- 📊 **Analyse de performances** avec graphiques interactifs temps réel
- 🎨 **Génération de portraits** via DALL-E 3 avec gestion d'erreurs
- 🌍 **Support multilingue** (FR/EN)
- 💰 **Calcul coûts temps réel** pour tous les modèles IA
- 🖥️ **Monitoring système** avancé (CPU, RAM, réseau)
- ⚡ **Base de données optimisée** (WAL mode, cache, pooling)

## 🛠️ Installation

### Pré-requis
- Python 3.8 ou supérieur
- Clés API pour les services que vous souhaitez utiliser :
  - OpenAI API Key (pour GPT-4, GPT-4o, DALL-E)
  - Anthropic API Key (pour Claude 3.5 Sonnet)
  - DeepSeek API Key (optionnel)

### Installation locale

1. **Cloner le repository :**
```bash
git clone https://github.com/AFlo59/CompareModelPoc.git
cd CompareModelPoc
```

2. **Créer un environnement virtuel :**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances :**
```bash
pip install -r requirements/requirements.txt
pip install -r requirements/dev-requirements.txt  # Pour le développement
```

4. **Configurer les variables d'environnement :**
```bash
cp .env.example .env
# Éditer .env avec vos vraies clés API
```

5. **Lancer l'application :**
```bash
# 🏠 MÉTHODE 1: Lancement direct (le plus simple)
python run_app.py

# 🏠 MÉTHODE 2: Streamlit direct
streamlit run src/ui/app.py

# 🔧 MÉTHODE 3: Via script de développement (avec outils)
python scripts/dev.py run                # Version legacy
python scripts/dev.py run --refactored   # Version optimisée

# 🐳 MÉTHODE 4: Docker (pour production ou isolement)
python scripts/deploy.py docker          # Via script automatisé
# OU
cd docker/ && docker-compose up          # Docker-compose direct
```

### ⚡ **Résumé des méthodes de lancement**

| Méthode | Commande | Usage | Docker |
|---------|----------|--------|--------|
| **Direct** | `python run_app.py` | Simple, rapide | ❌ Non |
| **Streamlit** | `streamlit run src/ui/app.py` | Debug interface | ❌ Non |
| **Dev script** | `python scripts/dev.py run` | Développement + outils | ❌ Non |
| **Deploy local** | `python scripts/deploy.py local` | Test déploiement | ❌ Non |
| **Deploy Docker** | `python scripts/deploy.py docker` | Production, isolement | ✅ Oui |
| **Docker direct** | `cd docker/ && docker-compose up` | Docker manuel | ✅ Oui |

### Configuration des secrets GitHub (pour CI/CD)

Pour que les tests automatisés fonctionnent, ajoutez ces secrets dans votre repository GitHub :

1. Allez dans **Settings** → **Secrets and variables** → **Actions**
2. Ajoutez ces secrets :
   - `OPENAI_API_KEY` : Votre clé API OpenAI
   - `ANTHROPIC_API_KEY` : Votre clé API Anthropic  
   - `DEEPSEEK_API_KEY` : Votre clé API DeepSeek (optionnel)

### Installation automatique

1. **Clonez le repository**
   ```bash
   git clone https://github.com/votre-username/CompareModelPoc.git
   cd CompareModelPoc
   ```

2. **Exécutez le script d'installation**
   ```bash
   python scripts/setup.py
   ```

3. **Configurez vos clés API**
   
   Éditez le fichier `.env` créé automatiquement :
   ```bash
   OPENAI_API_KEY=sk-votre-cle-openai
   ANTHROPIC_API_KEY=sk-ant-api03-votre-cle-anthropic
   DEEPSEEK_API_KEY=votre-cle-deepseek
   ```

4. **Lancez l'application**
   ```bash
# Méthode classique
python run_app.py

# Méthodes automatisées (recommandé)
python scripts/dev.py run                 # Version legacy
python scripts/dev.py run --refactored    # Version optimisée

# Configuration rapide première fois
python scripts/setup_quick.py
```

## 🛠️ Scripts d'automatisation

Le projet inclut **3 scripts automatisés** pour simplifier le développement et déploiement :

### ⚡ `setup_quick.py` - Configuration express
Configuration automatique en 30 secondes :
```bash
python scripts/setup_quick.py           # Tout-en-un rapide
```

### 🔧 `dev.py` - Développement LOCAL (sans Docker)
```bash
python scripts/dev.py setup              # Configure l'environnement complet
python scripts/dev.py run                # Lance l'app LOCAL (legacy)
python scripts/dev.py run --refactored   # Lance l'app LOCAL (version optimisée)
python scripts/dev.py test               # Exécute les 158 tests
python scripts/dev.py test --no-coverage # Tests sans couverture
python scripts/dev.py check              # Vérifications qualité (Black, flake8, mypy)
python scripts/dev.py fix                # Corrige automatiquement le style
python scripts/dev.py clean              # Nettoie les fichiers temporaires
python scripts/dev.py status             # Affiche le statut complet du projet
```

### 🚢 `deploy.py` - Déploiement automatisé
```bash
python scripts/deploy.py check           # Vérifier les prérequis
python scripts/deploy.py local           # Déploiement local simple
python scripts/deploy.py local --optimized # Version optimisée
python scripts/deploy.py docker          # Déploiement Docker (development)
python scripts/deploy.py docker --staging # Environnement staging
python scripts/deploy.py docker --production # Production avec sécurité
python scripts/deploy.py package         # Créer un package ZIP déployable
python scripts/deploy.py stop            # Arrêter tous les déploiements
```

### 🐳 **Docker - Conteneurisation**
```bash
# Méthode 1: Via script deploy.py (RECOMMANDÉ)
python scripts/deploy.py docker          # Mode développement
python scripts/deploy.py docker --production # Mode production

# Méthode 2: Docker-compose direct
cd docker/
docker-compose up -d                     # Lancement en arrière-plan
docker-compose logs -f                   # Voir les logs
docker-compose down                      # Arrêter les conteneurs
```

### Installation manuelle

1. **Installez les dépendances**
   ```bash
   pip install -r requirements/requirements.txt
   ```

2. **Configurez l'environnement**
   ```bash
   cp .env.exemple .env
   # Éditez .env avec vos clés API
   ```

3. **Initialisez la base de données**
   ```bash
   python -c "from src.data.database import init_db; init_db()"
   ```

4. **Lancez l'application**
   ```bash
   python run_app.py
   ```

## 🚀 Utilisation

### 1. Première connexion
- Créez un compte avec un email et un mot de passe sécurisé
- Connectez-vous avec vos identifiants

### 2. Configuration
- Choisissez votre modèle IA préféré
- Les modèles disponibles dépendent des clés API configurées

### 3. Création de campagne
- Donnez un nom à votre campagne
- Sélectionnez les thèmes (Fantasy, Horreur, Sci-Fi, etc.)
- Choisissez la langue (FR/EN)

### 4. Création de personnage
- Définissez nom, classe, race, genre
- Ajoutez une description physique
- Générez un portrait IA (optionnel)

### 5. Jeu
- Interagissez avec le Maître du Jeu IA
- Vos actions et l'historique sont sauvegardés
- Consultez les performances en temps réel

## 📊 Analyse des Performances

L'application enregistre et analyse automatiquement :

- **Latence** : Temps de réponse de chaque modèle
- **Tokens** : Consommation d'entrée et de sortie
- **Coûts** : Estimation basée sur les tarifs actuels
- **Comparaisons** : Graphiques interactifs entre modèles

### Métriques disponibles
- Distribution de latence par modèle
- Évolution temporelle des performances
- Répartition des coûts
- Statistiques d'utilisation

## 🏗️ Architecture

### Structure du Projet (Optimisée)

```
📦 CompareModelPoc/
├── 🎯 run_app.py                # Point d'entrée principal
├── 📁 scripts/                 # Outils développement/déploiement
│   ├── deploy.py               # Déploiement automatisé
│   ├── dev.py                  # Outils développement
│   ├── setup.py                # Installation/configuration
│   └── setup_quick.py          # Configuration express
├── 🐳 docker/                  # Infrastructure Docker
│   ├── Dockerfile              
│   ├── docker-compose.yml
│   ├── DOCKER.md
│   └── nginx/                  # Configuration Nginx
├── 📦 requirements/            # Gestion dépendances
│   ├── requirements.txt        # Production
│   └── dev-requirements.txt    # Développement
├── 📚 docs/                    # Documentation complète
│   ├── README.md               # Guide principal
│   ├── DEPLOYMENT_GUIDE.md     # Guide déploiement
│   ├── TECHNICAL_GUIDE.md      # Documentation technique
│   ├── USER_GUIDE.md           # Guide utilisateur
│   ├── MIGRATION_ROADMAP.md    # Plan migration (historique)
│   └── PROJECT_STATUS.md       # État projet (historique)
└── 🏗️ src/                     # Code applicatif unifié
    ├── 🤖 ai/                  # Intelligence artificielle
    │   ├── chatbot.py          # Interface chat + API (optimisé)
    │   ├── portraits.py        # Génération portraits (optimisé)
    │   ├── api_client.py       # Gestionnaire API centralisé
    │   └── models_config.py    # Configuration modèles
    ├── 🔐 auth/                 # Authentification
    │   └── auth.py             # Système auth complet (optimisé)
    ├── 💾 data/                 # Données et base
    │   ├── database.py         # Gestionnaire BD optimisé
    │   └── models.py           # Modèles données optimisés
    ├── 📊 analytics/            # Analyses et monitoring
    │   ├── performance.py      # Métriques performances
    │   └── system_monitoring.py # Monitoring système
    ├── ⚙️ core/                 # Configuration core
    │   └── config.py           # Configuration centralisée
    └── 🖥️ ui/                   # Interface utilisateur
        ├── app.py              # Application principale (optimisée)
        ├── app_refactored.py   # Version modulaire
        ├── components/         # Composants réutilisables
        │   └── styles.py       # Styles CSS
        └── pages/              # Pages modulaires
            ├── auth_page.py    # Page authentification
            ├── chatbot_page.py # Page chat principal
            ├── dashboard_page.py # Tableau de bord
            ├── performance_page.py # Analyses performances
            └── settings_page.py # Configuration utilisateur
```

### 🔧 Outils et Scripts

Le projet inclut plusieurs scripts d'automatisation dans `scripts/` :

- **setup.py** : Installation complète avec vérifications  
- **setup_quick.py** : Configuration express
- **dev.py** : Outils de développement (run, tests, lint, fix)
- **deploy.py** : Déploiement automatisé (local, Docker)

### Technologies utilisées
- **Frontend** : Streamlit avec Plotly pour les graphiques
- **Backend** : Python avec SQLite
- **IA** : OpenAI GPT-4/4o, Anthropic Claude, DeepSeek
- **Images** : DALL-E 3 pour la génération de portraits
- **Tests** : pytest avec mocks
- **CI/CD** : GitHub Actions

## 🧪 Tests

Exécutez les tests unitaires :

```bash
# Tous les tests
pytest tests/

# Tests spécifiques
pytest tests/test_ia.py -v
pytest tests/test_models.py -v

# Avec couverture
pytest tests/ --cov=. --cov-report=html
```

## 🔧 Configuration Avancée

### Variables d'environnement

| Variable | Description | Requis |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Clé API OpenAI | Oui (pour GPT-4/4o) |
| `ANTHROPIC_API_KEY` | Clé API Anthropic | Optionnel |
| `DEEPSEEK_API_KEY` | Clé API DeepSeek | Optionnel |
| `DATABASE_PATH` | Chemin de la base de données | Non (défaut: database.db) |
| `LOG_LEVEL` | Niveau de logging | Non (défaut: INFO) |

### Personnalisation

Modifiez `config.py` pour :
- Ajouter de nouveaux modèles
- Changer les paramètres de génération
- Personnaliser l'interface utilisateur
- Ajuster les coûts par token

## 🐛 Dépannage

### Problèmes courants

1. **Erreur de clé API**
   ```
   Vérifiez que vos clés API sont correctement configurées dans .env
   ```

2. **Erreur de base de données**
   ```bash
   python -c "from src.data.database import init_db; init_db()"
   ```

3. **Dépendances manquantes**
   ```bash
   pip install -r requirements/requirements.txt
   ```

4. **Tests qui échouent**
   ```bash
   # Réinstaller les dépendances de test
   pip install pytest pytest-cov
   ```

### Logs

Les logs sont affichés dans la console avec le niveau INFO par défaut. 
Changez `LOG_LEVEL=DEBUG` dans `.env` pour plus de détails.

## 🤝 Contribution

1. Fork le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Standards de code
- Utilisez `black` pour le formatage
- Ajoutez des tests pour les nouvelles fonctionnalités
- Documentez les fonctions publiques
- Respectez PEP 8

## 📈 Roadmap

- [ ] Support pour plus de modèles (Llama, Mistral, etc.)
- [ ] Interface de gestion avancée des campagnes
- [ ] Export des conversations en PDF
- [ ] Mode multijoueur
- [ ] Intégration avec des outils de JdR existants
- [ ] Support pour des modèles auto-hébergés
- [ ] Interface mobile optimisée

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [Streamlit](https://streamlit.io/) pour le framework d'interface
- [OpenAI](https://openai.com/) pour GPT-4 et DALL-E
- [Anthropic](https://anthropic.com/) pour Claude
- [Plotly](https://plotly.com/) pour les graphiques interactifs
- La communauté open source Python

## 📞 Support

- 🐛 **Issues** : [GitHub Issues](https://github.com/votre-username/CompareModelPoc/issues)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/votre-username/CompareModelPoc/discussions)
- 📧 **Email** : votre-email@exemple.com

---

**Amusez-vous bien dans vos aventures avec l'IA ! 🎲⚔️🧙‍♂️**
