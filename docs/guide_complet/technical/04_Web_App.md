# 4. Interface Web (`web/`)

L'interface web permet de visualiser les alertes en temps réel. Elle est construite avec le micro-framework **Flask**.

## Architecture Web

Le serveur Flask (`web/app.py`) joue deux rôles :
1.  **Serveur de pages** (HTML/Jinja2) pour le rendu initial.
2.  **API REST** (JSON) pour les mises à jour dynamiques via JavaScript.

### Routes Principales (HTML)

*   `GET /` : Dashboard principal (requiert authentification).
*   `GET /login` : Page de connexion.
*   `GET /settings` : Configuration et changement de mot de passe.
*   `GET /reports` : Page de génération de rapports.

### API REST (JSON)

Ces endpoints sont appelés par le frontend (`static/js/dashboard.js`) :

*   `GET /api/stats` : Retourne les compteurs globaux (total logs, total alerts).
*   `GET /api/alerts` : Liste les alertes récentes.
    *   Paramètres : `?limit=50&severity=critical`
*   `GET /api/alerts/by-hour` : Données pour le graphiques d'activité (24h).
*   `POST /api/alerts/<id>/acknowledge` : Acquitte une alerte (la marque comme "vue").

## Frontend

L'interface n'utilise pas de framework lourd (React/Vue) pour rester légère, mais du **Javascript Vanilla** moderne.

*   **Graphiques** : La bibliothèque **Chart.js** est utilisée pour rendre les courbes d'activité et les camemberts de sévérité.
*   **Polling** : Un script JS interroge `/api/stats` et `/api/alerts` toutes les 5 secondes pour rafraîchir l'affichage sans recharger la page.

## Sécurité Web

*   **Sessions** : Sessions signées cryptographiquement par Flask (Secret Key aléatoire).
*   **Décorateur `@login_required`** : Protège toutes les routes sensibles.
*   **Mots de passe** : Stockés dans `config/credentials.yaml`. *Note de sécurité : Dans une version future, ils devraient être hashés (Argon2/BCrypt) plutôt que stockés en clair.*

[< Précédent : Base de Données](./03_Database.md) | [Retour au début](../06_Architecture_Technique.md)
