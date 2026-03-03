# Guide d'Installation - LogMonitor

## Installation Rapide (Recommandé)

**Une seule commande pour tout installer :**

```bash
cd LogMonitor
./install.sh
```

Le script `install.sh` fait automatiquement :
- ✅ Vérification de Python 3.10+
- ✅ Détection de la distribution Linux
- ✅ Installation de `pipx` (gestionnaire de packages Python)
- ✅ Installation de LogMonitor comme commande globale
- ✅ Création des répertoires nécessaires (data, reports)
- ✅ Configuration du fichier de logs (selon la distro)
- ✅ Installation et activation du service systemd
- ✅ Démarrage immédiat de LogMonitor

---

## Après Installation

### 1. Recharger le shell

```bash
source ~/.bashrc    # bash
# ou
source ~/.zshrc     # zsh
```

### 2. Vérifier l'installation

```bash
logmonitor --version
# Output: LogMonitor, version 0.1.0

logmonitor config-validate
# Output: [+] Config valid
```

### 3. Vérifier le service

LogMonitor se lance **automatiquement au démarrage** de la machine :

```bash
sudo systemctl status logmonitor
```

### 4. Utiliser LogMonitor

```bash
# Analyser un fichier
logmonitor scan -f /var/log/auth.log

# Voir les alertes
logmonitor alerts list

# Générer un rapport
logmonitor report generate

# Dashboard web
logmonitor web
```

---

## Configuration des Permissions

Pour lire les fichiers de logs système, ajoutez votre utilisateur au groupe `adm` :

```bash
sudo usermod -a -G adm $USER
newgrp adm
```

Ou déconnectez-vous puis reconnectez-vous.

---

## Installation Manuelle (Optionnel)

Si vous préférez installer manuellement :

```bash
# 1. Installer pipx
sudo apt install pipx       # Debian/Ubuntu
pipx ensurepath
source ~/.bashrc

# 2. Installer LogMonitor
cd LogMonitor
pipx install .

# 3. Créer les répertoires
mkdir -p data/evidence reports /tmp/logmonitor

# 4. Activer le démarrage automatique (optionnel)
sudo cp logmonitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now logmonitor
```

---

## Gestion du Service Systemd

```bash
sudo systemctl status logmonitor       # Voir l'état
sudo systemctl stop logmonitor         # Arrêter
sudo systemctl start logmonitor        # Démarrer
sudo systemctl restart logmonitor      # Redémarrer
sudo systemctl disable logmonitor      # Désactiver le démarrage auto
sudo journalctl -u logmonitor -f       # Voir les logs en direct
```

---

## Prérequis

- **Système** : Linux (Ubuntu 20.04+, Lubuntu, Debian 10+, Fedora, Arch, Kali…)
- **Python** : Version 3.10 ou supérieure
- **RAM** : Minimum 2 GB
- **CPU** : Minimum 1 vCPU
- **Droits** : Lecture des logs système (`adm` pour fichiers, `systemd-journal` pour journald)

---

## Dépannage

### « logmonitor: command not found »

**Cause** : Le PATH n'est pas rechargé après l'installation.

```bash
# Solution 1 : Recharger le shell
source ~/.bashrc   # ou ~/.zshrc

# Solution 2 : Lancer directement
~/.local/bin/logmonitor --version

# Solution 3 : Réinstaller
pipx uninstall logmonitor 2>/dev/null || true
pipx install .
source ~/.bashrc
```

### « Permission denied » lors de la lecture des logs

Sur les systèmes avec `/var/log/auth.log` (Debian/Ubuntu/Lubuntu) :
```bash
sudo usermod -a -G adm $USER
newgrp adm
```

Sur les systèmes journald (Kali, Arch, Ubuntu 24.04+) :
```bash
sudo usermod -a -G systemd-journal $USER
newgrp systemd-journal
```

### « python3: command not found »

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.10 python3.10-venv python3-pip

# Fedora/RHEL
sudo dnf install python3.10
```

---

## Désinstallation

```bash
# 1. Désactiver et supprimer le service
sudo systemctl stop logmonitor
sudo systemctl disable logmonitor
sudo rm /etc/systemd/system/logmonitor.service
sudo systemctl daemon-reload

# 2. Désinstaller LogMonitor
pipx uninstall logmonitor

# 3. Supprimer les fichiers (optionnel)
rm -rf /tmp/logmonitor
```

---

## Prochaines Étapes

- [Guide utilisateur CLI](guide_complet/04_Utilisation_CLI.md)
- [Guide daemon](daemon_guide.md)
- [Dashboard web](guide_complet/05_Tableau_de_Bord.md)
- [README](../README.md)
