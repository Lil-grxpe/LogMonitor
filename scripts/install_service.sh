#!/bin/bash
# Script d'installation de LogMonitor comme service Linux
# Conforme au cahier des charges

set -e

echo "=== Installation de LogMonitor comme service Linux ==="

# Vérifier que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo "[-] Ce script doit être exécuté en tant que root (sudo)"
    exit 1
fi

# Variables
INSTALL_DIR="/opt/logmonitor"
SERVICE_FILE="/etc/systemd/system/logmonitor.service"
LOG_DIR="/var/log/logmonitor"
USER="logmonitor"
GROUP="logmonitor"

echo "[*] Création de l'utilisateur système logmonitor..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER"
    echo "[+] Utilisateur $USER créé"
else
    echo "[!] Utilisateur $USER existe déjà"
fi

echo "[*] Création des répertoires..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$INSTALL_DIR/data/evidence"
mkdir -p "$INSTALL_DIR/reports"
mkdir -p "$INSTALL_DIR/config"

echo "[*] Copie des fichiers du projet..."
cp -r logmonitor "$INSTALL_DIR/"
cp -r config/* "$INSTALL_DIR/config/"
cp requirements.txt "$INSTALL_DIR/"
cp setup.py "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/"

echo "[*] Configuration de l'environnement Python..."
cd "$INSTALL_DIR"

# Créer l'environnement virtuel
python3 -m venv venv

# Activer et installer les dépendances
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
deactivate

echo "[*] Configuration des permissions..."
# Ajouter l'utilisateur logmonitor au groupe adm pour lire les logs
usermod -a -G adm "$USER"

# Définir les propriétaires
chown -R "$USER:$GROUP" "$INSTALL_DIR"
chown -R "$USER:$GROUP" "$LOG_DIR"

# Permissions strictes
chmod 750 "$INSTALL_DIR"
chmod 750 "$LOG_DIR"

echo "[*] Installation du service systemd..."
cp "$INSTALL_DIR/../logmonitor.service" "$SERVICE_FILE" 2>/dev/null || \
    cp logmonitor.service "$SERVICE_FILE"

# Recharger systemd
systemctl daemon-reload

echo "[+] Installation terminée !"
echo ""
echo "Pour démarrer LogMonitor :"
echo "  sudo systemctl start logmonitor"
echo ""
echo "Pour activer au démarrage :"
echo "  sudo systemctl enable logmonitor"
echo ""
echo "Pour vérifier le statut :"
echo "  sudo systemctl status logmonitor"
echo ""
echo "Pour voir les logs :"
echo "  sudo journalctl -u logmonitor -f"
