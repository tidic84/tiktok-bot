#!/bin/bash
# Script rapide de vérification IP et test TikTok

echo "════════════════════════════════════════════════════════════"
echo "  🔍 VÉRIFICATION IP ET TEST TIKTOK"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "📍 Votre IP actuelle:"
curl -s ifconfig.me
echo -e "\n"

echo "🧪 Test du scraper TikTok..."
echo ""

source venv/bin/activate 2>/dev/null
timeout 60 python debug_scraper.py 2>&1 | grep -E "(✓|✅|❌|ERROR|vidéos)" | head -20

echo ""
echo "════════════════════════════════════════════════════════════"
