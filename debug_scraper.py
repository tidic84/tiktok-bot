"""Script de debug pour tester le scraper TikTok"""
import asyncio
import sys
import logging

# Configuration du logging détaillé
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_tiktok_api():
    """Test de l'API TikTok"""
    print("=" * 70)
    print("TEST DU SCRAPER TIKTOK")
    print("=" * 70)
    
    try:
        # Test 1: Import des modules
        print("\n[1/5] Test des imports...")
        from config import Config
        from scraper.tiktok_scraper import TikTokScraper
        from scraper.video_filter import VideoFilter
        print("✓ Imports réussis")
        
        # Test 2: Création de la config
        print("\n[2/5] Test de la configuration...")
        config = Config()
        print(f"✓ Configuration chargée")
        print(f"  - MIN_LIKES: {config.MIN_LIKES}")
        print(f"  - MIN_VIEWS: {config.MIN_VIEWS}")
        print(f"  - HASHTAGS: {config.TARGET_HASHTAGS}")
        
        # Test 3: Initialisation du scraper
        print("\n[3/5] Initialisation du scraper...")
        scraper = TikTokScraper(config)
        
        try:
            await scraper.initialize()
            print("✓ Scraper initialisé")
        except Exception as e:
            print(f"✗ Erreur d'initialisation: {e}")
            print("\nErreur courante: TikTokApi nécessite Playwright")
            print("Solution: playwright install")
            return False
        
        # Test 4: Récupération de quelques vidéos trending
        print("\n[4/5] Test récupération vidéos trending (10 vidéos)...")
        try:
            videos = await scraper.get_trending_videos(count=10)
            print(f"✓ Récupéré {len(videos)} vidéos trending")
            
            if videos:
                print("\nExemple de vidéo récupérée:")
                v = videos[0]
                print(f"  ID: {v.get('id')}")
                print(f"  Auteur: {v.get('author')}")
                views = v.get('views', 0)
                likes = v.get('likes', 0)
                print(f"  Vues: {views:,}" if isinstance(views, int) else f"  Vues: {views}")
                print(f"  Likes: {likes:,}" if isinstance(likes, int) else f"  Likes: {likes}")
                print(f"  Description: {v.get('desc', '')[:50]}...")
                print(f"  URL vidéo: {'Présent' if v.get('video_url') else 'MANQUANT'}")
            else:
                print("⚠ Aucune vidéo récupérée")
                
        except Exception as e:
            print(f"✗ Erreur lors de la récupération: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Filtrage
        print("\n[5/5] Test du filtrage...")
        filter_obj = VideoFilter(config)
        
        if videos:
            quality_videos = filter_obj.filter_videos(videos)
            print(f"✓ Filtrage effectué: {len(quality_videos)}/{len(videos)} vidéos passent les critères")
            
            if not quality_videos:
                print("\n⚠ PROBLÈME IDENTIFIÉ: Aucune vidéo ne passe les critères de filtrage")
                print("\nCritères actuels:")
                print(f"  - Likes minimum: {config.MIN_LIKES:,}")
                print(f"  - Vues minimum: {config.MIN_VIEWS:,}")
                print(f"  - Engagement minimum: {config.MIN_ENGAGEMENT_RATE:.1%}")
                
                print("\nStatistiques des vidéos récupérées:")
                for i, v in enumerate(videos[:5], 1):
                    engagement = filter_obj.calculate_engagement_rate(v)
                    views = v.get('views', 0)
                    likes = v.get('likes', 0)
                    views_str = f"{views:,}" if isinstance(views, int) else str(views)
                    likes_str = f"{likes:,}" if isinstance(likes, int) else str(likes)
                    print(f"  {i}. Vues: {views_str} | Likes: {likes_str} | Engagement: {engagement:.2%}")
                
                print("\n💡 SOLUTION: Réduire les critères dans config.py")
                print("   Exemple:")
                print("   MIN_LIKES = 1000")
                print("   MIN_VIEWS = 10000")
                print("   MIN_ENGAGEMENT_RATE = 0.01")
        
        # Fermer
        await scraper.close()
        print("\n" + "=" * 70)
        print("✓ TEST TERMINÉ AVEC SUCCÈS")
        print("=" * 70)
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Erreur d'import: {e}")
        print("\nVérifiez que toutes les dépendances sont installées:")
        print("  pip install -r requirements.txt")
        print("  playwright install")
        return False
        
    except Exception as e:
        print(f"\n✗ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_relaxed_criteria():
    """Test avec critères plus souples"""
    print("\n" + "=" * 70)
    print("TEST AVEC CRITÈRES ASSOUPLIS")
    print("=" * 70)
    
    try:
        from config import Config
        from scraper.tiktok_scraper import TikTokScraper
        from scraper.video_filter import VideoFilter
        
        # Config avec critères très bas
        config = Config()
        config.MIN_LIKES = 100
        config.MIN_VIEWS = 1000
        config.MIN_ENGAGEMENT_RATE = 0.01
        
        print(f"\nCritères assouplis:")
        print(f"  - Likes minimum: {config.MIN_LIKES:,}")
        print(f"  - Vues minimum: {config.MIN_VIEWS:,}")
        print(f"  - Engagement minimum: {config.MIN_ENGAGEMENT_RATE:.1%}")
        
        scraper = TikTokScraper(config)
        await scraper.initialize()
        
        videos = await scraper.get_trending_videos(count=20)
        print(f"\n✓ Récupéré {len(videos)} vidéos")
        
        filter_obj = VideoFilter(config)
        quality_videos = filter_obj.filter_videos(videos)
        
        print(f"✓ {len(quality_videos)} vidéos passent les critères assouplis")
        
        if quality_videos:
            print("\nTop 3 vidéos:")
            for i, v in enumerate(quality_videos[:3], 1):
                print(f"\n{i}. ID: {v['id']}")
                print(f"   Auteur: @{v['author']}")
                print(f"   Vues: {v['views']:,}")
                print(f"   Likes: {v['likes']:,}")
                print(f"   Engagement: {v['engagement_rate']:.2%}")
                print(f"   Score viralité: {v['virality_score']:.2f}")
        
        await scraper.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale"""
    print("\n🔍 DIAGNOSTIC DU BOT TIKTOK\n")
    
    # Test 1: API normale
    success1 = asyncio.run(test_tiktok_api())
    
    if success1:
        # Test 2: Critères assouplis
        print("\n")
        success2 = asyncio.run(test_with_relaxed_criteria())
        
        if success2:
            print("\n" + "=" * 70)
            print("✅ DIAGNOSTIC COMPLET")
            print("=" * 70)
            print("\nLe scraper fonctionne correctement !")
            print("\nSi le bot principal ne trouve toujours pas de vidéos,")
            print("les critères de filtrage sont probablement trop stricts.")
            print("\n👉 Modifiez config.py avec des valeurs plus basses.")
    else:
        print("\n" + "=" * 70)
        print("❌ PROBLÈMES DÉTECTÉS")
        print("=" * 70)
        print("\nVérifiez:")
        print("  1. Les dépendances sont installées: pip install -r requirements.txt")
        print("  2. Playwright est installé: playwright install")
        print("  3. Vous avez une connexion internet")


if __name__ == "__main__":
    main()

