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
- 🔐 **Authentification sécurisée** avec validation des mots de passe
- 🎭 **Création de personnages** avec génération de portraits IA
- 📚 **Gestion de campagnes** multi-thèmes et multi-langues
- 💬 **Interface de chat** immersive avec historique persistant
- 📊 **Analyse de performances** avec graphiques interactifs
- 🎨 **Génération de portraits** via DALL-E 3
- 🌍 **Support multilingue** (FR/EN)

## 🛠️ Installation

### Pré-requis
- Python 3.8 ou supérieur
- Clés API pour les services que vous souhaitez utiliser :
  - OpenAI API Key (pour GPT-4, GPT-4o, DALL-E)
  - Anthropic API Key (pour Claude)
  - DeepSeek API Key (optionnel)

### Installation automatique

1. **Clonez le repository**
   ```bash
   git clone https://github.com/votre-username/CompareModelPoc.git
   cd CompareModelPoc
   ```

2. **Exécutez le script d'installation**
   ```bash
   python setup.py
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
   python run_app.py
   ```

### Installation manuelle

1. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurez l'environnement**
   ```bash
   cp .env.exemple .env
   # Éditez .env avec vos clés API
   ```

3. **Initialisez la base de données**
   ```bash
   python -c "from database import init_db; init_db()"
   ```

4. **Lancez l'application**
   ```bash
   streamlit run app.py
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

```
CompareModelPoc/
├── app.py              # Application principale Streamlit
├── auth.py             # Gestion de l'authentification
├── chatbot.py          # Interface de chat et gestion des modèles
├── config.py           # Configuration centralisée
├── database.py         # Gestion de la base de données SQLite
├── models.py           # Modèles de données et requêtes
├── performance.py      # Analyse et visualisation des performances
├── portraits.py        # Génération de portraits IA
├── run_app.py          # Script de lancement avec vérifications
├── setup.py            # Script d'installation automatique
├── requirements.txt    # Dépendances Python
├── .env.exemple        # Template de configuration
├── tests/              # Tests unitaires
│   ├── test_app.py
│   ├── test_ia.py
│   └── test_models.py
└── .github/workflows/  # CI/CD GitHub Actions
    └── ci-develop.yml
```

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
   python -c "from database import init_db; init_db()"
   ```

3. **Dépendances manquantes**
   ```bash
   pip install -r requirements.txt
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
