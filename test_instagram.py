#!/usr/bin/env python3
"""Script de test pour le scraper Instagram"""
import logging
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from scraper.instagram_scraper import InstagramScraper

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_scraper():
    """Tester le scraper Instagram avec les créateurs de cosplay"""
    logger.info("=" * 60)
    logger.info("TEST DU SCRAPER INSTAGRAM - BOT COSPLAY")
    logger.info("=" * 60)

    # Créer la configuration
    config = Config()
    config.create_folders()

    logger.info(f"Créateurs à scraper: {config.INSTAGRAM_CREATORS}")
    logger.info(f"Proxies configurés: {len(config.INSTAGRAM_PROXIES)}")
    logger.info(f"Session file: {config.INSTAGRAM_SESSION_FILE}")

    # Créer le scraper
    scraper = InstagramScraper(config)

    # Tester avec UN SEUL créateur pour commencer
    test_creator = config.INSTAGRAM_CREATORS[0]
    logger.info(f"\nTest avec le créateur: @{test_creator}")
    logger.info("Récupération de 3 vidéos max pour le test...")

    try:
        videos = scraper.get_user_videos(test_creator, count=3)

        logger.info(f"\n{'=' * 60}")
        logger.info(f"RÉSULTATS DU TEST")
        logger.info(f"{'=' * 60}")
        logger.info(f"Vidéos récupérées: {len(videos)}")

        if videos:
            logger.info("\nDétails des vidéos:")
            for i, video in enumerate(videos, 1):
                logger.info(f"\n[{i}] ID: {video['id']}")
                logger.info(f"    Auteur: @{video['author']}")
                logger.info(f"    Likes: {video['likes']:,}")
                logger.info(f"    Vues: {video['views']:,}")
                logger.info(f"    Commentaires: {video['comments']:,}")
                logger.info(f"    Engagement: {video['engagement_rate']:.2%}")
                logger.info(f"    Description: {video['desc'][:100]}...")
                logger.info(f"    Fichier local: {video.get('local_path', 'N/A')}")

                # Vérifier que le fichier existe
                local_path = video.get('local_path')
                if local_path:
                    file_path = Path(local_path)
                    if file_path.exists():
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        logger.info(f"    ✓ Fichier vérifié: {size_mb:.2f} MB")
                    else:
                        logger.warning(f"    ⚠️  Fichier introuvable!")

            logger.info(f"\n{'=' * 60}")
            logger.info("✓ TEST RÉUSSI!")
            logger.info(f"{'=' * 60}")
            return True
        else:
            logger.warning(f"\n{'=' * 60}")
            logger.warning("⚠️  AUCUNE VIDÉO RÉCUPÉRÉE")
            logger.warning(f"{'=' * 60}")
            return False

    except Exception as e:
        logger.error(f"\n{'=' * 60}")
        logger.error(f"❌ ERREUR LORS DU TEST: {e}")
        logger.error(f"{'=' * 60}")
        logger.debug("Détails:", exc_info=True)
        return False
    finally:
        scraper.close()

if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)
