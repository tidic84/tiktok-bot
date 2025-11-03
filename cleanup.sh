#!/bin/bash
# Script de nettoyage complet des processus et cache

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║                  🧹 NETTOYAGE COMPLET DU BOT                         ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "1. Arrêt du bot..."
pkill -f "python.*main.py" 2>/dev/null && echo "   ✓ Bot arrêté" || echo "   - Bot n'était pas actif"

echo ""
echo "2. Nettoyage des processus Playwright/Chromium..."
BEFORE=$(ps aux | grep -E "(playwright|chromium)" | grep -v grep | wc -l)
pkill -9 -f playwright 2>/dev/null
pkill -9 -f chromium 2>/dev/null
sleep 2
AFTER=$(ps aux | grep -E "(playwright|chromium)" | grep -v grep | wc -l)
echo "   ✓ $BEFORE processus tués"

echo ""
echo "3. Nettoyage du cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
echo "   ✓ Cache Python nettoyé"

echo ""
echo "4. (Optionnel) Nettoyage du cache Playwright..."
read -p "   Voulez-vous nettoyer le cache Playwright? (o/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    rm -rf ~/.cache/ms-playwright/ 2>/dev/null
    echo "   ✓ Cache Playwright supprimé"
    echo "   ⚠  Relancez: playwright install chromium"
else
    echo "   - Cache Playwright conservé"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✅ NETTOYAGE TERMINÉ"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Vous pouvez maintenant relancer le bot:"
echo "  python main.py"
echo ""


