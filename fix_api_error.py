"""
Script pour contourner l'erreur 10201 de TikTok API
Utilise des techniques alternatives pour récupérer les vidéos
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_different_approaches():
    """Tester différentes approches pour contourner l'erreur 10201"""
    
    print("=" * 70)
    print("TEST DES DIFFÉRENTES APPROCHES POUR CONTOURNER L'ERREUR 10201")
    print("=" * 70)
    
    # Approche 1: Avec région spécifiée
    print("\n[1/3] Test avec région US...")
    try:
        from TikTokApi import TikTokApi
        
        async with TikTokApi() as api:
            await api.create_sessions(
                num_sessions=1,
                headless=True,
                context_options={
                    "locale": "en-US",
                    "timezone_id": "America/New_York"
                }
            )
            
            videos = []
            try:
                async for video in api.trending.videos(count=5):
                    videos.append(video)
                    if len(videos) >= 5:
                        break
                
                print(f"✓ Récupéré {len(videos)} vidéos avec région US")
                return True
            except Exception as e:
                print(f"✗ Erreur: {e}")
    except Exception as e:
        print(f"✗ Échec approche 1: {e}")
    
    # Approche 2: User par ID direct
    print("\n[2/3] Test avec recherche par utilisateur...")
    try:
        from TikTokApi import TikTokApi
        
        async with TikTokApi() as api:
            await api.create_sessions(num_sessions=1, headless=True)
            
            # Essayer de récupérer des vidéos d'un utilisateur populaire
            user = api.user(username="tiktok")
            videos = []
            async for video in user.videos(count=5):
                videos.append(video)
                if len(videos) >= 5:
                    break
            
            print(f"✓ Récupéré {len(videos)} vidéos par utilisateur")
            return True
    except Exception as e:
        print(f"✗ Échec approche 2: {e}")
    
    # Approche 3: Recherche par mot-clé
    print("\n[3/3] Test avec recherche par mot-clé...")
    try:
        from TikTokApi import TikTokApi
        
        async with TikTokApi() as api:
            await api.create_sessions(num_sessions=1, headless=True)
            
            # Recherche par mot-clé au lieu de trending
            videos = []
            async for video in api.search.videos("funny", count=5):
                videos.append(video)
                if len(videos) >= 5:
                    break
            
            print(f"✓ Récupéré {len(videos)} vidéos par recherche")
            return True
    except Exception as e:
        print(f"✗ Échec approche 3: {e}")
    
    return False


async def test_with_delay():
    """Tester avec délai entre requêtes"""
    print("\n[4/4] Test avec délais entre requêtes...")
    try:
        from TikTokApi import TikTokApi
        import time
        
        async with TikTokApi() as api:
            await api.create_sessions(num_sessions=1, headless=True)
            
            # Attendre un peu avant de faire des requêtes
            await asyncio.sleep(5)
            
            videos = []
            async for video in api.trending.videos(count=3):
                videos.append(video)
                # Petit délai entre chaque vidéo
                await asyncio.sleep(2)
                if len(videos) >= 3:
                    break
            
            print(f"✓ Récupéré {len(videos)} vidéos avec délais")
            return True
    except Exception as e:
        print(f"✗ Échec: {e}")
        return False


async def main():
    """Fonction principale"""
    print("\n🔍 DIAGNOSTIC DE L'ERREUR 10201\n")
    print("Cette erreur indique que TikTok bloque l'accès à l'API.")
    print("Causes possibles:")
    print("  • Trop de requêtes en peu de temps")
    print("  • IP bloquée temporairement")
    print("  • Détection de bot")
    print("\n")
    
    success = await test_different_approaches()
    
    if not success:
        success = await test_with_delay()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ SOLUTION TROUVÉE")
        print("=" * 70)
        print("\nAu moins une méthode fonctionne.")
    else:
        print("❌ TOUTES LES APPROCHES ONT ÉCHOUÉ")
        print("=" * 70)
        print("\n💡 SOLUTIONS POSSIBLES:")
        print("\n1. ATTENDRE (Recommandé)")
        print("   • Attendre 1-2 heures avant de réessayer")
        print("   • TikTok lève souvent les restrictions après un délai")
        print("\n2. CHANGER D'IP")
        print("   • Utiliser un VPN")
        print("   • Redémarrer votre routeur (nouvelle IP)")
        print("\n3. UTILISER UN PROXY")
        print("   • Configurer un proxy dans TikTokApi")
        print("   • Utiliser des proxies rotatifs")
        print("\n4. ALTERNATIVE: YT-DLP")
        print("   • Utiliser yt-dlp au lieu de TikTokApi")
        print("   • Plus stable mais nécessite l'URL de la vidéo")
        print("\n5. RÉDUIRE LA FRÉQUENCE")
        print("   • Augmenter CHECK_INTERVAL dans config.py")
        print("   • Faire moins de requêtes par cycle")


if __name__ == "__main__":
    asyncio.run(main())



