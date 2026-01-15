#!/bin/bash
# Script d'export des logs systemd pour LogMonitor sur Kali Linux
# Auteur: Equipe LogMonitor
# Date: 2026-01-02

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Export des logs systemd pour LogMonitor${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Repertoire de sortie
OUTPUT_DIR="${1:-/tmp/logmonitor_exports}"
PERIOD="${2:-24 hours ago}"

echo -e "${YELLOW}[*] Repertoire de sortie:${NC} $OUTPUT_DIR"
echo -e "${YELLOW}[*] Periode:${NC} depuis $PERIOD"
echo ""

# Creer le repertoire si necessaire
mkdir -p "$OUTPUT_DIR"

# Fonction pour exporter un service
export_service() {
    local service=$1
    local output_file=$2
    local description=$3
    
    echo -n "[*] Export $description... "
    
    if journalctl -u "$service" --since "$PERIOD" --no-pager > "$output_file" 2>/dev/null; then
        local line_count=$(wc -l < "$output_file")
        if [ "$line_count" -gt 0 ]; then
            echo -e "${GREEN}[+]${NC} ($line_count lignes)"
        else
            echo -e "${YELLOW}[!]${NC} (aucune donnee)"
        fi
    else
        echo -e "${RED}[-]${NC} (service non disponible)"
        return 1
    fi
}

# Fonction pour exporter par identifiant
export_identifier() {
    local identifier=$1
    local output_file=$2
    local description=$3
    
    echo -n "[*] Export $description... "
    
    if journalctl -t "$identifier" --since "$PERIOD" --no-pager > "$output_file" 2>/dev/null; then
        local line_count=$(wc -l < "$output_file")
        if [ "$line_count" -gt 0 ]; then
            echo -e "${GREEN}[+]${NC} ($line_count lignes)"
        else
            echo -e "${YELLOW}[!]${NC} (aucune donnee)"
        fi
    else
        echo -e "${RED}[-]${NC} (identifiant non trouve)"
        return 1
    fi
}

# Export des differents services
echo -e "${YELLOW}[*] Export des logs...${NC}"
echo ""

# SSH
export_service "ssh" "$OUTPUT_DIR/ssh.log" "SSH"

# SSHD (alternative)
export_service "sshd" "$OUTPUT_DIR/sshd.log" "SSHD"

# Sudo
export_identifier "sudo" "$OUTPUT_DIR/sudo.log" "Sudo"

# Authentification systeme
export_service "systemd-logind" "$OUTPUT_DIR/auth.log" "Authentification"

# Apache (si disponible)
if systemctl is-active --quiet apache2 2>/dev/null; then
    export_service "apache2" "$OUTPUT_DIR/apache2.log" "Apache2"
fi

# Nginx (si disponible)
if systemctl is-active --quiet nginx 2>/dev/null; then
    export_service "nginx" "$OUTPUT_DIR/nginx.log" "Nginx"
fi

# MySQL (si disponible)
if systemctl is-active --quiet mysql 2>/dev/null; then
    export_service "mysql" "$OUTPUT_DIR/mysql.log" "MySQL"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}[+] Export termine !${NC}"
echo ""

# Afficher le resume
echo -e "${YELLOW}[*] Resume des fichiers exportes:${NC}"
echo ""

total_size=0
for file in "$OUTPUT_DIR"/*.log; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        lines=$(wc -l < "$file")
        filename=$(basename "$file")
        
        if [ "$lines" -gt 0 ]; then
            echo -e "  ${GREEN}[+]${NC} $filename - $size ($lines lignes)"
            total_size=$((total_size + $(stat -c%s "$file")))
        fi
    fi
done

echo ""
total_size_human=$(numfmt --to=iec-i --suffix=B $total_size 2>/dev/null || echo "$total_size bytes")
echo -e "${YELLOW}[*] Taille totale:${NC} $total_size_human"
echo ""

# Suggestions
echo -e "${YELLOW}[*] Prochaines etapes:${NC}"
echo ""
echo "  # Analyser les logs exportes"
echo "  logmonitor scan $OUTPUT_DIR/ssh.log"
echo ""
echo "  # Analyser tous les fichiers"
echo "  for log in $OUTPUT_DIR/*.log; do logmonitor scan \"\$log\"; done"
echo ""
echo "  # Voir les alertes"
echo "  logmonitor alerts list"
echo ""
echo "  # Lancer le dashboard"
echo "  logmonitor web --port 5000"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
