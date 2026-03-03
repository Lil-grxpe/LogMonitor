#!/bin/bash

# =============================================
#   LogMonitor - Script de Désinstallation
# =============================================

set -e

INSTALL_DIR=$(pwd)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "============================================="
echo "   LogMonitor v0.1.0 - Désinstallation"
echo "============================================="
echo ""

# Confirmation
if [[ "$1" != "--force" ]]; then
    read -p "❓ Êtes-vous sûr de vouloir désinstaller LogMonitor ? [o/N] " CONFIRM
    case "$CONFIRM" in
        [oO]|[oO][uU][iI])
            echo ""
            ;;
        *)
            echo -e "${YELLOW}[!]${NC} Désinstallation annulée."
            exit 0
            ;;
    esac
fi

# ───────────────────────────────────────────────
# 1. Arrêt et suppression du service systemd
# ───────────────────────────────────────────────
echo -e "${BLUE}[*]${NC} Arrêt du service LogMonitor..."

if systemctl list-units --type=service 2>/dev/null | grep -q logmonitor; then
    sudo systemctl stop logmonitor 2>/dev/null || true
    sudo systemctl disable logmonitor 2>/dev/null || true
    echo -e "${GREEN}[+]${NC} Service systemd arrêté et désactivé"
else
    echo -e "${YELLOW}[!]${NC} Service systemd non trouvé (peut-être pas installé)"
fi

SERVICE_FILE="/etc/systemd/system/logmonitor.service"
if [ -f "$SERVICE_FILE" ]; then
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
    echo -e "${GREEN}[+]${NC} Fichier service supprimé : $SERVICE_FILE"
fi

# ───────────────────────────────────────────────
# 2. Arrêt du daemon si encore en cours
# ───────────────────────────────────────────────
echo -e "${BLUE}[*]${NC} Arrêt du daemon LogMonitor (si actif)..."

if command -v logmonitor &>/dev/null; then
    logmonitor stop 2>/dev/null || true
    echo -e "${GREEN}[+]${NC} Daemon arrêté"
fi

PID_FILE="/tmp/logmonitor/logmonitor.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo -e "${GREEN}[+]${NC} PID file supprimé"
fi

# ───────────────────────────────────────────────
# 3. Désinstallation via pipx
# ───────────────────────────────────────────────
echo -e "${BLUE}[*]${NC} Désinstallation du paquet LogMonitor (pipx)..."

if command -v pipx &>/dev/null; then
    if pipx list 2>/dev/null | grep -q logmonitor; then
        pipx uninstall logmonitor
        echo -e "${GREEN}[+]${NC} Package logmonitor supprimé via pipx"
    else
        echo -e "${YELLOW}[!]${NC} LogMonitor n'est pas installé via pipx"
    fi
else
    echo -e "${YELLOW}[!]${NC} pipx non trouvé — tentative de suppression manuelle..."
fi

# Suppression du binaire restant si persistant
BIN_PATH="$HOME/.local/bin/logmonitor"
if [ -f "$BIN_PATH" ]; then
    rm -f "$BIN_PATH"
    echo -e "${GREEN}[+]${NC} Binaire supprimé : $BIN_PATH"
fi

# ───────────────────────────────────────────────
# 4. Suppression des fichiers temporaires
# ───────────────────────────────────────────────
echo -e "${BLUE}[*]${NC} Suppression des fichiers temporaires..."

TMP_DIR="/tmp/logmonitor"
if [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
    echo -e "${GREEN}[+]${NC} Dossier temporaire supprimé : $TMP_DIR"
fi

# ───────────────────────────────────────────────
# 5. (Optionnel) Suppression des données
# ───────────────────────────────────────────────
echo ""
if [[ "$1" != "--force" ]]; then
    read -p "🗑️  Supprimer aussi les données (base de données, rapports, preuves) ? [o/N] " DEL_DATA
else
    DEL_DATA="n"
fi

case "$DEL_DATA" in
    [oO]|[oO][uU][iI])
        echo -e "${BLUE}[*]${NC} Suppression des données..."

        if [ -d "$INSTALL_DIR/data" ]; then
            rm -rf "$INSTALL_DIR/data"
            echo -e "${GREEN}[+]${NC} Dossier data/ supprimé"
        fi

        if [ -d "$INSTALL_DIR/reports" ]; then
            rm -rf "$INSTALL_DIR/reports"
            echo -e "${GREEN}[+]${NC} Dossier reports/ supprimé"
        fi

        if [ -f "$INSTALL_DIR/config/logmonitor.yaml.bak" ]; then
            rm -f "$INSTALL_DIR/config/logmonitor.yaml.bak"
            echo -e "${GREEN}[+]${NC} Backup de config supprimé"
        fi
        ;;
    *)
        echo -e "${YELLOW}[!]${NC} Données conservées dans : $INSTALL_DIR/data/ et $INSTALL_DIR/reports/"
        ;;
esac

# ───────────────────────────────────────────────
# 6. Suppression des entrées PATH (optionnel)
# ───────────────────────────────────────────────
for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC_FILE" ] && grep -q 'HOME/.local/bin' "$RC_FILE"; then
        echo -e "${YELLOW}[!]${NC} Note : La ligne PATH dans $RC_FILE n'a pas été supprimée"
        echo "    (elle peut être utilisée par d'autres outils pipx)"
    fi
done

# ───────────────────────────────────────────────
echo ""
echo "============================================="
echo "   ✅ Désinstallation terminée"
echo "============================================="
echo ""
echo -e "${YELLOW}[!]${NC} Pour supprimer complètement le code source :"
echo "    rm -rf \"$INSTALL_DIR\""
echo ""
echo -e "${YELLOW}[!]${NC} Pour réinstaller LogMonitor :"
echo "    bash install.sh"
echo ""
