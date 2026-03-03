# 1. Introduction à LogMonitor

## Qu'est-ce que LogMonitor ?

**LogMonitor** est un outil de surveillance et d'analyse de sécurité pour les systèmes Linux. Il détecte automatiquement le système de journalisation de votre distribution (fichiers `/var/log/auth.log`, `/var/log/syslog` ou **journald** via `journalctl`) et analyse les événements de sécurité en temps réel.

Contrairement aux solutions complexes comme Splunk ou ELK, LogMonitor est **léger**, **local** (pas d'envoi de données vers le cloud) et s'installe en quelques minutes.

## Fonctionnalités Principales

*   **🕵️ Détection en Temps Réel** : Analyse les logs dès qu'ils sont écrits pour identifier les menaces immédiatement (mode Daemon).
*   **🛡️ Règles de Sécurité** : Détecte nativement :
    *   Attaques par force brute (SSH).
    *   Tentatives de connexion Root.
    *   Utilisation de comptes multiples suspects.
    *   Accès à des fichiers sensibles (ex: `/etc/shadow`).
    *   Pics d'activité anormaux.
*   **📊 Tableau de Bord Web** : Interface simple pour visualiser les statistiques, les IPs suspectes et l'historique des alertes.
*   **📄 Rapports Automatisés** : Génération de rapports d'incidents au format PDF ou CSV pour l'archivage ou l'audit.
*   **🔒 Respect de la Vie Privée** : Toutes les données sont stockées localement dans une base de données SQLite optimisée.

## Pourquoi utiliser LogMonitor ?

C'est l'outil idéal pour les administrateurs système, les étudiants en cybersécurité ou toute personne souhaitant sécuriser un serveur Linux personnel (VPS, Raspberry Pi) sans complexité excessive.

[Suivant : Installation >](./02_Installation.md)
