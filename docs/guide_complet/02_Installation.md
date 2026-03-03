# 2. Installation de LogMonitor

Ce guide couvre l'installation de LogMonitor sur les distributions Linux courantes (Debian, Ubuntu, CentOS, Fedora, Arch, Kali).

## Prérequis

*   **Système d'exploitation** : Linux (supportant systemd pour le démarrage automatique).
*   **Python** : Version 3.10 ou supérieure.
    *   Vérifier avec : `python3 --version`
*   **Droits** : Accès `sudo` (pour installer les dépendances système et le service).

## Méthode Recommandée : Script Automatique

Le script `install.sh` gère tout pour vous : détection de la distribution, installation des dépendances, configuration et activation du service systemd.

1.  **Cloner le dépôt** :
    ```bash
    git clone https://github.com/Lil-grxpe/LogMonitor.git
    cd LogMonitor
    ```

2.  **Lancer l'installation** :
    ```bash
    ./install.sh
    ```

3.  **Suivre les instructions** :
    *   Le script installera `pipx` si nécessaire.
    *   Il configurera la détection automatique de la source de logs (journald ou auth.log).
    *   Il installera et activera le **service systemd** pour un démarrage automatique au boot.
    *   LogMonitor sera **démarré immédiatement** à la fin de l'installation.

4.  **Recharger votre shell** :
    ```bash
    source ~/.bashrc   # bash
    # ou
    source ~/.zshrc    # zsh
    ```

## Méthode Alternative : Installation Manuelle

Si vous préférez installer manuellement via `pipx` :

```bash
# 1. Installer pipx (si absent)
sudo apt install pipx  # Debian/Ubuntu
# ou
sudo dnf install pipx  # Fedora/RHEL

# 2. Ajouter pipx au PATH
pipx ensurepath
source ~/.bashrc

# 3. Installer LogMonitor depuis le dossier source
cd LogMonitor
pipx install .
```

## Vérification de l'Installation

```bash
# Vérifier la commande
logmonitor --version

# Vérifier le service (si installé via install.sh)
sudo systemctl status logmonitor
```

> Si `logmonitor: command not found` apparaît, rechargez votre shell avec `source ~/.bashrc` ou ouvrez un nouveau terminal.

## Gestion du Service Systemd

Après l'installation, LogMonitor démarre **automatiquement** à chaque boot :

```bash
sudo systemctl status logmonitor       # Voir l'état
sudo systemctl stop logmonitor         # Arrêter
sudo systemctl restart logmonitor      # Redémarrer
sudo journalctl -u logmonitor -f       # Voir les logs en direct
```

[< Précédent : Introduction](./01_Introduction.md) | [Suivant : Configuration >](./03_Configuration.md)
