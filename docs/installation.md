# Guide d'Installation - LogMonitor

## Installation Rapide (Recommandé)

**Une seule commande pour tout installer :**

```bash
cd Projet_tuteuré
./install.sh
```

Le script `install.sh` fait automatiquement :
- ✅ Vérification de Python 3.10+
- ✅ Création de l'environnement virtuel (venv)
- ✅ Installation de toutes les dépendances
- ✅ Installation de LogMonitor
- ✅ Création des répertoires nécessaires
- ✅ Validation de la configuration

---

## Après Installation

### 1. Activer l'environnement

```bash
source venv/bin/activate
```

### 2. Vérifier l'installation

```bash
logmonitor --version
# Output: logmonitor, version 0.1.0

logmonitor config validate
# Output: ✅ Configuration valide
```

### 3. Utiliser LogMonitor

```bash
# Mode daemon (arrière-plan)
logmonitor start
logmonitor status
logmonitor stop

# Analyser un fichier
logmonitor scan /var/log/auth.log

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

Ou reconnectez-vous pour que les changements prennent effet.

---

## Installation Manuelle (Optionnel)

Si vous préférez installer manuellement :

```bash
# 1. Créer l'environnement
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 3. Installer LogMonitor
pip install -e .

# 4. Créer les répertoires
mkdir -p data/evidence reports /tmp/logmonitor
```

---

## Installation comme Service Système (Production)

Pour installer LogMonitor comme service systemd :

sudo ./scripts/install_service.sh
```

Ce script (nécessite root) :
- Crée l'utilisateur système `logmonitor`
- Installe LogMonitor dans `/opt/logmonitor`
- Configure le service systemd
- Configure les permissions

**Utilisation du service** :
```bash
sudo systemctl start logmonitor
sudo systemctl enable logmonitor
sudo systemctl status logmonitor
sudo journalctl -u logmonitor -f
```

---

## Prérequis

- **Système** : Linux (Ubuntu 20.04+, Debian 10+, ou équivalent)
- **Python** : Version 3.10 ou supérieure
- **RAM** : Minimum 2 GB
- **CPU** : Minimum 1 vCPU
- **Droits** : Accès en lecture aux fichiers de logs (`/var/log/`)

---

## Dépannage

### Problème : "Permission denied" lors de la lecture des logs

**Solution** : Ajouter votre utilisateur au groupe `adm`
```bash
sudo usermod -a -G adm $USER
newgrp adm
```

### Problème : "python3: command not found"

**Solution** : Installer Python 3.10+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Fedora/RHEL
sudo dnf install python3.10
```

### Problème : "Module not found"

**Solution** : Vérifier que l'environnement est activé
```bash
which python
# Devrait afficher: .../venv/bin/python
```

Si ce n'est pas le cas :
```bash
source venv/bin/activate
```

---

## Désinstallation

```bash
# Arrêter le daemon si actif
logmonitor stop

# Désactiver l'environnement
deactivate

# Supprimer les fichiers
cd ..
rm -rf Projet_tuteuré
```

Pour le service systemd :
```bash
sudo systemctl stop logmonitor
sudo systemctl disable logmonitor
sudo rm /etc/systemd/system/logmonitor.service
sudo systemctl daemon-reload
sudo userdel -r logmonitor
sudo rm -rf /opt/logmonitor
```

---

## Prochaines Étapes

Une fois l'installation terminée, consultez :
- [Guide utilisateur](user_guide.md) - Comment utiliser LogMonitor
- [Guide daemon](daemon_guide.md) - Utilisation du mode daemon
- [README.md](../README.md) - Vue d'ensemble du projet
