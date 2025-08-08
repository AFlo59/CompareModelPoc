# 🚀 Roadmap de Migration - Optimisation du Projet

## 📊 État Actuel Analysé

### ✅ **Itération 1 Terminée** - Structure reorganisée 
- `scripts/` → Scripts développement/déploiement  
- `docker/` → Fichiers Docker + nginx
- `requirements/` → Fichiers dépendances
- Tests corrigés → `ModelCache` import fixé

### 🔍 **Problèmes Identifiés**

#### 1. **Doublons de Code** 
| Fichier Basique | Fichier Optimisé | Status | Action |
|----------------|------------------|--------|--------|
| `auth.py` | `auth_optimized.py` | ✅ **Optimisé > Basique** | Remplacer |
| `chatbot.py` | `chatbot_optimized.py` | ✅ **Optimisé > Basique** | Remplacer |  
| `models.py` | `models_optimized.py` | ✅ **Optimisé > Basique** | Remplacer |
| `database.py` | `database_optimized.py` | ✅ **Optimisé > Basique** | Remplacer |
| `portraits.py` | `portraits_optimized.py` | ✅ **Optimisé > Basique** | Remplacer |
| `app.py` | `app_refactored.py` | 🔄 **Refactored incomplet** | Finaliser |

#### 2. **Architecture Incohérente**
- **Point d'entrée :** `run_app.py` utilise les versions basiques
- **Tests :** Mélange basiques/optimisées  
- **Pages refactorisées :** Incomplètes (manque campaign, character, etc.)

## 🎯 **Plan de Migration - Itération 2**

### **Phase A : Migration Backend (Safe)**
1. **Backup automatique** → Renommer `.py` → `_legacy.py`
2. **Promotion optimisées** → Renommer `_optimized.py` → `.py`  
3. **Test validation** → Vérifier que tout fonctionne

### **Phase B : Migration Frontend** 
1. **Finaliser app_refactored.py** → Ajouter pages manquantes
2. **Mise à jour point d'entrée** → Rediriger vers version refactorisée
3. **Nettoyage final** → Supprimer fichiers legacy

### **Phase C : Tests & Documentation**
1. **Correction tests** → Adapter aux nouvelles versions
2. **Mise à jour docs** → Refléter nouvelle architecture  
3. **Validation complète** → Tests CI/CD

## 🛠️ **Commandes de Migration Suggérées**

### Option 1 : Migration Manuelle Sécurisée
```bash
# Backup des versions actuelles
cd src/auth && cp auth.py auth_legacy.py
cd ../ai && cp chatbot.py chatbot_legacy.py
cd ../data && cp models.py models_legacy.py

# Promotion des versions optimisées  
cd src/auth && cp auth_optimized.py auth.py
cd ../ai && cp chatbot_optimized.py chatbot.py
cd ../data && cp models_optimized.py models.py
```

### Option 2 : Script Automatisé
```bash
# Utiliser le script de migration (à créer)
python scripts/migrate_to_optimized.py --backup --validate
```

## 📈 **Bénéfices Attendus**

### **Performance**
- ⚡ **Base de données :** WAL mode, cache optimisé, pooling
- 🔄 **API :** Retry automatique, timeout, gestion d'erreurs  
- 💾 **Cache :** Mise en cache des requêtes fréquentes

### **Sécurité**  
- 🛡️ **Auth :** Protection force brute, session timeout
- 🔐 **Validation :** Email/password renforcée
- 📊 **Monitoring :** Logs détaillés, tracking tentatives

### **UX Améliorée**
- 💰 **Coûts :** Calcul temps réel, métriques performance
- 🎯 **Interface :** Messages erreur clairs, loading states
- 📱 **Responsive :** Architecture modulaire, pages séparées

## ⚠️ **Risques & Mitigation**

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|---------|------------|
| Tests cassés | 🟡 Moyen | 🟡 Moyen | Backup + tests unitaires |
| Import cassés | 🟢 Faible | 🔴 Élevé | Validation imports + rollback |
| Régression UX | 🟢 Faible | 🟡 Moyen | Tests fonctionnels manuels |

## 🎯 **Prochaines Étapes**

1. **Validation utilisateur** → Approbation plan migration
2. **Création script backup** → Sécurisation automatique  
3. **Migration pilote** → Test sur module auth
4. **Extension complète** → Migration tous modules
5. **Validation finale** → Tests + documentation

---

## 🔄 Schéma Base de Données – Version 4

- Ajout de la colonne `ai_model` à la table `campaigns`
- Migration idempotente: si la colonne existe déjà, aucun changement
- Le chemin DB suit la priorité: `DATABASE_PATH` (env) → `DatabaseConfig.DB_PATH` (tests) → `DB_PATH` (module) → `database.db`

## 🐳 Docker – Notes de déploiement

- Le conteneur crée `/app/data` et `/app/logs` et lance l’app en root par défaut pour éviter les erreurs de permissions sur volumes bindés
- Compose utilise un nom de projet stable: `comparemodelpoc_<environnement>` et `--remove-orphans` pour éviter les conflits au rebuild
- Variables requises: `DATABASE_PATH=/app/data/database.db`, API keys (optionnelles)

## ✅ État

**Statut :** 🟢 Stable (itération en cours)
**Dernière mise à jour :** automatique
