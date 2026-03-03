# Guide d'Utilisation - Mode Daemon

> **💡 Installation** : Si vous n'avez pas encore installé LogMonitor, exécutez `./install.sh` à la racine du projet. Le daemon sera automatiquement activé au démarrage.

## Démarrage du Service

### Méthode 1 : Via systemd (recommandé — installé automatiquement)

Le script `install.sh` configure et active un service systemd. LogMonitor démarre **automatiquement à chaque boot**.

```bash
# Vérifier l'état du service
sudo systemctl status logmonitor

# Redémarrer
sudo systemctl restart logmonitor

# Arrêter
sudo systemctl stop logmonitor

# Réactiver le démarrage automatique
sudo systemctl enable logmonitor

# Voir les logs en direct
sudo journalctl -u logmonitor -f
```

### Méthode 2 : Via CLI LogMonitor (manuel)

Si vous préférez gérer le daemon manuellement :

```bash
# Démarrer le daemon
logmonitor start

# Vérifier le statut
logmonitor status

# Arrêter le daemon
logmonitor stop
```

## Fonctionnement du Daemon

Le daemon LogMonitor fonctionne en arrière-plan et :

1. **Détecte automatiquement** la source de logs selon la distribution :
   - `auth.log` / `syslog` sur Debian, Ubuntu, Lubuntu
   - `journald://auth` + `journald://system` sur Kali, Arch et tout système sans fichiers plats
2. **Surveille en continu** via watchdog (fichiers) ou `journalctl -f` (journald)
3. **Normalise** automatiquement chaque nouvelle ligne de log
4. **Détecte** les anomalies avec les règles de sécurité configurées
5. **Stocke** les logs et alertes dans la base SQLite
6. **Génère** des preuves sécurisées (hash SHA256) pour chaque alerte

## Architecture du Daemon

### Double Fork Unix
Le processus utilise la technique du double fork pour se détacher complètement du terminal :
- Premier fork : Détacher du processus parent
- Second fork : Créer un nouveau groupe de processus

### Gestion des Signaux
- `SIGTERM` : Arrêt propre avec nettoyage
- `SIGINT` : Interruption (Ctrl+C)
- `SIGKILL` : Arrêt forcé (dernier recours)

### Fichiers Importants
- **PID file** : `/tmp/logmonitor/logmonitor.pid` — Contient le PID du processus
- **Log file** : `/tmp/logmonitor/app.log` — Logs internes du daemon
- **Database** : `data/logmonitor.db` — Base SQLite

## Sources de Logs Supportées

Le daemon détecte automatiquement la bonne source. Configuration manuelle optionnelle dans `config/logmonitor.yaml` :

```yaml
# config/logmonitor.yaml
logs:
  auto_detect: true  # Détection automatique (recommandé)
  paths: []          # Laisser vide = auto-detect

  # Ou forcer manuellement :
  # paths:
  #   - /var/log/auth.log         # Debian/Ubuntu/Lubuntu
  #   - /var/log/syslog           # Debian/Ubuntu
  #   - journald://auth           # Kali/Arch/systemd
  #   - journald://system         # Tous messages système
```

Chaque source est surveillée dans un thread séparé pour des performances optimales.

## Commandes Utiles

```bash
# Voir les logs du daemon
sudo journalctl -u logmonitor -f      # via systemd
tail -f /tmp/logmonitor/app.log       # via fichier

# Voir les alertes en temps réel
logmonitor alerts list

# Générer un rapport pendant que le daemon tourne
logmonitor report generate

# Lancer le dashboard web
logmonitor web --daemon
```

## Dépannage

### Le service systemd ne démarre pas

```bash
# Vérifier les logs détaillés
sudo journalctl -u logmonitor -n 30

# Vérifier que le binaire existe
ls -la ~/.local/bin/logmonitor

# Recharger et redémarrer
sudo systemctl daemon-reload
sudo systemctl restart logmonitor
```

### Le daemon CLI ne démarre pas

```bash
# Vérifier s'il tourne déjà
logmonitor status

# Vérifier s'il y a un PID obsolète
cat /tmp/logmonitor/logmonitor.pid

# Nettoyer le PID obsolète
rm -f /tmp/logmonitor/logmonitor.pid
```

### Le daemon se termine de manière inattendue

```bash
# Voir les logs
tail -50 /tmp/logmonitor/app.log

# Vérifier si une source de logs est détectée
# (le daemon loguera "CRITICAL: No collectors" si aucune source trouvée)
grep -i 'collector\|critical\|journald' /tmp/logmonitor/app.log

# Vérifier les permissions sur les fichiers de logs
ls -la /var/log/auth.log 2>/dev/null || echo 'Pas de auth.log'
ls /run/systemd/journal/socket 2>/dev/null || echo 'Pas de journald'

### Problème de permissions

```bash
# Ajouter l'utilisateur au groupe adm
sudo usermod -a -G adm $USER
newgrp adm
```

## Arrêt Propre

Toujours utiliser `sudo systemctl stop logmonitor` ou `logmonitor stop` pour un arrêt propre.

Ne **jamais** utiliser `kill -9` sauf en dernier recours, car cela empêche le nettoyage :
- Fermeture de la base de données
- Suppression du fichier PID
- Flush des buffers

## Performance

Le daemon est optimisé pour :
- **Latence minimale** : Traitement en < 10 secondes
- **Multi-threading** : Un thread par source de log
- **Surveillance temps réel** : watchdog pour les fichiers, `journalctl -f` pour journald
- **Gestion mémoire** : Nettoyage automatique du contexte de détection

## Sécurité

Le daemon respecte les bonnes pratiques Unix :
- Exécution avec droits minimaux
- Pas d'envoi de données à l'extérieur
- Stockage local sécurisé avec hash SHA256
- Logs internes avec rotation automatique
