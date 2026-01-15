# 📦 Fichiers de Logs de Test - Récapitulatif Final

## ✅ Ce qui a été créé

### 🎯 6 Fichiers de Logs de Test

Tous les fichiers sont dans `tests/test_logs/` :

| # | Fichier | Lignes | Règle Testée | Alertes Attendues |
|---|---------|--------|--------------|-------------------|
| 1 | `01_bruteforce_ssh.log` | 30 | BruteForce SSH | ✅ Multiples |
| 2 | `02_multiple_accounts_attack.log` | 30 | Multiple Accounts Attack | ✅ 1+ |
| 3 | `03_suspicious_root_login.log` | 30 | Suspicious Root Login | ✅ 15 |
| 4 | `04_sensitive_file_modification.log` | 29 | Sensitive File Modification | ✅ Multiples |
| 5 | `05_activity_spike.log` | 60 | Activity Spike | ✅ 1+ |
| 6 | `06_normal_activity.log` | 41 | Aucune (test faux positifs) | ❌ Aucune |

**Total : 220 lignes de logs de test**

---

## 📚 Documentation Créée

### 1. `README.md` - Documentation détaillée
- Description de chaque fichier de test
- Scénarios d'attaque simulés
- Alertes attendues
- Résumé des règles de détection

### 2. `USAGE.md` - Guide d'utilisation
- Démarrage rapide
- Tests manuels et automatiques
- Commandes pour générer des rapports
- Checklist de validation
- Dépannage

### 3. `test_all_logs.sh` - Script de test automatique
- Teste les 6 fichiers automatiquement
- Affiche un rapport coloré
- Vérifie l'environnement
- Compte les réussites/échecs

### 4. `/docs/kali_linux_guide.md` - Guide Kali Linux
- Adaptation pour systemd journal
- Export des logs SSH/sudo
- Configuration spécifique Kali
- Workflow recommandé

---

## 🚀 Utilisation Rapide

### Test Automatique (Recommandé)

```bash
cd /home/lil_grxpe/Bureau/Projet_tuteuré
source venv/bin/activate
./tests/test_logs/test_all_logs.sh
```

### Tests Manuels Individuels

```bash
# Test 1 : Bruteforce SSH
logmonitor scan tests/test_logs/01_bruteforce_ssh.log

# Test 2 : Attaque multi-comptes
logmonitor scan tests/test_logs/02_multiple_accounts_attack.log

# Test 3 : Connexions root suspectes
logmonitor scan tests/test_logs/03_suspicious_root_login.log

# Test 4 : Modifications fichiers sensibles
logmonitor scan tests/test_logs/04_sensitive_file_modification.log

# Test 5 : Pic d'activité
logmonitor scan tests/test_logs/05_activity_spike.log

# Test 6 : Activité normale (pas d'alertes)
logmonitor scan tests/test_logs/06_normal_activity.log
```

### Voir les Résultats

```bash
# Lister toutes les alertes
logmonitor alerts list

# Filtrer par sévérité
logmonitor alerts list --severity critical
logmonitor alerts list --severity high

# Dashboard web
logmonitor web --port 5000
# Ouvrir http://localhost:5000

# Générer un rapport PDF
logmonitor report generate --format pdf
```

---

## 📊 Règles de Détection Testées

### Règle 1 : BruteForce SSH
- **Seuil** : 5 échecs en 300 secondes
- **Sévérité** : High
- **Fichier** : `01_bruteforce_ssh.log`
- **Test** : 30 tentatives depuis 2 IPs différentes

### Règle 2 : Multiple Accounts Attack
- **Seuil** : 3 comptes en 600 secondes
- **Sévérité** : Medium
- **Fichier** : `02_multiple_accounts_attack.log`
- **Test** : 15+ comptes ciblés depuis 1 IP

### Règle 3 : Suspicious Root Login
- **Seuil** : IP non autorisée
- **Sévérité** : High
- **Fichier** : `03_suspicious_root_login.log`
- **Test** : 15 connexions root depuis IPs externes

### Règle 4 : Sensitive File Modification
- **Seuil** : Modification détectée
- **Sévérité** : Critical
- **Fichier** : `04_sensitive_file_modification.log`
- **Test** : Modifications de /etc/passwd, /etc/shadow, /etc/sudoers, /etc/ssh/sshd_config

### Règle 5 : Activity Spike
- **Seuil** : 3x la baseline
- **Sévérité** : Medium
- **Fichier** : `05_activity_spike.log`
- **Test** : 40 événements en 1 minute vs 2 normalement

### Test 6 : Activité Normale
- **Objectif** : Pas de faux positifs
- **Fichier** : `06_normal_activity.log`
- **Test** : Activité légitime (connexions SSH normales, sudo, cron)

---

## 🎓 Utilisation pour Kali Linux

Sur Kali, les logs ne sont pas dans `/var/log/auth.log` mais dans systemd journal.

### Export des logs systemd

```bash
# Utiliser le script fourni
./scripts/export_systemd_logs.sh /tmp/kali_logs "24 hours ago"

# Analyser les logs exportés
logmonitor scan /tmp/kali_logs/ssh.log
logmonitor scan /tmp/kali_logs/sudo.log
```

### Export manuel

```bash
# SSH
journalctl -u ssh --since "7 days ago" --no-pager > /tmp/ssh.log
logmonitor scan /tmp/ssh.log

# Sudo
journalctl -t sudo --since "7 days ago" --no-pager > /tmp/sudo.log
logmonitor scan /tmp/sudo.log
```

---

## ✅ Checklist de Validation

- [ ] Les 6 fichiers de test sont créés
- [ ] Le script `test_all_logs.sh` fonctionne
- [ ] Bruteforce SSH détecté (fichier 01)
- [ ] Attaque multi-comptes détectée (fichier 02)
- [ ] Connexions root suspectes détectées (fichier 03)
- [ ] Modifications fichiers sensibles détectées (fichier 04)
- [ ] Pic d'activité détecté (fichier 05)
- [ ] Aucune fausse alerte sur activité normale (fichier 06)
- [ ] Dashboard web affiche les alertes
- [ ] Rapports PDF/CSV se génèrent
- [ ] Export systemd fonctionne sur Kali

---

## 📁 Structure des Fichiers

```
tests/test_logs/
├── 01_bruteforce_ssh.log              # 30 lignes - Bruteforce
├── 02_multiple_accounts_attack.log    # 30 lignes - Multi-comptes
├── 03_suspicious_root_login.log       # 30 lignes - Root suspect
├── 04_sensitive_file_modification.log # 29 lignes - Fichiers sensibles
├── 05_activity_spike.log              # 60 lignes - Pic d'activité
├── 06_normal_activity.log             # 41 lignes - Activité normale
├── README.md                          # Documentation détaillée
├── USAGE.md                           # Guide d'utilisation
├── SUMMARY.md                         # Ce fichier
└── test_all_logs.sh                   # Script de test automatique

docs/
└── kali_linux_guide.md                # Guide spécifique Kali

scripts/
└── export_systemd_logs.sh             # Export logs systemd
```

---

## 🎯 Objectifs Atteints

✅ **6 fichiers de logs de test** couvrant tous les cas malveillants  
✅ **Documentation complète** (README, USAGE, Guide Kali)  
✅ **Script de test automatique** pour validation rapide  
✅ **Support Kali Linux** avec export systemd journal  
✅ **Exemples réalistes** basés sur de vraies attaques  
✅ **Test de faux positifs** avec activité normale  

---

## 💡 Prochaines Étapes

1. **Tester** : Exécuter `./tests/test_logs/test_all_logs.sh`
2. **Valider** : Vérifier que les 5 règles détectent correctement
3. **Dashboard** : Lancer `logmonitor web` pour visualiser
4. **Rapports** : Générer un PDF avec `logmonitor report generate`
5. **Kali** : Tester l'export systemd avec le script fourni

---

**Créé le** : 2026-01-02  
**Auteur** : Équipe LogMonitor  
**Version** : 1.0  
**Statut** : ✅ Complet et prêt à l'emploi
