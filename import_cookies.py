#!/usr/bin/env python3
"""
Script pour importer des cookies TikTok depuis un fichier JSON

Usage:
    python import_cookies.py cookies.json
    ou
    python import_cookies.py  # utilise tiktok_cookies.json par défaut
"""
import sys
import logging
from pathlib import Path
from uploader.cookie_manager import CookieManager
from config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal"""
    
    logger.info("=" * 60)
    logger.info("IMPORT DE COOKIES TIKTOK DEPUIS JSON")
    logger.info("=" * 60)
    
    # Récupérer le fichier JSON depuis les arguments
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "tiktok_cookies.json"
    
    json_path = Path(json_file)
    
    # Vérifier que le fichier existe
    if not json_path.exists():
        logger.error(f"❌ Fichier non trouvé: {json_file}")
        logger.info("\nUsage:")
        logger.info("  python import_cookies.py <fichier_cookies.json>")
        logger.info("\nExemple:")
        logger.info("  python import_cookies.py tiktok_cookies.json")
        sys.exit(1)
    
    logger.info(f"Fichier JSON: {json_file}")
    
    # Initialiser la configuration
    config = Config()
    
    # Créer le gestionnaire de cookies
    cookie_manager = CookieManager(config.COOKIES_FILE)
    
    # Importer les cookies
    logger.info(f"\nImport des cookies depuis {json_file}...")
    success = cookie_manager.import_cookies_from_json(str(json_path))
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ IMPORT RÉUSSI !")
        logger.info("=" * 60)
        logger.info(f"\nLes cookies ont été importés et sauvegardés dans:")
        logger.info(f"  • {config.COOKIES_FILE} (pickle)")
        logger.info(f"  • {config.COOKIES_FILE.replace('.pkl', '.json')} (JSON backup)")
        logger.info("\nVous pouvez maintenant lancer le bot:")
        logger.info("  python main.py")
        logger.info("\nLe bot utilisera automatiquement ces cookies pour se connecter.")
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ ÉCHEC DE L'IMPORT")
        logger.error("=" * 60)
        logger.error("\nVérifiez que:")
        logger.error("  • Le fichier JSON est valide")
        logger.error("  • Le format des cookies est correct")
        logger.error("  • Les cookies ne sont pas expirés")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Import interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Erreur: {e}", exc_info=True)
        sys.exit(1)

