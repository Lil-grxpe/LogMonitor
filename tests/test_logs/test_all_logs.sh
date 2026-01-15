#!/bin/bash
# Script de test pour valider les 6 fichiers de logs de test
# Auteur: Équipe LogMonitor
# Date: 2026-01-02

set -e

echo "=================================================="
echo "  Test des Fichiers de Logs - LogMonitor"
echo "=================================================="
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire des logs de test
TEST_LOGS_DIR="tests/test_logs"

# Vérifier que l'environnement virtuel est activé
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Erreur: L'environnement virtuel n'est pas activé${NC}"
    echo "Exécutez: source venv/bin/activate"
    exit 1
fi

# Vérifier que logmonitor est installé
if ! command -v logmonitor &> /dev/null; then
    echo -e "${RED}❌ Erreur: logmonitor n'est pas installé${NC}"
    echo "Exécutez: pip install -e ."
    exit 1
fi

echo -e "${GREEN}✅ Environnement validé${NC}"
echo ""

# Liste des fichiers de test
declare -a TEST_FILES=(
    "01_bruteforce_ssh.log"
    "02_multiple_accounts_attack.log"
    "03_suspicious_root_login.log"
    "04_sensitive_file_modification.log"
    "05_activity_spike.log"
    "06_normal_activity.log"
)

declare -a TEST_NAMES=(
    "Bruteforce SSH"
    "Attaque sur Plusieurs Comptes"
    "Connexions Root Suspectes"
    "Modification de Fichiers Sensibles"
    "Pic d'Activité Inhabituel"
    "Activité Normale (pas d'alertes)"
)

# Compteurs
TOTAL_TESTS=6
PASSED_TESTS=0
FAILED_TESTS=0

# Tester chaque fichier
for i in "${!TEST_FILES[@]}"; do
    FILE="${TEST_FILES[$i]}"
    NAME="${TEST_NAMES[$i]}"
    FILEPATH="$TEST_LOGS_DIR/$FILE"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test $((i+1))/$TOTAL_TESTS: $NAME${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Vérifier que le fichier existe
    if [ ! -f "$FILEPATH" ]; then
        echo -e "${RED}❌ Fichier non trouvé: $FILEPATH${NC}"
        ((FAILED_TESTS++))
        echo ""
        continue
    fi
    
    # Afficher les statistiques du fichier
    LINE_COUNT=$(wc -l < "$FILEPATH")
    FILE_SIZE=$(du -h "$FILEPATH" | cut -f1)
    echo -e "📄 Fichier: ${GREEN}$FILE${NC}"
    echo -e "📊 Lignes: ${GREEN}$LINE_COUNT${NC}"
    echo -e "💾 Taille: ${GREEN}$FILE_SIZE${NC}"
    echo ""
    
    # Scanner le fichier avec logmonitor
    echo -e "${YELLOW}🔍 Scan en cours...${NC}"
    if logmonitor scan "$FILEPATH" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Scan réussi${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ Échec du scan${NC}"
        ((FAILED_TESTS++))
    fi
    
    echo ""
done

# Résumé final
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📊 RÉSUMÉ DES TESTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Total: $TOTAL_TESTS tests"
echo -e "${GREEN}✅ Réussis: $PASSED_TESTS${NC}"
echo -e "${RED}❌ Échoués: $FAILED_TESTS${NC}"
echo ""

# Afficher les alertes générées
echo -e "${YELLOW}🚨 Alertes générées:${NC}"
echo ""
logmonitor alerts list 2>/dev/null || echo -e "${YELLOW}⚠️  Aucune alerte ou commande non disponible${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Code de sortie
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ TOUS LES TESTS ONT RÉUSSI !${NC}"
    exit 0
else
    echo -e "${RED}❌ CERTAINS TESTS ONT ÉCHOUÉ${NC}"
    exit 1
fi
