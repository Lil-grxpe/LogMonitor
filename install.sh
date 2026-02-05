#!/bin/bash

set -e

INSTALL_DIR=$(pwd)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "============================================="
echo "   LogMonitor v0.1.0 - Installation Systeme"
echo "============================================="
echo ""

echo -e "${BLUE}[*]${NC} Verification de Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[-]${NC} Python 3 n'est pas installe"
    echo "    Installez Python 3.10+ et relancez ce script"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}[+]${NC} Python $PYTHON_VERSION detecte"

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)
echo -e "${BLUE}[*]${NC} Distribution detectee: $DISTRO"

echo -e "${BLUE}[*]${NC} Verification de pipx..."
if ! command -v pipx &> /dev/null; then
    echo -e "${YELLOW}[!]${NC} pipx n'est pas installe"
    echo -e "${BLUE}[*]${NC} Installation de pipx..."
    
    case $DISTRO in
        debian|ubuntu|kali|linuxmint|pop)
            sudo apt update -qq
            sudo apt install -y pipx
            ;;
        fedora)
            sudo dnf install -y pipx
            ;;
        rhel|centos|rocky|almalinux)
            sudo dnf install -y python3-pip
            python3 -m pip install --user pipx
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm python-pipx
            ;;
        opensuse*|suse*)
            sudo zypper install -y python3-pipx
            ;;
        *)
            echo -e "${YELLOW}[!]${NC} Distribution non reconnue, installation via pip"
            python3 -m pip install --user pipx
            ;;
    esac
    
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}[+]${NC} pipx installe"
else
    echo -e "${GREEN}[+]${NC} pipx deja installe"
fi

echo -e "${BLUE}[*]${NC} Installation de LogMonitor..."

if [ -f "$HOME/.local/bin/logmonitor" ]; then
    rm -f "$HOME/.local/bin/logmonitor"
fi

if pipx list 2>/dev/null | grep -q logmonitor; then
    pipx uninstall logmonitor 2>/dev/null || true
fi

pipx install -e "$INSTALL_DIR"
echo -e "${GREEN}[+]${NC} LogMonitor installe"

echo -e "${BLUE}[*]${NC} Creation des repertoires..."
mkdir -p data/evidence
mkdir -p reports
mkdir -p /tmp/logmonitor
echo -e "${GREEN}[+]${NC} Repertoires crees"

if [ ! -f "config/credentials.yaml" ] && [ -f "config/credentials.yaml.template" ]; then
    cp config/credentials.yaml.template config/credentials.yaml
    echo -e "${GREEN}[+]${NC} Fichier credentials.yaml cree"
fi

echo ""
echo -e "${BLUE}[*]${NC} Configuration du fichier de logs"

case $DISTRO in
    debian|ubuntu|kali|linuxmint|pop)
        DEFAULT_LOG="/var/log/auth.log"
        ;;
    fedora|rhel|centos|rocky|almalinux)
        DEFAULT_LOG="/var/log/secure"
        ;;
    arch|manjaro|endeavouros|opensuse*)
        DEFAULT_LOG="/var/log/auth.log"
        ;;
    *)
        DEFAULT_LOG="/var/log/auth.log"
        ;;
esac

read -p "    Chemin du fichier (defaut: $DEFAULT_LOG): " LOG_PATH
LOG_PATH=${LOG_PATH:-$DEFAULT_LOG}

if [ ! -f "$LOG_PATH" ]; then
    echo -e "${YELLOW}[!]${NC} Le fichier $LOG_PATH n'existe pas"
    echo "    Verifiez le chemin dans config/logmonitor.yaml"
fi

CONFIG_FILE="config/logmonitor.yaml"
if [ -f "$CONFIG_FILE" ]; then
    ESCAPED_PATH=$(echo "$LOG_PATH" | sed 's/\//\\\//g')
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    sed -i "s/^\s*-\s*\/var\/log\/auth.log.*/    - $ESCAPED_PATH/" "$CONFIG_FILE"
    sed -i "s/^\s*-\s*\/var\/log\/secure.*/    - $ESCAPED_PATH/" "$CONFIG_FILE"
    echo -e "${GREEN}[+]${NC} Configuration mise a jour: $LOG_PATH"
fi

echo ""
echo -e "${BLUE}[*]${NC} Verification du PATH..."
if [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo -e "${GREEN}[+]${NC} PATH configure correctement"
else
    if [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo -e "${GREEN}[+]${NC} PATH ajoute a ~/.zshrc"
    fi
    if [ -f "$HOME/.bashrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${GREEN}[+]${NC} PATH ajoute a ~/.bashrc"
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

echo -e "${BLUE}[*]${NC} Validation..."
if logmonitor config-validate > /dev/null 2>&1; then
    echo -e "${GREEN}[+]${NC} Configuration valide"
else
    echo -e "${YELLOW}[!]${NC} Verifiez config/logmonitor.yaml"
fi

if [ -r "$LOG_PATH" ]; then
    echo -e "${GREEN}[+]${NC} Acces au fichier de logs OK"
else
    echo -e "${YELLOW}[!]${NC} Pas d'acces a $LOG_PATH"
    echo "    Ajoutez votre utilisateur au groupe 'adm':"
    echo "    sudo usermod -a -G adm \$USER"
fi

echo ""
echo "============================================="
echo "   Installation terminee"
echo "============================================="
echo ""
echo "Commandes disponibles:"
echo "  logmonitor --version"
echo "  logmonitor config-validate"
echo "  logmonitor start"
echo "  logmonitor web --daemon"
echo ""
echo "Dashboard: http://127.0.0.1:5000"
echo "Identifiants: admin / admin"
echo ""
