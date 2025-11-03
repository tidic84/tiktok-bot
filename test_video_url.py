"""Test pour trouver comment obtenir l'URL des vidéos"""
import asyncio
from TikTokApi import TikTokApi


async def test_video_structure():
    """Inspecter la structure d'une vidéo TikTok"""
    async with TikTokApi() as api:
        await api.create_sessions(num_sessions=1, headless=True)
        
        print("Récupération d'une vidéo...")
        async for video in api.trending.videos(count=1):
            print("\n=== STRUCTURE DE L'OBJET VIDEO ===\n")
            
            # Attributs principaux
            print(f"ID: {video.id}")
            print(f"Author: {video.author.username if hasattr(video.author, 'username') else 'N/A'}")
            
            # Stats
            if hasattr(video, 'stats'):
                print(f"\nStats: {video.stats}")
            
            # Video object
            if hasattr(video, 'video'):
                print(f"\nVideo object exists: True")
                video_obj = video.video
                print(f"Video attributes: {dir(video_obj)}")
                
                # Essayer différentes propriétés
                for attr in ['download_addr', 'downloadAddr', 'playAddr', 'play_addr', 'url']:
                    if hasattr(video_obj, attr):
                        value = getattr(video_obj, attr)
                        print(f"  {attr}: {value}")
            
            # Regarder as_dict
            if hasattr(video, 'as_dict'):
                data = video.as_dict
                print(f"\n=== as_dict KEYS ===")
                print(f"Keys: {list(data.keys())}")
                
                if 'video' in data:
                    print(f"\nVideo data: {data['video']}")
            
            # Essayer l'attribut info
            if hasattr(video, 'info'):
                print(f"\nInfo: {video.info}")
            
            break


if __name__ == "__main__":
    asyncio.run(test_video_structure())



