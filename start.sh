#!/bin/bash
# Script de démarrage du Bot TikTok

echo "=========================================="
echo "Démarrage du Bot TikTok"
echo "=========================================="
echo ""

# Vérifier que l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé"
    echo "Lancez d'abord: bash install.sh"
    exit 1
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier le fichier .env
if [ ! -f .env ]; then
    echo "❌ Fichier .env non trouvé"
    echo "Copiez .env.example vers .env et remplissez vos identifiants"
    exit 1
fi

# Lancer le bot
echo "Lancement du bot..."
echo ""
python main.py

