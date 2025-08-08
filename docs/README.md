# 🎲 DnD AI GameMaster - Documentation

## 📋 Table des matières

- [🏗️ Architecture & Structure](#-architecture--structure)
- [🚀 Guide de Démarrage](#-guide-de-démarrage)  
- [🧪 Tests & Qualité](#-tests--qualité)
- [🚢 Déploiement](#-déploiement)
- [🔧 Maintenance & Support](#-maintenance--support)

---

## 🎯 Vue d'ensemble

**DnD AI GameMaster** est une application Streamlit optimisée qui permet de comparer les performances de différents modèles IA (GPT-4, Claude, DeepSeek) dans le contexte d'un jeu de rôle Donjons & Dragons.

### ✨ Fonctionnalités principales

- 🤖 **4 modèles IA supportés** : GPT-4, GPT-4o, Claude 3.5 Sonnet, DeepSeek
- 🎭 **Génération de portraits** avec DALL-E 3
- 📊 **Analytics en temps réel** : performance, coûts, métriques
- 🔐 **Authentification sécurisée** avec protection anti force brute
- 🏰 **Gestion multi-campagnes** avec persistance des données
- 📈 **Monitoring système** intégré

### 📊 Statistiques projet

| Métrique | Valeur |
|----------|--------|
| **Lignes de code** | ~4,500+ lignes |
| **Tests automatisés** | 158 tests |
| **Couverture de code** | 80%+ |
| **Modules principaux** | 15 modules |
| **Structure** | Architecture src/ modulaire |

---

## 🏗️ Architecture & Structure

### Structure du projet optimisée

```
CompareModelPoc/
├── 📦 src/                     # Code source principal
│   ├── 🖥️ ui/                  # Interface utilisateur
│   │   ├── components/         # Composants réutilisables
│   │   │   └── styles.py      # Styles CSS & configuration
│   │   ├── pages/             # Pages de l'application
│   │   │   ├── auth_page.py   # Authentification
│   │   │   ├── dashboard_page.py # Tableau de bord
│   │   │   ├── chatbot_page.py   # Interface de chat
│   │   │   ├── performance_page.py # Analytics
│   │   │   └── settings_page.py   # Paramètres
│   │   ├── app.py             # Application principale (legacy)
│   │   └── app_refactored.py  # Application refactorisée
│   │
│   ├── 🔐 auth/               # Authentification & sécurité
│   │   ├── auth.py           # Système d'auth (legacy)
│   │   └── auth_optimized.py # Auth optimisé avec sécurité renforcée
│   │
│   ├── 🤖 ai/                 # Intelligence artificielle
│   │   ├── api_client.py     # Gestionnaire API centralisé
│   │   ├── models_config.py  # Configuration des modèles IA
│   │   ├── chatbot.py        # Chatbot principal (legacy)
│   │   ├── chatbot_optimized.py # Chatbot optimisé
│   │   ├── portraits.py      # Génération portraits (legacy)
│   │   └── portraits_optimized.py # Portraits optimisés
│   │
│   ├── 💾 data/               # Données & persistance
│   │   ├── database.py       # Gestionnaire DB (legacy)
│   │   ├── database_optimized.py # DB optimisée (index, cache)
│   │   ├── models.py         # Modèles de données (legacy)
│   │   └── models_optimized.py   # Modèles optimisés
│   │
│   ├── 📊 analytics/          # Analytics & monitoring
│   │   ├── performance.py    # Métriques de performance
│   │   └── system_monitoring.py # Monitoring système
│   │
│   └── ⚙️ core/               # Configuration centrale
│       └── config.py         # Configuration globale
│
├── 🧪 tests/                  # Suite de tests (158 tests)
│   ├── test_*.py             # Tests unitaires et d'intégration
│   └── conftest.py           # Configuration pytest
│
├── 📚 docs/                   # Documentation
├── 🐳 docker/                 # Configuration Docker
├── 🔧 .github/workflows/      # CI/CD GitHub Actions
└── 📄 Configuration files     # pyproject.toml, requirements.txt, etc.
```

### 🔄 Modules legacy vs optimisés

Le projet maintient les **deux versions** pour assurer la compatibilité :

| Module | Legacy | Optimisé | État |
|--------|--------|----------|------|
| **App principal** | `app.py` | `app_refactored.py` | ✅ Refactorisé |
| **Authentification** | `auth.py` | `auth_optimized.py` | ✅ Sécurisé |
| **Chatbot** | `chatbot.py` | `chatbot_optimized.py` | ✅ Performant |
| **Base de données** | `database.py` | `database_optimized.py` | ✅ Indexé |
| **Modèles** | `models.py` | `models_optimized.py` | ✅ Mis en cache |
| **Portraits** | `portraits.py` | `portraits_optimized.py` | ✅ Robuste |

---

## 🚀 Guide de Démarrage

### Prérequis

- **Python 3.10+**
- **Clés API** : OpenAI, Anthropic (optionnel : DeepSeek)
- **Git** pour cloner le projet

### Installation rapide

```bash
# 1. Cloner le projet
git clone <votre-repo>
cd CompareModelPoc

# 2. Créer environnement virtuel
python -m venv venv

# 3. Activer l'environnement
# Windows :
venv\\Scripts\\activate
# Linux/Mac :
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Configuration des clés API
# Créer .env avec :
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key  # optionnel

# 6. Lancer l'application
python run_app.py
# OU directement :
streamlit run src/ui/app.py
```

### 🔧 Configuration

Le fichier `src/core/config.py` centralise toute la configuration :

- **Modèles IA** : Paramètres, coûts, limites de tokens
- **Base de données** : Configuration SQLite optimisée
- **Sécurité** : Paramètres d'authentification
- **Interface** : Thèmes, styles, layouts

---

## 🧪 Tests & Qualité

### Suite de tests complète

**158 tests automatisés** couvrant :

- ✅ **Tests unitaires** : Chaque module individuellement
- ✅ **Tests d'intégration** : Communication entre modules  
- ✅ **Tests d'interface** : Composants UI et pages
- ✅ **Tests de configuration** : Structure projet et imports
- ✅ **Tests de sécurité** : Authentification et validation

### Exécution des tests

```bash
# Tests complets avec couverture
pytest tests/ --cov=src --cov-report=html

# Tests rapides
pytest tests/ -v

# Tests spécifiques
pytest tests/test_auth_optimized.py -v
```

### Outils de qualité

- **Black** : Formatage de code
- **isort** : Organisation des imports  
- **flake8** : Linting et vérifications
- **mypy** : Vérification des types

```bash
# Vérification complète
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

---

## 🚢 Déploiement

Voir le [Guide de Déploiement détaillé](DEPLOYMENT_GUIDE.md) pour :

- 🐳 **Docker** : Configuration containers
- ☁️ **Cloud** : AWS, GCP, Azure  
- 🔧 **Production** : Variables d'environnement, monitoring
- 📊 **Scaling** : Performance et optimisations

---

## 🔧 Maintenance & Support

### Structure de support

1. **Issues GitHub** : Bugs et demandes de fonctionnalités
2. **Documentation** : Cette documentation complète
3. **Tests automatisés** : Détection précoce des régressions
4. **Monitoring** : Tableau de bord système intégré

### Contribution

1. Fork du projet
2. Créer une branche feature
3. Tests passants + couverture 80%+
4. Pull request avec description détaillée

### Monitoring en production

L'application inclut un **monitoring système** complet :

- 📊 **Métriques temps réel** : CPU, mémoire, disque, réseau
- 💰 **Suivi des coûts** : API calls et estimations
- ⚡ **Performance** : Latence des modèles IA
- 🔍 **Logs structurés** : Debug et troubleshooting

---

## 📞 Contact & Support

- **GitHub** : Issues et discussions
- **Documentation** : Cette documentation complète
- **Tests** : 158 tests automatisés pour la stabilité

---

*Dernière mise à jour : Décembre 2024*  
*Version : 2.0.0*
