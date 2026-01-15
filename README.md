# LogMonitor 🛡️

**Outil de surveillance et d'analyse de logs pour systèmes Linux**

![License](https://img.shields.io/badge/license-Academic-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-Stable-green)

## 📋 Description

**LogMonitor** est une solution de sécurité légère et performante conçue pour surveiller, analyser et visualiser les journaux systèmes (logs) Linux. Elle permet de détecter automatiquement les tentatives d'intrusion (Bruteforce SSH, accès Root, etc.) sans la complexité d'un SIEM.

Idéal pour les administrateurs systèmes et les équipes de sécurité souhaitant une visibilité rapide et claire sur l'état de leurs serveurs.

## 🚀 Fonctionnalités Clés

*   **🕵️ Détection en Temps Réel & Batch** : Analyse instantanée via daemon ou rétroactive sur fichiers.
*   **🚨 Règles de Sécurité Avancées** :
    *   Bruteforce SSH (avec seuil configurable)
    *   Attaques sur comptes multiples
    *   Connexions Root suspectes
    *   Modification de fichiers critiques (`/etc/passwd`, `/etc/shadow`, etc.)
    *   Pics d'activité anormaux
*   **🌐 Dashboard Web Moderne** : Interface responsive, graphiques temps réel, alertes critiques.
*   **📊 Rapports Automatisés** : Génération PDF/CSV des incidents.
*   **💾 Base de Données Locale** : Persistance SQLite performante et respectueuse de la vie privée.

---

## 📦 Installation Rapide

**Note** : Testé sur Linux (Ubuntu/Debian/Kali). Nécessite Python 3.10+.

1.  **Cloner le dépôt** :
    ```bash
    git clone https://github.com/votre-repo/logmonitor.git
    cd logmonitor
    ```

2.  **Lancer le script d'installation** :
    ```bash
    ./install.sh
    ```
    *Ce script crée un environnement virtuel, installe les dépendances et configure l'outil.*

3.  **Activer l'environnement** :
    ```bash
    source venv/bin/activate
    ```

C'est tout ! 🎉

---

## 🛠️ Guide d'Utilisation

### 1. 🖥️ Interface en Ligne de Commande (CLI)

LogMonitor s'utilise principalement via la commande `logmonitor`.

#### **Scanner un fichier de logs**
Pour analyser un fichier spécifique (détection automatique du format Auth/Syslog) :
```bash
logmonitor scan -f /var/log/auth.log
# Ou pour tester avec nos fichiers de démo :
logmonitor scan -f tests/test_logs/01_bruteforce_ssh.log
```

#### **Gérer la Base de Données**
Voir les alertes détectées :
```bash
logmonitor alerts list
```
Nettoyer la base de données (logs et alertes) :
```bash
logmonitor clean
# Pour forcer sans confirmation :
logmonitor clean --force
```

#### **Générer un Rapport**
Créer un rapport PDF des dernières activités :
```bash
logmonitor report generate
```

### 2. 🌐 Dashboard Web

Pour visualiser les alertes graphiquement :

```bash
# Lancer le serveur web
logmonitor web
```
*   Accédez à **http://localhost:5000**
*   **Login par défaut** : `admin` / `logmonitor123` (Configurable dans config/credentials.yaml)

**Nouveau : Mode Daemon**
Pour lancer le web en tâche de fond :
```bash
logmonitor web --daemon
# Pour l'arrêter :
logmonitor web --stop
```

---

## 🧪 Tests & Démonstration

Le projet est fourni avec un générateur de scénarios pour valider le fonctionnement.

**Générer des logs de test :**
```bash
python3 tests/generate_scenarios.py
```
Cela crée 6 fichiers dans `tests/test_logs/` simulant diverses attaques.

**Lancer une validation complète :**
```bash
# Nettoie la DB et scanne tous les fichiers de test
logmonitor clean --force
for f in tests/test_logs/*.log; do logmonitor scan -f $f; done
logmonitor alerts list
```

---

## ⚙️ Configuration

Tout est configurable dans `config/logmonitor.yaml` :
*   Chemins des logs à surveiller (`/var/log/...` ou `journalctl`)
*   Seuils de détection (nombre d'essais, fenêtres de temps)
*   Niveaux de sévérité
*   Ports et IPs autorisées

## 👥 Équipe Projet

*Projet académique - École Supérieure de Gestion d'Informatique et de Sciences*

*   **AGUESSI Melkior** (Collecte)
*   **HOUNTONDJI Sophie** (Détection)
*   **BATONON Darwin** (Persistance)
*   **AIHOU Consylia** (CLI)
*   **DADAVI Camel** (Web & Rapports)

---
© 2026 LogMonitor Team.
