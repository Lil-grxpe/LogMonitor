# Guide d'Utilisation des Fichiers de Test LogMonitor

## 🎯 Objectif

Ce guide explique comment utiliser les 6 fichiers de logs de test pour valider le bon fonctionnement de LogMonitor.

## 📁 Structure des Fichiers

```
tests/test_logs/
├── 01_bruteforce_ssh.log              # 30 lignes - Bruteforce SSH
├── 02_multiple_accounts_attack.log    # 30 lignes - Attaque multi-comptes
├── 03_suspicious_root_login.log       # 30 lignes - Connexions root suspectes
├── 04_sensitive_file_modification.log # 29 lignes - Modifications fichiers sensibles
├── 05_activity_spike.log              # 60 lignes - Pic d'activité
├── 06_normal_activity.log             # 41 lignes - Activité normale
├── README.md                          # Documentation détaillée
├── test_all_logs.sh                   # Script de test automatique
└── USAGE.md                           # Ce fichier
```

## 🚀 Démarrage Rapide

### 1. Prérequis

```bash
# Se placer dans le répertoire du projet
cd /home/lil_grxpe/Bureau/Projet_tuteuré

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier l'installation
logmonitor --version
```

### 2. Test Automatique (Recommandé)

```bash
# Exécuter le script de test
./tests/test_logs/test_all_logs.sh
```

Ce script va :
- ✅ Vérifier l'environnement
- ✅ Scanner les 6 fichiers de test
- ✅ Afficher un rapport détaillé
- ✅ Lister les alertes générées

### 3. Tests Manuels Individuels

#### Test 1 : Bruteforce SSH
```bash
logmonitor scan tests/test_logs/01_bruteforce_ssh.log
```
**Résultat attendu :** Détection de multiples tentatives de bruteforce depuis 2 IPs différentes

#### Test 2 : Attaque Multi-Comptes
```bash
logmonitor scan tests/test_logs/02_multiple_accounts_attack.log
```
**Résultat attendu :** Détection d'une attaque ciblant 15+ comptes depuis une seule IP

#### Test 3 : Connexions Root Suspectes
```bash
logmonitor scan tests/test_logs/03_suspicious_root_login.log
```
**Résultat attendu :** Détection de 15 connexions root depuis des IPs non autorisées

#### Test 4 : Modifications de Fichiers Sensibles
```bash
logmonitor scan tests/test_logs/04_sensitive_file_modification.log
```
**Résultat attendu :** Détection de modifications sur /etc/passwd, /etc/shadow, /etc/sudoers, /etc/ssh/sshd_config

#### Test 5 : Pic d'Activité
```bash
logmonitor scan tests/test_logs/05_activity_spike.log
```
**Résultat attendu :** Détection d'un pic d'activité (40 événements en 1 minute vs 2 normalement)

#### Test 6 : Activité Normale
```bash
logmonitor scan tests/test_logs/06_normal_activity.log
```
**Résultat attendu :** AUCUNE alerte (validation qu'il n'y a pas de faux positifs)

## 📊 Visualisation des Résultats

### Lister toutes les alertes
```bash
logmonitor alerts list
```

### Filtrer par sévérité
```bash
# Alertes critiques uniquement
logmonitor alerts list --severity critical

# Alertes high uniquement
logmonitor alerts list --severity high

# Alertes medium uniquement
logmonitor alerts list --severity medium
```

### Générer un rapport PDF
```bash
# Scanner tous les fichiers
for log in tests/test_logs/0*.log; do
    logmonitor scan "$log"
done

# Générer le rapport
logmonitor report generate --format pdf
```

Le rapport sera disponible dans `reports/`

### Générer un rapport CSV
```bash
logmonitor report generate --format csv
```

## 🧪 Tests Unitaires Python

Pour tester les règles de détection avec pytest :

```bash
# Tous les tests
pytest tests/ -v

# Tests de détection uniquement
pytest tests/test_detector.py -v

# Avec couverture de code
pytest tests/ --cov=logmonitor.core.rules --cov-report=html
```

## 📈 Dashboard Web

Pour visualiser les alertes dans le dashboard web :

```bash
# Lancer le dashboard
logmonitor web --port 5000

# Ouvrir dans le navigateur
# http://localhost:5000
```

## 🔍 Analyse Détaillée

### Vérifier le parsing des logs

```bash
# Afficher les événements normalisés (si option disponible)
logmonitor scan tests/test_logs/01_bruteforce_ssh.log --verbose
```

### Inspecter la base de données

```bash
# Si SQLite est utilisé
sqlite3 data/logmonitor.db "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10;"
```

## 📋 Checklist de Validation

Utilisez cette checklist pour valider que LogMonitor fonctionne correctement :

- [ ] **Test 1** : Bruteforce SSH détecté (sévérité HIGH)
- [ ] **Test 2** : Attaque multi-comptes détectée (sévérité MEDIUM)
- [ ] **Test 3** : Connexions root suspectes détectées (sévérité HIGH)
- [ ] **Test 4** : Modifications fichiers sensibles détectées (sévérité CRITICAL)
- [ ] **Test 5** : Pic d'activité détecté (sévérité MEDIUM)
- [ ] **Test 6** : Aucune fausse alerte sur activité normale
- [ ] Les alertes contiennent des preuves (IPs, utilisateurs, compteurs)
- [ ] Les rapports PDF/CSV se génèrent correctement
- [ ] Le dashboard web affiche les alertes
- [ ] La base de données stocke les alertes

## 🐛 Dépannage

### Problème : "Permission denied" lors du scan
```bash
# Ajouter l'utilisateur au groupe adm
sudo usermod -a -G adm $USER
newgrp adm
```

### Problème : "logmonitor: command not found"
```bash
# Réinstaller en mode développement
pip install -e .
```

### Problème : Aucune alerte générée
```bash
# Vérifier la configuration
logmonitor config validate

# Vérifier que les règles sont activées
cat config/logmonitor.yaml
```

### Problème : Trop de fausses alertes sur le fichier normal
```bash
# Ajuster les seuils dans config/logmonitor.yaml
# Exemple : augmenter le threshold de bruteforce_ssh de 5 à 10
```

## 📚 Documentation Complémentaire

- **README.md** : Documentation détaillée de chaque fichier de test
- **../README.md** : Documentation générale du projet
- **../../docs/** : Documentation technique complète

## 💡 Conseils

1. **Commencez par le test automatique** (`test_all_logs.sh`) pour une vue d'ensemble
2. **Testez individuellement** chaque fichier pour comprendre chaque règle
3. **Vérifiez le fichier 06** en dernier pour valider l'absence de faux positifs
4. **Utilisez le dashboard web** pour une visualisation interactive
5. **Générez des rapports** pour documenter vos tests

## 🎓 Scénarios Pédagogiques

### Démonstration pour une présentation
```bash
# 1. Montrer une attaque en direct
logmonitor scan tests/test_logs/01_bruteforce_ssh.log

# 2. Afficher les alertes
logmonitor alerts list --severity high

# 3. Générer un rapport visuel
logmonitor report generate --format pdf

# 4. Ouvrir le dashboard
logmonitor web
```

### Test de performance
```bash
# Scanner tous les fichiers en boucle
time for i in {1..10}; do
    for log in tests/test_logs/0*.log; do
        logmonitor scan "$log" > /dev/null
    done
done
```

### Validation de la couverture de code
```bash
# Exécuter les tests avec couverture
pytest tests/ --cov=logmonitor --cov-report=html

# Ouvrir le rapport
firefox htmlcov/index.html
```

---

**Dernière mise à jour :** 2026-01-02  
**Version :** 1.0  
**Auteur :** Équipe LogMonitor
