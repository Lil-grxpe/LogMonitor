# 📊 Diagramme de Flux de Données (DFD) - LogMonitor

Ce diagramme illustre le parcours technique d'une information (un log brut) depuis sa création par le système d'exploitation jusqu'à son affichage sous forme d'alerte critique sur le tableau de bord web.

```mermaid
flowchart TD
    %% Entités Externes (Sources)
    subgraph Sources ["Machine Cible (OS Linux)"]
        OS_AUTH["/var/log/auth.log"]
        OS_JOURNAL["systemd-journald"]
    end

    %% Composants Core LogMonitor
    subgraph Core ["LogMonitor Daemon (Arrière-plan)"]
        COL_FILE["LogCollector (watchdog)"]
        COL_JOURNAL["JournaldCollector (subprocess)"]
        
        NORM["Normalizer (Regex Parseur)"]
        
        DETECTOR["Detector (Moteur de Règles)"]
        
        RULES["Règles de Sécurité\n- BruteForce\n- Sudo\n- Spike..."]
    end

    %% Base de données
    subgraph Storage ["Persistance locale"]
        DB[(SQLite3 Database)]
    end

    %% Interface Web
    subgraph Frontend ["Serveur Web (Port 5000)"]
        FLASK["Flask API Backend"]
        UI["Tableau de Bord HTML/JS"]
        PDF["Générateur PDF/CSV"]
    end

    %% --- Flux de données ---
    
    %% 1. Collecte
    OS_AUTH -- "Flux texte\n(Temps réel)" --> COL_FILE
    OS_JOURNAL -- "Flux texte\n(journalctl -f)" --> COL_JOURNAL
    
    %% 2. Normalisation
    COL_FILE -- "Ligne brute" --> NORM
    COL_JOURNAL -- "Ligne brute" --> NORM
    
    %% 3. Détection
    NORM -- "Dictionnaire JSON pur\n{ip, user, date, service}" --> DETECTOR
    DETECTOR <..> RULES : "Évaluation des seuils"
    
    %% 4. Stockage
    NORM -- "Statistiques de log trafic" --> DB
    DETECTOR -- "Alerte de Sécurité" --> DB
    
    %% 5. Affichage Web
    DB -- "Requêtes SQL\n(SELECT ... LIMIT 50)" --> FLASK
    FLASK -- "JSON (API REST)" --> UI
    FLASK -- "Export" --> PDF
    
    %% Styles visuels
    classDef source fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#fff;
    classDef core fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#fff;
    classDef db fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff;
    classDef web fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff;
    
    class OS_AUTH,OS_JOURNAL source;
    class COL_FILE,COL_JOURNAL,NORM,DETECTOR core;
    class DB db;
    class FLASK,UI,PDF web;
```

## Étapes du parcours de la donnée

1. **Génération (L'attaque)** : L'attaquant exécute `sshpass wrongpass`. Le serveur OpenSSH de Lubuntu génère un événement binaire et l'envoie à `systemd-journald`.
2. **Extraction (Collector)** : À la milliseconde près, le `JournaldCollector` branché sur le processus Linux lit la ligne texte (`mars 03 22:34 l-standard sshd: Failed password`).
3. **Traduction (Normalizer)** : La ligne de texte brut est analysée par une Regex ultra-ciblée. Le normaliseur "traduit" mentalement les mois français en anglais, et construit un objet python : `{"event": "ssh_failed", "ip": "192.168.1.10"}`.
4. **Décision (Detector)** : L'objet est transmis au cerveau. Le détecteur consulte le dictionnaire de mémoire caché (Cache) de `BruteForceSSHRule`. Si c'est la 5e fois que la règle voit cette IP en moins de 5 minutes, elle lève un drapeau rouge (Alerte).
5. **Enregistrement (Database)** : L'objet pur et l'Alerte (si levée) sont insérés via des verrous de Thread dans le fichier de base de données `logmonitor.db`.
6. **Affichage (Web)** : L'administrateur, depuis son navigateur de PC distant, réactualise le Dashboard `http://ip:5000`. L'application Flask lance une requête SQL sur `.db` et rafraichit la liste des alarmes en HTML avec la pastille "CRITICAL".
