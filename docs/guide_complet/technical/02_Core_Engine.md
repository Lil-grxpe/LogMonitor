# 2. Cœur du Système (Core Engine)

Le package `logmonitor.core` est responsable de toute la chaîne de traitement des logs.

## 1. Collecteur (`collector.py`)

Le module `collector` gère l'ingestion des logs. Il utilise la bibliothèque **Watchdog** pour une surveillance efficace.

*   **Classe `LogCollector`** : Interface abstraite.
*   **Classe `AuthLogCollector`** : Implémentation spécifique pour les logs d'authentification.
*   **Mode Batch** : Lit le fichier ligne par ligne (itérateur) pour une analyse historique.
*   **Mode Streaming** : Utilise `Observer` et `FileSystemEventHandler` pour détecter l'écriture de nouvelles lignes (`FileModifiedEvent`). Cela évite de polling intensif et économise le CPU.

## 2. Normalisateur (`normalizer.py`)

Ce module transforme des chaînes de caractères brutes en dictionnaires Python structurés.

*   **Logique** : Utilise des expressions régulières (`re`) pré-compilées pour la performance.
*   **Classe `AuthLogNormalizer`** : Contient les patterns pour :
    *   `ssh_failed` : Échecs de mot de passe SSH.
    *   `ssh_accepted` : Connexions réussies.
    *   `sudo` : Commandes exécutées via sudo.
    *   `sudo_failed` : Échecs sudo.

**Exemple de transformation :**
```python
# Entrée (Raw)
"Oct 27 10:00:00 server sshd[123]: Failed password for root from 1.2.3.4"

# Sortie (Dict)
{
    "timestamp": "2023-10-27T10:00:00",
    "event_type": "ssh_failed_login",
    "user": "root",
    "source_ip": "1.2.3.4",
    "level": "warning"
}
```

## 3. Détecteur (`detector.py` & `rules.py`)

Le `DetectionEngine` reçoit les événements normalisés et les soumet aux règles de sécurité.

### Gestion du Contexte
Le moteur maintient un objet `DetectionContext` en mémoire pour les règles qui nécessitent une corrélation temporelle (Stateful).
*   *Exemple* : Pour détecter un bruteforce, il faut compter le nombre d'échecs *pour une même IP* dans une *fenêtre de 5 minutes*.

### Types de Règles (`rules.py`)
Chaque règle hérite de la classe de base `DetectionRule`.

1.  **BruteForceSSHRule** : Compte les `ssh_failed_login` par IP. Déclenche une alerte si `count > threshold`.
2.  **SuspiciousRootLoginRule** : Alerte immédiate si `user == 'root'` et `event_type == 'ssh_accepted_login'`.
3.  **UnusualLoginTimeRule** : Vérifie si l'heure de connexion est dans la liste des "heures interdites" configurées.

[< Précédent : Vue d'Ensemble](./01_Overview.md) | [Suivant : Base de Données >](./03_Database.md)
