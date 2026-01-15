# Guide d'Utilisation - Mode Daemon

> **💡 Installation** : Si vous n'avez pas encore installé LogMonitor, exécutez d'abord `./install.sh` à la racine du projet.

## Démarrage du Service

### Méthode 1 : Via CLI LogMonitor

```bash
# Activer l'environnement
source venv/bin/activate

# Démarrer le daemon
logmonitor start

# Vérifier le statut
logmonitor status

# Arrêter le daemon
logmonitor stop
```

### Méthode 2 : Via systemd (en production)

```bash
# Installer le service
sudo ./scripts/install_service.sh

# Démarrer
sudo systemctl start logmonitor

# Activer au démarrage
sudo systemctl enable logmonitor

# Vérifier le statut
sudo systemctl status logmonitor

# Voir les logs
sudo journalctl -u logmonitor -f
```

## Fonctionnement du Daemon

Le daemon LogMonitor fonctionne en arrière-plan et :

1. **Surveille en continu** les fichiers de logs configurés  dans `config/logmonitor.yaml`
2. **Normalise** automatiquement chaque nouvelle ligne
3. **Détecte** les anomalies avec les 5 règles configurées
4. **Stocke** les logs et alertes dans SQLite
5. **Génère** des preuves sécurisées pour chaque alerte

## Architecture du Daemon

### Double Fork Unix
Le processus utilise la technique du double fork pour se détacher complètement du terminal parent :
- Premier fork : Détacher du processus parent
- Second fork : Créer un nouveau groupe de processus

### Gestion des Signaux
- `SIGTERM` : Arrêt propre avec nettoyage
- `SIGINT` : Interruption (Ctrl+C)
- `SIGKILL` : Arrêt forcé (dernier recours)

### Fichiers Importants
- **PID file** : `/tmp/logmonitor/logmonitor.pid` - Contient le PID du processus
- **Log file** : `/tmp/logmonitor/app.log` - Logs internes du daemon
- **Database** : `data/logmonitor.db` - Base SQLite

## Surveillance Multi-Fichiers

Le daemon peut surveiller plusieurs fichiers de logs simultanément :

```yaml
# config/logmonitor.yaml
logs:
  paths:
    - /var/log/auth.log
    - /var/log/syslog
    - /var/log/custom.log
```

Chaque fichier est surveillé dans un thread séparé pour des performances optimales.

## Commandes Utiles

```bash
# Voir les logs du daemon (si en mode CLI)
tail -f /tmp/logmonitor/app.log

# Voir les alertes en temps réel
logmonitor alerts list

# Générer un rapport pendant que le daemon tourne
logmonitor report generate

# Lancer le dashboard web
logmonitor web
```

## Dépannage

### Le daemon ne démarre pas

```bash
# Vérifier le statut
logmonitor status

# Vérifier s'il y a un PID obsolète
cat /tmp/logmonitor/logmonitor.pid

# Nettoyer
rm -f /tmp/logmonitor/logmonitor.pid
```

### Le daemon se termine de manière inattendue

```bash
# Vérifier les logs
tail -50 /tmp/logmonitor/app.log

# Vérifier les permissions
ls -la /var/log/auth.log
```

### Problème de permissions

```bash
# Ajouter l'utilisateur au groupe adm
sudo usermod -a -G adm $USER

# Recharger les groupes
newgrp adm
```

## Arrêt Propre

Toujours utiliser `logmonitor stop` ou `systemctl stop logmonitor` pour un arrêt propre.

Ne **jamais** utiliser `kill -9` sauf en dernier recours, car cela empêche le nettoyage :
- Fermeture de la DB
- Suppression du PID file
- Flush des buffers

## Performance

Le daemon est optimisé pour :
- **Latence minimale** : Traitement en < 10 secondes
- **Multi-threading** : Un thread par fichier de log
- **Surveillance temps réel** : Utilise watchdog pour détecter les modifications
- **Gestion mémoire** : Nettoyage automatique du contexte de détection

## Sécurité

Le daemon respecte les bonnes pratiques Unix :
- Exécution avec droits minimaux
- Pas d'envoi de données à l'extérieur
- Stockage local sécurisé avec hash SHA256
- Logs internes avec rotation automatique
