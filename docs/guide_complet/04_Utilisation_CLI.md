# 4. Utilisation en Ligne de Commande (CLI)

LogMonitor s'utilise principalement via le terminal. La commande principale est `logmonitor`.

## Commandes de Base

### 1. Lancer un Scan Manuel
Pour analyser un fichier de logs existant (mode « one-shot ») :

```bash
logmonitor scan -f /var/log/auth.log
```
Cela affichera les menaces détectées directement dans le terminal et les enregistrera dans la base de données.

### 2. Lister les Alertes
Pour voir l'historique des alertes enregistrées :

```bash
logmonitor alerts list
```

Filtrer par sévérité :
```bash
logmonitor alerts list --severity critical
```
(Sévérités disponibles : `low`, `medium`, `high`, `critical`)

### 3. Générer un Rapport
Pour créer un rapport complet des incidents :

```bash
logmonitor report generate --format pdf
# ou
logmonitor report generate --format csv
```
Les rapports sont sauvegardés dans le dossier `reports/`.

### 4. Nettoyer la Base de Données
Pour effacer toutes les anciennes alertes :

```bash
logmonitor clean --force
```

### 5. Valider la Configuration

```bash
logmonitor config-validate
```

## Mode Daemon (Surveillance en Arrière-plan)

### Via le service systemd (recommandé)

LogMonitor est installé comme **service systemd** et se lance **automatiquement au démarrage** de la machine. Vous n'avez rien à faire !

```bash
# Vérifier que le service tourne
sudo systemctl status logmonitor

# Redémarrer le service
sudo systemctl restart logmonitor

# Voir les logs du daemon en direct
sudo journalctl -u logmonitor -f
```

### Via la commande CLI (manuel)

Vous pouvez aussi démarrer et arrêter LogMonitor manuellement :

*   **Démarrer la surveillance** :
    ```bash
    logmonitor start
    ```
    Le programme tournera en fond et analysera les logs en temps réel.

*   **Vérifier le statut** :
    ```bash
    logmonitor status
    ```

*   **Arrêter la surveillance** :
    ```bash
    logmonitor stop
    ```

> **Astuce** : Vous pouvez lancer le Dashboard Web en même temps que le daemon pour visualiser les alertes en direct avec `logmonitor web --daemon`.

[< Précédent : Configuration](./03_Configuration.md) | [Suivant : Tableau de Bord >](./05_Tableau_de_Bord.md)
