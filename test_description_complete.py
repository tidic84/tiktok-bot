#!/usr/bin/env python3
"""
Script de test pour vérifier que les descriptions sont récupérées en entier
"""
import asyncio
import logging
from config import Config
from scraper.url_scraper import URLScraper

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_description_recovery():
    """Tester la récupération complète des descriptions"""
    
    logger.info("=" * 60)
    logger.info("TEST DE RÉCUPÉRATION DES DESCRIPTIONS COMPLÈTES")
    logger.info("=" * 60)
    
    # Initialiser la configuration
    config = Config()
    
    # Utiliser le scraper URL (plus fiable)
    scraper = URLScraper(config)
    
    # Tester avec les créateurs configurés
    logger.info(f"\nTest avec les créateurs: {', '.join(config.TARGET_CREATORS[:2])}")
    logger.info("Récupération de 3 vidéos par créateur...\n")
    
    videos = scraper.get_videos_from_creators(
        config.TARGET_CREATORS[:2],  # Prendre seulement les 2 premiers pour le test
        count_per_creator=3
    )
    
    if not videos:
        logger.error("❌ Aucune vidéo récupérée")
        return
    
    logger.info(f"\n✓ {len(videos)} vidéos récupérées\n")
    logger.info("=" * 60)
    logger.info("ANALYSE DES DESCRIPTIONS")
    logger.info("=" * 60)
    
    # Analyser chaque vidéo
    for i, video in enumerate(videos, 1):
        description = video.get('desc', '')
        
        logger.info(f"\n--- Vidéo {i}/{len(videos)} ---")
        logger.info(f"ID: {video.get('id', 'N/A')}")
        logger.info(f"Auteur: @{video.get('author', 'N/A')}")
        logger.info(f"Likes: {video.get('likes', 0):,}")
        logger.info(f"Vues: {video.get('views', 0):,}")
        logger.info(f"\n📝 Description ({len(description)} caractères):")
        logger.info(f"{description}")
        
        # Compter les hashtags
        hashtags = [word for word in description.split() if word.startswith('#')]
        logger.info(f"\n🏷️  Hashtags trouvés ({len(hashtags)}): {' '.join(hashtags)}")
        
        # Vérifications
        if len(description) == 0:
            logger.warning("⚠️  Description vide!")
        elif len(description) < 10:
            logger.warning("⚠️  Description très courte, possible troncature")
        else:
            logger.info("✅ Description semble complète")
    
    # Statistiques globales
    logger.info("\n" + "=" * 60)
    logger.info("STATISTIQUES GLOBALES")
    logger.info("=" * 60)
    
    total_chars = sum(len(v.get('desc', '')) for v in videos)
    avg_chars = total_chars / len(videos) if videos else 0
    total_hashtags = sum(
        len([w for w in v.get('desc', '').split() if w.startswith('#')])
        for v in videos
    )
    avg_hashtags = total_hashtags / len(videos) if videos else 0
    
    logger.info(f"Nombre de vidéos: {len(videos)}")
    logger.info(f"Total de caractères: {total_chars:,}")
    logger.info(f"Moyenne par description: {avg_chars:.1f} caractères")
    logger.info(f"Total de hashtags: {total_hashtags}")
    logger.info(f"Moyenne par vidéo: {avg_hashtags:.1f} hashtags")
    
    # Vidéos sans description
    empty_desc = [v for v in videos if not v.get('desc', '').strip()]
    if empty_desc:
        logger.warning(f"\n⚠️  {len(empty_desc)} vidéo(s) sans description")
    else:
        logger.info("\n✅ Toutes les vidéos ont une description")
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST TERMINÉ")
    logger.info("=" * 60)
    
    # Afficher un exemple de ce qui serait uploadé
    if videos:
        example = videos[0]
        logger.info("\n📤 EXEMPLE D'UPLOAD")
        logger.info("=" * 60)
        logger.info(f"Vidéo: {example.get('id')}")
        logger.info(f"Description qui serait uploadée:")
        logger.info(f"{example.get('desc', '')}")
        logger.info("=" * 60)
        logger.info("\n✅ Cette description COMPLÈTE serait copiée sur TikTok")


def main():
    """Point d'entrée principal"""
    try:
        asyncio.run(test_description_recovery())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur durant le test: {e}", exc_info=True)


if __name__ == "__main__":
    main()

