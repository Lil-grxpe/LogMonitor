# ⚙️ Architecture Technique & Manuel Exhaustif du Code de LogMonitor

Ce document fournit une analyse approfondie et ultra-détaillée du code source du projet **LogMonitor**. Il est destiné aux développeurs, auditeurs de sécurité ou universitaires souhaitant comprendre le fonctionnement intime du système, de la collecte des logs jusqu'à l'affichage Web.

---

## 🏗️ 1. Architecture Globale

LogMonitor est un **HIDS (Host-based Intrusion Detection System)** léger écrit en Python. Son architecture s'articule autour de 3 processus majeurs isolés :

1. **Le Démon (Daemon)** : Processus en arrière-plan (système) qui aspire les logs en continu via des *collecteurs*, les filtre via des *normaliseurs*, et les envoie au *détecteur*.
2. **La Base de Données (Storage)** : Un système SQLite local qui enregistre les événements purs (Logs) et les événements de sécurité (Alertes) de manière persistante.
3. **Le Serveur Web (Dashboard)** : Une application Flask (front-end HTML/JS) qui se connecte à la même base SQLite pour afficher les statistiques en temps réel.

---

## 📦 2. Analyse Module par Module (`logmonitor/`)

### 2.1 📥 Le Collecteur (`core/collector.py`)
**Rôle :** C'est les "oreilles" de LogMonitor. Son but est de lire de la donnée brute depuis la machine cible.
**Fonctionnement interne :**
* Le collecteur mère `LogCollector` gère les **fichiers textes plats classiques** (ex: `/var/log/auth.log`). Il effectue une rotation via `watchdog` pour réagir instantanément quand une ligne est écrite dans le fichier.
* **Le cas complexe :** `JournaldCollector`. Sur les systèmes Linux modernes (Lubuntu, Kali, Ubuntu >= 24.04), les logs ne sont plus dans de simples fichiers textes. Ils sont encapsulés dans le binaire `systemd-journald`. Ce module ouvre un sous-processus `subprocess.Popen` qui lance la commande :
  ```bash
  journalctl -f -o short-iso --no-pager
  ```
  L'astuce est qu'il utilise `.stdout.readline()` en boucle invisible (`iter(...)`) pour capturer chaque nouvelle ligne (Stream) de la machine hôte **à la seconde près** sans créer de *Deadlock* de mémoire.

### 2.2 🧩 Le Normaliseur (`core/normalizer.py`)
**Rôle :** C'est le "traducteur". Les logs de Linux sont un chaos de texte non formaté. Le normaliseur reçoit des Strings et recrache des dictionnaires JSON structurés.
**Fonctionnement interne :**
1. Il existe deux types de normaliseurs : `AuthLogNormalizer` (Syslog classique) et `JournaldNormalizer` (Linux moderne).
2. Ils contiennent de lourdes expressions régulières (Regex), ex : `_PREFIX = r'^(.+?)\s+([a-zA-Z0-9_-]+)\s+([a-zA-Z0-9_\-\.]+)(?:\[\d+\])?:\s+'`. Cette ligne mathématique lit une phrase (ex: `"mars 03 22:34 l-standardpc sshd: Failed password"`) et l'explose en 3 cases : [Date], [Nom de PC], [Service].
3. `_extract_timestamp()` : C'est le bijou du code. LogMonitor est confronté à des horloges de toutes sortes. S'il lit `"mars 03"`, il remplace `"mars"` par `"Mar"` (traduction FR/EN à la volée) pour que le chronomètre Python puisse dater précisément l'événement.

### 2.3 🧠 Le Détecteur de Menaces (`core/detector.py` & `rules.py`)
**Rôle :** C'est le "cerveau" SOC. Il analyse le flux de JSON formaté et crie "Alerte !" si un schéma correspond à une attaque.
**Fonctionnement interne :**
* Le fichier `rules.py` contient des algorithmes (Règles). Chaque règle possède une logique métier et une Sévérité (LOW, MEDIUM, HIGH, CRITICAL).
* **BruteForceSSHRule :** Garde en mémoire (via un dictionnaire en cache) les IP qui échouent. Si une IP dépasse la variable `threshold=5` en moins de X minutes, la règle déclenche une alerte HIGH. L'IP est bannie du cache pour éviter les doublons.
* **ActivitySpikeRule :** Compte chaque interaction réseau envoyée par le Normalizer. S'il y a plus de 20 logs en une milliseconde (comme lors de notre attaque Flood avec 50 instances de `sshpass`), la moyenne explose et la règle gueule **CRITICAL**.
* **SensitiveFileModificationRule :** Vérifie le message normalisé. S'il y a "sudo" et "vim /etc/passwd", elle s'allume.

### 2.4 💾 Le Stockage (`storage/database.py`)
**Rôle :** C'est la "mémoire". Écrire dans un fichier `.txt` serait trop lent et ingérable pour la page Web.
**Fonctionnement interne :**
* Utilise la bibliothèque native `sqlite3`.
* Possède deux tables : `logs` (chaque ligne collectée, pour les stats de trafic) et `alerts` (chaque attaque interceptée par le cerveau).
* Implémente le pattern *Thread-Safe* : l'accès à SQLite depuis de multiples threads Python étant dangereux (erreur `database is locked`), le système utilise des `Lock()` (verrous) pour forcer une file d'attente lors de l'insertion de grosses attaques.

### 2.5 🌐 Le Tableau de Bord Web (`web/app.py`)
**Rôle :** C'est "l'interface graphique" pour que l'humain supervise le cerveau.
**Fonctionnement interne :**
* C'est un serveur `Flask` léger.
* **API REST :** Des routes comme `/api/alerts` qui exécutent des requêtes SQL ultra pures `SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50` puis renvoient le tableau en JSON au Javascript du navigateur web.
* **Connexion :** La route de login charge le fichier `config/credentials.yaml`. Le code a été patché pour traiter d'anciennes versions du YAML, éviter les erreurs 500, et assigner un Cookie de session sécurisé `admin`.
* **Génération PDF :** Le routeur fait aussi office d'export. La route `/api/reports/generate` va chercher `logmonitor/reporting/pdf_generator.py` qui fabrique "à la main" des tableaux PDF (avec le module tiers `reportlab`), y colle les alertes de la DB, et renvoie le fichier.

### 2.6 ⚙️ Le Processus Démon & Détection (`utils/daemon.py` et `linux_detect.py`)
**Rôle :** L'installateur autonome. 
**Fonctionnement interne :**
* Le fichier `linux_detect.py` est l'expert environnemental. Avant même que LogMonitor ne s'arrume, il lit `/etc/os-release` (pour savoir s'il est sous Kali, Ubuntu, ou Lubuntu). Ensuite, **il teste le système de fichier** : Si `/var/log/auth.log` est manquant mais que le socket Unix `/run/systemd/journal/socket` existe, il sait qu'il s'agit d'un Linux de dernière génération 100% journald.
* `daemon.py` rassemble tout le monde : Il crée une file d'attente (Queue), assemble le collector approprié (dépisté par `linux_detect.py`) avec le normalizer de la même nature, attache le détecteur, puis lance un Thread (`threading.Thread`) global d'aspiration qui ne mourra jamais tant que la machine vit.

---

## 🎯 Conclusion Globale

LogMonitor est un programme redoutable par sa solidité multi-plateforme. Son atout principal réside dans **sa boucle de découplage total** : 
`Source (OS)` -> `[Collector]` -> `String brute` -> `[Normalizer]` -> `Objet Event pur` -> `[Detector]` -> `Alerte Métier` -> `[Database]`.

L'ajout ou le remplacement du fonctionnement réseau sur Kali Linux ou Lubuntu affecte **uniquement** les Collector/Normalizer initiaux. Le Cerveau (`Detector`) et le Web restent indifférents, offrant une maintenance future du code enfantine et sans cassure (Crash-Proof).
