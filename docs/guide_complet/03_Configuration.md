# 3. Configuration

LogMonitor est conçu pour fonctionner avec une configuration minimale ("zero config"), mais il est entièrement personnalisable.

## Fichiers de Configuration

Tous les fichiers se trouvent dans le dossier `config/`.

1.  `config/logmonitor.yaml` : Configuration principale (logs, détection).
2.  `config/credentials.yaml` : Utilisateurs et mots de passe (Dashboard).

## Configurer les sources de Logs (`logmonitor.yaml`)

Par défaut, LogMonitor tente de détecter automatiquement votre distribution et le fichier de logs approprié.

```yaml
logs:
  auto_detect: true  # Laisse LogMonitor choisir la meilleure source
  paths: []          # Vide = auto-detect. 
  # Pour forcer manuellement :
  # paths:
  #   - /var/log/auth.log
  #   - journald://auth
  mode: streaming  # 'streaming' (temps réel) ou 'batch' (analyse statique)
```

Si vous utilisez un fichier personnalisé (ex: logs d'un serveur web), ajoutez son chemin dans `paths`.

## Régler la Sensibilité de Détection

Vous pouvez modifier les seuils de déclenchement des alertes dans la section `detection` :

```yaml
detection:
  bruteforce_ssh:
    enabled: true
    threshold: 5       # Nombre d'échecs avant alerte
    time_window: 300   # En secondes (5 minutes)
    
  suspicious_time:
    enabled: true
    hours: [23, 5]     # Alerte si connexion entre 23h et 5h
```

*   **threshold** : Le nombre d'événements suspects tolérés.
*   **time_window** : La période (en secondes) durant laquelle ces événements sont comptés.

## Gestion des Utilisateurs (`credentials.yaml`)

Ce fichier stocke les accès au Tableau de Bord Web.

```yaml
users:
  admin:
    password: "admin"  # Changez ceci immédiatement !
    role: "admin"
```

> **Note** : Il est recommandé de changer le mot de passe via l'interface web (Page *Paramètres*) plutôt que d'éditer ce fichier manuellement, pour éviter les erreurs de formatage.

[< Précédent : Installation](./02_Installation.md) | [Suivant : Utilisation CLI >](./04_Utilisation_CLI.md)
