# LogMonitor

Outil de surveillance et d'analyse de sécurité pour les logs Linux.

## Fonctionnalités

- **Détection temps réel & batch** — Analyse les logs en continu (daemon) ou ponctuellement
- **5 règles de sécurité** — Bruteforce SSH, comptes multiples, connexions root, fichiers sensibles, pics d'activité
- **Dashboard web** — Visualisation des alertes, statistiques et IPs suspectes
- **Rapports PDF/CSV** — Génération automatique de rapports d'incidents
- **Stockage SQLite** — Base de données locale, respectueuse de la vie privée
- **Démarrage automatique** — Service systemd activé à l'installation

## Installation Rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/Lil-grxpe/LogMonitor.git
cd LogMonitor

# 2. Lancer l'installation
./install.sh
```

Le script `install.sh` gère **tout automatiquement** :
- ✅ Vérification de Python 3.10+
- ✅ Installation de `pipx` (si absent)
- ✅ Installation de LogMonitor comme commande globale
- ✅ Configuration du fichier de logs selon la distribution
- ✅ Activation du service systemd (démarrage automatique au boot)
- ✅ Démarrage immédiat de LogMonitor

> **Après l'installation, LogMonitor est actif.** Aucune commande supplémentaire n'est nécessaire.

**Dashboard** : http://127.0.0.1:5000  
**Identifiants** : admin / admin

## Commandes CLI

```bash
# Scan ponctuel d'un fichier de logs
logmonitor scan -f /var/log/auth.log

# Lister les alertes détectées
logmonitor alerts list
logmonitor alerts list --severity critical

# Générer un rapport
logmonitor report generate --format pdf
logmonitor report generate --format csv

# Nettoyer la base de données
logmonitor clean --force
```

## Gestion du Service

LogMonitor se lance automatiquement au démarrage de la machine. Pour le gérer :

```bash
sudo systemctl status logmonitor       # Voir l'état
sudo systemctl stop logmonitor         # Arrêter
sudo systemctl start logmonitor        # Démarrer
sudo systemctl restart logmonitor      # Redémarrer
sudo journalctl -u logmonitor -f       # Voir les logs en direct
```

Vous pouvez aussi utiliser les commandes CLI directement :

```bash
logmonitor start     # Démarrer manuellement
logmonitor status    # Vérifier l'état
logmonitor stop      # Arrêter
```

## Dashboard Web

```bash
# Lancement en premier plan
logmonitor web --port 5000

# Lancement en arrière-plan
logmonitor web --daemon
```

## Configuration

Éditez `config/logmonitor.yaml` :

```yaml
logs:
  auto_detect: true  # Détection automatique selon la distro
  paths:
    - /var/log/auth.log  # Debian/Ubuntu
    # - /var/log/secure  # RHEL/CentOS
  mode: streaming

detection:
  bruteforce_ssh:
    enabled: true
    threshold: 5
    time_window: 300
```

## Distributions Supportées

| Distribution | Fichiers de logs |
|---|---|
| Debian / Ubuntu | /var/log/auth.log, /var/log/syslog |
| RHEL / CentOS / Fedora | /var/log/secure, /var/log/messages |
| Kali / Arch | journald (utiliser le script d'export) |

## Documentation Complète

- [Guide d'installation](docs/installation.md)
- [Guide complet](docs/guide_complet/01_Introduction.md)
- [Guide daemon](docs/daemon_guide.md)
- [Guide Kali Linux](docs/kali_linux_guide.md)

## Équipe

Projet académique — ESGIS 2026

---
© 2026 LogMonitor Team
