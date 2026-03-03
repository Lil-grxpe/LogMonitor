# Guide LogMonitor pour Kali Linux (et systèmes journald)

## 🔍 Fonctionnement automatique

Sur **Kali Linux**, **Arch** et tout système n'ayant pas de `/var/log/auth.log` (Ubuntu 24.04+, Lubuntu minimal, etc.), LogMonitor **détecte automatiquement** que journald est la source de logs et s'y connecte sans aucune configuration manuelle.

```
LogMonitor démarre → détecte la distro → cherche /var/log/auth.log
→ introuvable → vérifie /run/systemd/journal/socket
→ journald disponible → connecte journald://auth + journald://system
→ streaming en temps réel via journalctl -f
```

> **Aucune action requise.** Lancer `logmonitor start` suffit.

---

## 🚀 Installation sur Kali

```bash
git clone https://github.com/Lil-grxpe/LogMonitor.git
cd LogMonitor
./install.sh
```

Le script détecte Kali et active le service systemd. LogMonitor démarre automatiquement au boot.

---

## 🧪 Utilisation

### Démarrage / statut

```bash
sudo systemctl status logmonitor
logmonitor status
```

### Scan ponctuel (logs récents via journald)

```bash
# Exporter puis analyser
journalctl -u ssh --since "24 hours ago" --no-pager -o short-iso > /tmp/ssh.log
logmonitor scan -f /tmp/ssh.log
```

### Alertes en temps réel

```bash
# Voir les alertes détectées
logmonitor alerts list
logmonitor alerts list --severity high

# Dashboard web
logmonitor web --port 5000
```

---

## 📊 Configuration journald explicite (optionnel)

Si vous voulez forcer les sources journald dans `config/logmonitor.yaml` :

```yaml
logs:
  auto_detect: false  # désactiver la détection automatique
  paths:
    - journald://auth    # sshd, sudo, login, su, useradd...
    - journald://system  # tous les messages système
  mode: streaming
```

---

## 🔑 Permissions journald

Pour lire journald sans sudo :

```bash
sudo usermod -a -G systemd-journal $USER
newgrp systemd-journal
```

Pour rendre les logs persistants (redémarrages) :

```bash
sudo mkdir -p /var/log/journal
sudo systemctl restart systemd-journald
```

---

## 🐛 Dépannage

### LogMonitor ne détecte rien

```bash
# Vérifier que journald tourne
ls /run/systemd/journal/socket   # doit exister
journalctl --lines=5 --no-pager  # doit afficher des lignes

# Vérifier les logs LogMonitor
tail -f /tmp/logmonitor/app.log
```

### « journalctl: command not found »

```bash
sudo apt install systemd
```

### SSH non loggué dans journald

```bash
sudo systemctl status ssh
sudo systemctl start ssh
```

---

## 💡 Test bruteforce SSH (depuis Kali vers VM cible)

```bash
# Attaque bruteforce depuis Kali
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://[IP_VM]

# Sur la VM cible (LogMonitor actif) → vérifier alertes
logmonitor alerts list --severity high
```

---

**Version** : 2.0 — mars 2026  
**Maintenu par** : Équipe LogMonitor
