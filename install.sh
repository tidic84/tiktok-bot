#!/bin/bash
# Script d'installation du Bot TikTok

echo "=========================================="
echo "Installation du Bot TikTok"
echo "=========================================="
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

echo "✓ Python 3 détecté: $(python3 --version)"

# Créer environnement virtuel
echo ""
echo "Création de l'environnement virtuel..."
python3 -m venv venv

# Activer environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer dépendances
echo ""
echo "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Installer Playwright
echo ""
echo "Installation de Playwright..."
playwright install chromium

# Créer fichier .env
if [ ! -f .env ]; then
    echo ""
    echo "Création du fichier .env..."
    cp .env.example .env
    echo "⚠️  N'oubliez pas de remplir vos identifiants dans le fichier .env"
else
    echo ""
    echo "✓ Le fichier .env existe déjà"
fi

# Créer dossiers nécessaires
echo ""
echo "Création des dossiers..."
mkdir -p downloaded_videos logs

echo ""
echo "=========================================="
echo "✓ Installation terminée !"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "1. Éditez le fichier .env avec vos identifiants TikTok"
echo "2. Lancez le bot avec: python main.py"
echo ""
echo "Pour activer l'environnement virtuel manuellement:"
echo "  source venv/bin/activate"
echo ""

