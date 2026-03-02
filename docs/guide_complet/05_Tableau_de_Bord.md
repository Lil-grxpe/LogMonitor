# 5. Tableau de Bord Web

LogMonitor inclut une interface web moderne pour visualiser la sécurité de votre système.

## Lancer le Dashboard

Vous pouvez lancer le serveur web via la ligne de commande :

```bash
# Lancement simple (bloque le terminal)
logmonitor web

# Lancement en arrière-plan (recommandé)
logmonitor web --daemon
```

Le dashboard sera accessible à l'adresse : **http://127.0.0.1:5000**

## Connexion

*   **Identifiant par défaut** : `admin`
*   **Mot de passe par défaut** : `admin`

> ⚠️ **Important** : Changez le mot de passe dès la première connexion via l'onglet *Paramètres (Settings)*.

## Navigation

### 🏠 Dashboard (Accueil)
Une vue d'ensemble de la sécurité du système :
*   **Alertes Récentes** : Liste des 5 dernières menaces détectées.
*   **Statistiques** : Graphiques montrant l'évolution des attaques dans le temps.
*   **Top IPs Suspectes** : Les adresses IP générant le plus d'alertes.

### 📋 Rapports (Reports)
Cette page vous permet de :
*   Générer des rapports PDF ou CSV à la demande.
*   Télécharger les rapports précédemment générés.

### ⚙️ Paramètres (Settings)
*   **Changer le mot de passe** : Modifiez vos identifiants de connexion.
*   **Voir la configuration** : Affiche la configuration actuelle (lecture seule) pour vérification.

[< Précédent : Utilisation CLI](./04_Utilisation_CLI.md) | [Suivant : Architecture Technique >](./06_Architecture_Technique.md)
