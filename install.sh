#!/bin/bash
# Script d'installation automatique de LogMonitor
# Ce script installe LogMonitor en mode utilisateur (sans root)

set -e

echo "═══════════════════════════════════════════════════════"
echo "   Installation de LogMonitor v0.1.0"
echo "═══════════════════════════════════════════════════════"
echo ""

# Variables
INSTALL_DIR=$(pwd)
VENV_DIR="$INSTALL_DIR/venv"

# Vérifier Python 3.10+
echo "[*] Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 n'est pas installé"
    echo "   Installez Python 3.10+ et relancez ce script"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "[+] Python $PYTHON_VERSION détecté"

# Créer l'environnement virtuel
if [ -d "$VENV_DIR" ]; then
    echo "[!] Environnement virtuel existant trouvé"
    read -p "   Voulez-vous le recréer ? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        echo "[-] Suppression de l'ancien venv..."
        rm -rf "$VENV_DIR"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Création de l'environnement virtuel..."
    python3 -m venv venv
    echo "[+] Environnement virtuel créé"
fi

# Activer l'environnement
echo "[*] Activation de l'environnement..."
source venv/bin/activate

# Mettre à jour pip
echo "[*] Mise à jour de pip..."
pip install --upgrade pip -q

# Installer les dépendances
echo "[*] Installation des dépendances..."
pip install -r requirements.txt -q
echo "[+] Dépendances installées"

# Installer LogMonitor
echo "[*] Installation de LogMonitor..."
pip install -e . -q
echo "[+] LogMonitor installé"

# Créer les répertoires nécessaires
echo "[*] Création des répertoires..."
mkdir -p data/evidence
mkdir -p reports
mkdir -p /tmp/logmonitor
echo "[+] Répertoires créés"

# Configuration des credentials
if [ ! -f "config/credentials.yaml" ] && [ -f "config/credentials.yaml.template" ]; then
    echo "[*] Initialisation de config/credentials.yaml..."
    cp config/credentials.yaml.template config/credentials.yaml
    echo "[+] Fichier credentials.yaml créé à partir du modèle"
fi


# Configuration du fichier de log
echo ""
echo "[*] Configuration du fichier de logs a surveiller"
read -p "   Entrez le chemin complet du fichier (defaut: /var/log/auth.log): " LOG_PATH
LOG_PATH=${LOG_PATH:-/var/log/auth.log}

if [ ! -f "$LOG_PATH" ]; then
    echo "[!] Attention: Le fichier $LOG_PATH n'existe pas."
    echo "    Assurez-vous de creer ce fichier ou de corriger le chemin dans config/logmonitor.yaml"
fi

# Mettre a jour la configuration
CONFIG_FILE="config/logmonitor.yaml"
if [ -f "$CONFIG_FILE" ]; then
    # Echapper les slashs pour sed
    ESCAPED_PATH=$(echo "$LOG_PATH" | sed 's/\//\\\//g')
    # Backup
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    # Remplacer la ligne contenant /var/log/auth.log
    sed -i "s/^\s*-\s*\/var\/log\/auth.log.*/    - $ESCAPED_PATH/" "$CONFIG_FILE"
    echo "[+] Configuration mise a jour avec: $LOG_PATH"
else
    echo "[!] Fichier de configuration non trouve: $CONFIG_FILE"
fi

# Valider la configuration
echo "[*] Validation de la configuration..."
if logmonitor config validate > /dev/null 2>&1; then
    echo "[+] Configuration valide"
else
    echo "[!] Problème de configuration (vérifiez config/logmonitor.yaml)"
fi

# Vérifier les permissions pour les logs
echo "[*] Vérification des permissions..."
if [ -r "$LOG_PATH" ]; then
    echo "[+] Accès en lecture à $LOG_PATH"
else
    echo "[!] Pas d'accès à $LOG_PATH"
    echo "   Ajoutez votre utilisateur au groupe 'adm' ou au groupe propriétaire du fichier:"
    echo "   sudo usermod -a -G adm $USER"
    echo "   Puis reconnectez-vous ou exécutez: newgrp adm"
fi

# Afficher le résumé
echo ""
echo "═══════════════════════════════════════════════════════"
echo "   [+] Installation terminée !"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "[*] Pour utiliser LogMonitor :"
echo "   1. Activez l'environnement : source venv/bin/activate"
echo "   2. Testez : logmonitor --version"
echo "   3. Validez : logmonitor config validate"
echo "   4. Lancez : logmonitor start"
echo ""
echo "[*] Documentation :"
echo "   - Guide d'installation : docs/installation.md"
echo "   - Guide daemon : docs/daemon_guide.md"
echo "   - README : README.md"
echo ""
echo "[*] Dashboard web : logmonitor web --daemon"
echo "[*] Statut : logmonitor status"
echo ""
