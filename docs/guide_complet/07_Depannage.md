# 7. Dépannage et FAQ

Solutions aux problèmes les plus fréquents rencontrés avec LogMonitor.

## Problèmes Courants

### 🛑 « logmonitor: command not found »

**Cause** : Le PATH n'a pas été rechargé après l'installation.

**Solution** :
1.  Rechargez votre shell :
    ```bash
    source ~/.bashrc   # bash
    source ~/.zshrc    # zsh
    ```
2.  Ou ouvrez un **nouveau terminal**.
3.  Si le problème persiste, vérifiez que le binaire existe :
    ```bash
    ls ~/.local/bin/logmonitor
    ```
4.  Si le fichier n'existe pas, réinstallez :
    ```bash
    pipx uninstall logmonitor 2>/dev/null || true
    cd /chemin/vers/LogMonitor
    pipx install .
    source ~/.bashrc
    ```

### 🛑 « Permission denied » lors de la lecture des logs

**Symptôme** : LogMonitor démarre mais ne détecte rien, ou affiche une erreur d'accès aux logs.

**Solution** :
1.  Sur les systèmes avec `/var/log/auth.log` (Debian/Ubuntu/Lubuntu) :
    ```bash
    sudo usermod -aG adm $USER
    ```
2.  Sur les systèmes journald (Kali, Arch, Ubuntu 24.04+) :
    ```bash
    sudo usermod -aG systemd-journal $USER
    ```
3.  Déconnectez-vous et reconnectez-vous pour appliquer les groupes, ou rechargez-les avec `newgrp adm` (ou `newgrp systemd-journal`).

### 🐍 « pipx not found »

**Symptôme** : La commande `install.sh` échoue car `pipx` est introuvable.

**Solution** :
*   Sur Debian/Ubuntu : `sudo apt install pipx`
*   Sur Fedora : `sudo dnf install pipx`
*   Sur Arch : `sudo pacman -S python-pipx`
*   Puis ajoutez-le au PATH : `pipx ensurepath` et relancez votre terminal.

### 🌐 Dashboard inaccessible

**Symptôme** : Impossible de se connecter à `http://127.0.0.1:5000`.

**Vérifications** :
1.  Le serveur web est-il lancé ? (`logmonitor web`)
2.  Si vous êtes sur un serveur distant (VPS), le port 5000 est-il ouvert dans le pare-feu ?
3.  Vérifiez les erreurs : `sudo journalctl -u logmonitor -n 20`

### ⚙️ Le service systemd ne démarre pas

**Symptôme** : `sudo systemctl status logmonitor` affiche « failed » ou « inactive ».

**Solution** :
1.  Vérifier les logs du service :
    ```bash
    sudo journalctl -u logmonitor -n 30
    ```
2.  Vérifier les permissions et sources de logs :
    ```bash
    ls -la /var/log/auth.log 2>/dev/null || echo 'Pas de auth.log'
    ls /run/systemd/journal/socket 2>/dev/null || echo 'Pas de journald'
    ```
3.  Vérifier que le binaire existe :
    ```bash
    ls -la ~/.local/bin/logmonitor
    ```
4.  Redémarrer le service :
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart logmonitor
    ```

---

## FAQ

**LogMonitor se lance-t-il automatiquement au démarrage ?**
Oui. Le script `install.sh` installe et active un service systemd. LogMonitor démarre automatiquement à chaque boot.

**LogMonitor envoie-t-il mes logs sur Internet ?**
Non. Tout reste 100% local sur votre machine. Aucune donnée ne sort.

**Puis-je surveiller plusieurs fichiers en même temps ?**
Oui. Ajoutez les chemins dans `config/logmonitor.yaml` sous `logs.paths`. Chaque fichier est surveillé dans un thread séparé.

**Comment désinstaller LogMonitor ?**
```bash
# 1. Désactiver le service
sudo systemctl stop logmonitor
sudo systemctl disable logmonitor
sudo rm /etc/systemd/system/logmonitor.service
sudo systemctl daemon-reload

# 2. Désinstaller le package
pipx uninstall logmonitor
```

[< Précédent : Architecture Technique](./06_Architecture_Technique.md) | [Retour au début : Introduction](./01_Introduction.md)
