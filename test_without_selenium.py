"""Test du scraper SANS lancer Selenium pour isoler le problème"""
import asyncio
import logging
from config import Config
from scraper.tiktok_scraper import TikTokScraper
from scraper.video_filter import VideoFilter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test():
    print("=" * 70)
    print("TEST SCRAPER SEUL (sans Selenium)")
    print("=" * 70)
    
    config = Config()
    scraper = TikTokScraper(config)
    filter_obj = VideoFilter(config)
    
    # Initialiser le scraper
    print("\n1. Initialisation du scraper...")
    await scraper.initialize()
    print("✓ Scraper initialisé")
    
    # Récupérer des vidéos
    print("\n2. Récupération de 10 vidéos trending...")
    videos = await scraper.get_trending_videos(count=10)
    print(f"✓ {len(videos)} vidéos récupérées")
    
    # Filtrer
    if videos:
        quality = filter_obj.filter_videos(videos)
        print(f"✓ {len(quality)} vidéos de qualité")
        
        if quality:
            v = quality[0]
            print(f"\nExemple: {v['views']:,} vues, {v['likes']:,} likes")
    
    # Fermer
    await scraper.close()
    print("\n✓ Test réussi !")

if __name__ == "__main__":
    asyncio.run(test())


