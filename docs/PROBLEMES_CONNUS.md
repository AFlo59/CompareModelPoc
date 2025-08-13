# ⚠️ Problèmes Connus - DnD AI GameMaster

## 📊 Page Performance

### 🐛 Évolution Temporelle - Graphiques Vides

#### **Symptômes**
- Section "Évolution temporelle" avec 3 onglets :
  - ✅ **Coûts** : Fonctionne correctement
  - ❌ **Tokens** : Graphique vide ou données manquantes
  - ❌ **Latence** : Graphique vide ou données manquantes

#### **Cause Racine**
```python
# Problème dans l'agrégation des données
daily_stats = (
    df.groupby(["date", "model"])
    .agg({"latency": "mean", "cost": "sum", "tokens_in": "sum", "tokens_out": "sum"})
    .reset_index()
)

# Les tokens_in et tokens_out ne s'agrègent pas correctement
# Ou données insuffisantes pour générer des tendances temporelles
```

#### **Impact Utilisateur**
- **🔴 Élevé** : Impossibilité de voir l'évolution des tokens et de la latence
- **🟡 Moyen** : Métriques principales toujours disponibles dans le résumé
- **🟢 Faible** : Fonctionnalités core non affectées

#### **Workarounds Disponibles**

##### 1. Utiliser les Métriques Globales
```bash
# Section "Résumé" affiche correctement :
✅ Requêtes totales
✅ Coût total  
✅ Latence moyenne
✅ Tokens totaux
```

##### 2. Données Détaillées
```bash
# Ouvrir l'expander "📋 Données détaillées"
✅ Voir toutes les requêtes individuelles
✅ Tokens réels par requête
✅ Latence exacte par requête
✅ Export CSV disponible
```

##### 3. Comparaison des Modèles
```bash
# Section "Comparaison des modèles" fonctionne :
✅ Statistiques par modèle
✅ Performance comparative
✅ Distribution des coûts
```

#### **Limitation Tokens (300 max)**

##### **Problème Design**
```python
# Dans les graphiques, limite d'affichage
max_tokens_display = 300

# Mais usage réel souvent plus élevé
typical_usage = 500-1500  # tokens par requête
initialization_usage = 1000+  # tokens à la création campagne
```

##### **Pourquoi c'est Problématique**
1. **Initialisation Campagne** : Souvent 1000+ tokens (contexte, portrait MJ)
2. **Conversations Longues** : Historique accumulated > 300 tokens
3. **Prompts Complexes** : Descriptions détaillées > 300 tokens

##### **Solutions Recommandées**
```python
# Option 1: Augmenter la limite d'affichage
max_tokens_display = 2000  # Plus réaliste

# Option 2: Échelle logarithmique
# Option 3: Grouper par tranches (0-300, 300-1000, 1000+)
```

### 🔧 Solutions Techniques (Pour Développeurs)

#### **Fix Rapide - Tokens Visualization**
```python
# Dans src/analytics/performance.py, ligne ~180
daily_stats["total_tokens"] = daily_stats["tokens_in"] + daily_stats["tokens_out"]

# Ajouter une vérification :
if daily_stats["total_tokens"].sum() > 0:
    fig_tokens_time = px.line(...)
else:
    st.warning("Données tokens insuffisantes pour afficher la tendance")
```

#### **Fix Complet - Agrégation**
```python
# Ajouter debugging dans show_performance_charts()
def show_performance_charts(df: pd.DataFrame) -> None:
    """Affiche des graphiques de performance."""
    if df.empty:
        return
    
    # DEBUG: Vérifier les données avant agrégation
    st.write("Debug - Données avant agrégation:", df.shape)
    st.write("Debug - Colonnes disponibles:", df.columns.tolist())
    
    # ... reste du code
```

## 📈 Métriques de Contournement

### Utilisation Efficace des Données Disponibles

#### **Dashboard Principal**
```bash
# Informations fiables disponibles :
📊 Total des requêtes IA
💰 Coût cumulé par modèle  
⚡ Latence moyenne globale
🎯 Distribution des tokens (données brutes)
```

#### **Export et Analyse Externe**
```bash
# Télécharger les données en CSV
1. Aller dans "📋 Données détaillées"
2. Filtrer par modèle si nécessaire
3. Cliquer "📥 Télécharger en CSV"
4. Analyser dans Excel/Google Sheets/Python
```

#### **Monitoring Manuel**
```bash
# Vérifications périodiques recommandées :
- Coût mensuel total
- Modèle le plus utilisé
- Sessions avec forte consommation
- Tendances d'usage par campagne
```

## 🚀 Améliorations Prévues

### Roadmap Correctifs

#### **Version 1.1 (Court terme)**
- ✅ Correction agrégation données temporelles
- ✅ Augmentation limite affichage tokens (300 → 2000)
- ✅ Messages d'erreur explicites quand données insuffisantes

#### **Version 1.2 (Moyen terme)**  
- 📊 Graphiques adaptatifs (échelle auto)
- 🔍 Zoom temporel (jour/semaine/mois)
- 📱 Interface responsive pour graphiques

#### **Version 2.0 (Long terme)**
- 🎯 Dashboard temps réel
- 📈 Prédictions de coût
- 🔔 Alertes de consommation
- 📊 Analytics avancées par campagne

## 💡 Recommandations Utilisateur

### **Meilleures Pratiques**

#### **Suivi des Coûts**
1. **Vérifier le résumé** après chaque session
2. **Télécharger les données** mensuellement  
3. **Surveiller** les modèles les plus coûteux
4. **Optimiser** en choisissant les modèles adaptés au contexte

#### **Utilisation Efficace**
1. **Conversations courtes** pour réduire les tokens
2. **Descriptions concises** dans les prompts
3. **Modèles moins chers** (DeepSeek) pour tests
4. **GPT-4o/Claude** pour contenus critiques

#### **Monitoring Proactif**
1. **Export hebdomadaire** des données
2. **Analyse tendances** dans tableur externe
3. **Budget mensuel** basé sur historique
4. **Alertes manuelles** si dépassement

---

## 📞 Support

### **Signaler un Problème**
- **GitHub Issues** : [Lien vers le repo]
- **Documentation** : Ce fichier sera mis à jour
- **Logs** : Vérifier `docker logs docker_app_1`

### **Demande d'Amélioration**
- **Priorité élevée** : Problèmes bloquants
- **Priorité moyenne** : Limitations UX
- **Priorité faible** : Améliorations esthétiques

---

**📅 Dernière mise à jour** : 13 août 2025  
**🔄 Version** : 1.0  
**👤 Auteur** : Assistant IA  
**📋 Status** : Document vivant - sera mis à jour avec nouvelles découvertes
