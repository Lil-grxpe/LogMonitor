# Fichiers de Logs de Test - LogMonitor

Ce répertoire contient 6 fichiers de logs de test pour valider les règles de détection de LogMonitor.

## 📋 Liste des Fichiers de Test

### 1️⃣ `01_bruteforce_ssh.log` - Bruteforce SSH
**Règle testée :** BruteForce SSH (Règle 1)  
**Sévérité :** High  
**Description :** Simule des attaques par force brute SSH avec de multiples tentatives de connexion échouées depuis plusieurs adresses IP.

**Scénarios inclus :**
- 30 tentatives échouées depuis `192.168.1.100` (admin, test, guest, root, ubuntu)
- 10 tentatives échouées depuis `45.76.123.45` (admin, root)
- Dépassement du seuil de 5 tentatives en 300 secondes

**Alertes attendues :** ✅ Multiples alertes de bruteforce détectées

---

### 2️⃣ `02_multiple_accounts_attack.log` - Attaque sur Plusieurs Comptes
**Règle testée :** Multiple Accounts Attack (Règle 2)  
**Sévérité :** Medium  
**Description :** Simule une attaque ciblant plusieurs comptes utilisateurs depuis une seule adresse IP.

**Scénarios inclus :**
- 30 tentatives échouées depuis `203.0.113.50`
- Ciblage de 15+ comptes différents (alice, bob, charlie, david, eve, frank, grace, henry, admin, administrator, test, guest, root, ubuntu, debian, centos, oracle, mysql, postgres)
- Dépassement du seuil de 3 comptes en 600 secondes

**Alertes attendues :** ✅ Alerte d'attaque sur plusieurs comptes

---

### 3️⃣ `03_suspicious_root_login.log` - Connexions Root Suspectes
**Règle testée :** Suspicious Root Login (Règle 3)  
**Sévérité :** High  
**Description :** Simule des connexions root réussies depuis des adresses IP non autorisées.

**Scénarios inclus :**
- Connexions normales d'utilisateurs réguliers depuis `10.0.0.x` (autorisées)
- 15 connexions root depuis des IPs externes suspectes :
  - `198.51.100.75`
  - `185.220.101.45`
  - `91.198.174.192`
  - `103.253.145.28`
  - `212.102.63.194`
  - `45.142.120.10`
  - `159.89.49.60`
  - `167.99.83.205`
  - `134.209.24.42`
  - `178.128.91.15`
  - `206.189.156.89`
  - `188.166.77.33`
  - `142.93.128.200`
  - `157.230.44.166`

**Alertes attendues :** ✅ 15 alertes de connexion root suspecte

---

### 4️⃣ `04_sensitive_file_modification.log` - Modification de Fichiers Sensibles
**Règle testée :** Sensitive File Modification (Règle 4)  
**Sévérité :** Critical  
**Description :** Simule des modifications de fichiers système critiques.

**Scénarios inclus :**
- Modifications de `/etc/passwd` (création/modification d'utilisateurs)
- Modifications de `/etc/shadow` (mots de passe)
- Modifications de `/etc/sudoers` (privilèges sudo)
- Modifications de `/etc/ssh/sshd_config` (configuration SSH)
- Utilisateurs suspects : admin, hacker, suspicious, attacker, malicious, badactor, intruder, compromised, backdoor

**Alertes attendues :** ✅ Multiples alertes critiques de modification de fichiers sensibles

---

### 5️⃣ `05_activity_spike.log` - Pic d'Activité Inhabituel
**Règle testée :** Activity Spike (Règle 5)  
**Sévérité :** Medium  
**Description :** Simule un pic soudain d'activité système.

**Scénarios inclus :**
- Activité normale : 2 événements par minute pendant 10 minutes
- Pic soudain : 40 événements en 1 minute (à 11:10)
- Ratio : 20x la moyenne normale
- Dépassement du seuil de 3x la baseline

**Alertes attendues :** ✅ Alerte de pic d'activité

---

### 6️⃣ `06_normal_activity.log` - Activité Normale
**Règle testée :** Aucune (test de faux positifs)  
**Sévérité :** N/A  
**Description :** Simule une activité système normale et légitime.

**Scénarios inclus :**
- Connexions SSH légitimes avec clés publiques
- Commandes sudo normales (apt update, systemctl, tail, docker, journalctl)
- Déconnexions normales
- Tâches cron planifiées
- Activité réseau normale (nginx, postfix)
- Logs système standards

**Alertes attendues :** ❌ Aucune alerte (pas de faux positifs)

---

## 🧪 Utilisation des Fichiers de Test

### Test Manuel
```bash
# Tester chaque fichier individuellement
logmonitor scan -f tests/test_logs/01_bruteforce_ssh.log
logmonitor scan tests/test_logs/02_multiple_accounts_attack.log
logmonitor scan tests/test_logs/03_suspicious_root_login.log
logmonitor scan tests/test_logs/04_sensitive_file_modification.log
logmonitor scan tests/test_logs/05_activity_spike.log
logmonitor scan tests/test_logs/06_normal_activity.log

# Voir les alertes générées
logmonitor alerts list
logmonitor alerts list --severity high
logmonitor alerts list --severity critical
```

### Test Automatisé
```bash
# Exécuter tous les tests
pytest tests/test_detection.py -v

# Avec couverture
pytest tests/test_detection.py --cov=logmonitor.core.rules
```

### Générer un Rapport
```bash
# Scanner tous les fichiers et générer un rapport
for log in tests/test_logs/*.log; do
    logmonitor scan "$log"
done

# Générer le rapport PDF
logmonitor report generate --format pdf

# Générer le rapport CSV
logmonitor report generate --format csv
```

---

## 📊 Résumé des Règles de Détection

| # | Règle | Sévérité | Fichier de Test | Seuil |
|---|-------|----------|-----------------|-------|
| 1 | BruteForce SSH | High | `01_bruteforce_ssh.log` | 5 échecs / 300s |
| 2 | Multiple Accounts Attack | Medium | `02_multiple_accounts_attack.log` | 3 comptes / 600s |
| 3 | Suspicious Root Login | High | `03_suspicious_root_login.log` | IP non autorisée |
| 4 | Sensitive File Modification | Critical | `04_sensitive_file_modification.log` | Fichiers sensibles |
| 5 | Activity Spike | Medium | `05_activity_spike.log` | 3x baseline |
| - | Normal Activity | - | `06_normal_activity.log` | Aucune alerte |

---

## ✅ Validation

Pour valider que LogMonitor fonctionne correctement :

1. **Aucune fausse alerte** sur `06_normal_activity.log`
2. **Détection correcte** des 5 types d'attaques
3. **Sévérité appropriée** pour chaque alerte
4. **Preuves complètes** dans les alertes (IP, utilisateurs, compteurs)

---

## 📝 Notes

- Les timestamps utilisent le format syslog standard
- Les adresses IP sont fictives ou réservées (RFC 5737, RFC 1918)
- Les noms d'utilisateurs sont génériques
- Les fichiers peuvent être utilisés pour des démonstrations ou des tests de performance

**Créé le :** 2026-01-02  
**Auteur :** Équipe LogMonitor  
**Version :** 1.0
