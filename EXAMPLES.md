# Exemples d'Utilisation et de Configuration

## 🎯 Scénarios d'Utilisation

### Scénario 1 : Gaming Content

Configuration pour un compte de gaming :

```python
# config.py
MIN_LIKES = 15000
MIN_VIEWS = 150000
MIN_ENGAGEMENT_RATE = 0.08

TARGET_HASHTAGS = [
    '#gaming',
    '#gamingontiktok',
    '#fortnite',
    '#minecraft',
    '#valorant',
    '#gamingclips'
]

MAX_VIDEOS_PER_DAY = 15

# Heures de forte activité pour le gaming
ACTIVE_HOURS_START = 14  # 14h
ACTIVE_HOURS_END = 23    # 23h
```

### Scénario 2 : Comedy/Entertainment

Configuration pour du contenu humoristique :

```python
# config.py
MIN_LIKES = 20000
MIN_VIEWS = 200000
MIN_ENGAGEMENT_RATE = 0.10  # Le comedy a généralement bon engagement

TARGET_HASHTAGS = [
    '#funny',
    '#comedy',
    '#humor',
    '#memes',
    '#viral',
    '#foryou'
]

MAX_VIDEOS_PER_DAY = 20

ACTIVE_HOURS_START = 10
ACTIVE_HOURS_END = 23
```

### Scénario 3 : Démarrage Progressif (Recommandé)

Configuration sûre pour débuter :

```python
# config.py - Semaine 1
MIN_LIKES = 5000
MIN_VIEWS = 50000
MIN_ENGAGEMENT_RATE = 0.03

TARGET_HASHTAGS = ['#fyp', '#viral', '#trending']

MAX_VIDEOS_PER_DAY = 5  # Commencer doucement !

MIN_DELAY_BETWEEN_UPLOADS = 900   # 15 minutes minimum
MAX_DELAY_BETWEEN_UPLOADS = 1800  # 30 minutes maximum
```

### Scénario 4 : Volume Maximum (Risqué)

Configuration agressive (attention aux bans) :

```python
# config.py
MIN_LIKES = 8000
MIN_VIEWS = 80000
MIN_ENGAGEMENT_RATE = 0.04

TARGET_HASHTAGS = [
    '#viral', '#fyp', '#trending', '#foryou', 
    '#tiktok', '#viralvideo', '#foryoupage'
]

MAX_VIDEOS_PER_DAY = 30  # Maximum recommandé

# Délais plus courts (mais risqué)
MIN_DELAY_BETWEEN_UPLOADS = 300  # 5 minutes
MAX_DELAY_BETWEEN_UPLOADS = 600  # 10 minutes

# Plus d'heures actives
ACTIVE_HOURS_START = 8
ACTIVE_HOURS_END = 23
```

### Scénario 5 : Niche Spécifique (Fitness)

```python
# config.py
MIN_LIKES = 12000
MIN_VIEWS = 120000
MIN_ENGAGEMENT_RATE = 0.06

TARGET_HASHTAGS = [
    '#fitness',
    '#workout',
    '#gym',
    '#fitnessmotivation',
    '#bodybuilding',
    '#fitnesslife'
]

MAX_VIDEOS_PER_DAY = 10

# Horaires optimaux pour fitness
ACTIVE_HOURS_START = 6   # Tôt le matin
ACTIVE_HOURS_END = 22
```

## 📊 Scripts Personnalisés

### Script 1 : Analyse des Tendances

Créer `analyze_trends.py` :

```python
"""Analyser les tendances sans publier"""
import asyncio
from config import Config
from scraper.tiktok_scraper import TikTokScraper
from scraper.video_filter import VideoFilter

async def main():
    config = Config()
    scraper = TikTokScraper(config)
    filter_obj = VideoFilter(config)
    
    await scraper.initialize()
    
    print("Récupération des vidéos...")
    videos = await scraper.get_all_videos()
    
    print(f"\nTotal vidéos: {len(videos)}")
    
    quality = filter_obj.filter_videos(videos)
    print(f"Vidéos de qualité: {len(quality)}")
    
    if quality:
        print("\n=== TOP 10 ===")
        for i, v in enumerate(quality[:10], 1):
            print(f"{i}. {v['id']}")
            print(f"   Auteur: {v['author']}")
            print(f"   Vues: {v['views']:,} | Likes: {v['likes']:,}")
            print(f"   Engagement: {v['engagement_rate']:.2%}")
            print(f"   Score: {v['virality_score']:.2f}")
            print()
    
    await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Utilisation :
```bash
python analyze_trends.py
```

### Script 2 : Téléchargement Seulement

Créer `download_only.py` :

```python
"""Télécharger des vidéos sans les uploader"""
import asyncio
from config import Config
from scraper.tiktok_scraper import TikTokScraper
from scraper.video_filter import VideoFilter
from downloader.video_downloader import VideoDownloader
from database.db_manager import DatabaseManager

async def main():
    config = Config()
    config.create_folders()
    
    scraper = TikTokScraper(config)
    filter_obj = VideoFilter(config)
    downloader = VideoDownloader(config)
    db = DatabaseManager(config.DATABASE_URL)
    
    await scraper.initialize()
    
    videos = await scraper.get_all_videos()
    quality = filter_obj.filter_videos(videos)
    
    print(f"Téléchargement de {min(len(quality), 10)} vidéos...")
    
    for i, video in enumerate(quality[:10], 1):
        if db.is_video_processed(video['id']):
            continue
        
        print(f"[{i}/10] Téléchargement {video['id']}...")
        path = downloader.download_video(video)
        
        if path:
            video['local_path'] = path
            db.add_video(video)
            print(f"✓ Sauvegardé : {path}")
    
    await scraper.close()
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Script 3 : Statistiques de Performance

Créer `stats.py` :

```python
"""Afficher les statistiques du bot"""
from database.db_manager import DatabaseManager
from config import Config
from datetime import datetime, timedelta

def main():
    config = Config()
    db = DatabaseManager(config.DATABASE_URL)
    
    print("=" * 60)
    print("STATISTIQUES DU BOT")
    print("=" * 60)
    
    # Statistiques globales
    all_videos = db.get_all_processed_videos(limit=10000)
    
    total = len(all_videos)
    uploaded = sum(1 for v in all_videos if v.is_uploaded)
    
    print(f"\nTotal vidéos traitées: {total}")
    print(f"Vidéos uploadées: {uploaded}")
    print(f"Taux de succès: {uploaded/total*100:.1f}%" if total > 0 else "N/A")
    
    # Statistiques aujourd'hui
    today_count = db.get_uploaded_count_today()
    print(f"\nUploadées aujourd'hui: {today_count}/{config.MAX_VIDEOS_PER_DAY}")
    
    # Engagement moyen
    if all_videos:
        avg_engagement = sum(v.engagement_rate for v in all_videos) / len(all_videos)
        avg_likes = sum(v.likes for v in all_videos) / len(all_videos)
        avg_views = sum(v.views for v in all_videos) / len(all_videos)
        
        print(f"\nEngagement moyen: {avg_engagement:.2%}")
        print(f"Likes moyens: {avg_likes:,.0f}")
        print(f"Vues moyennes: {avg_views:,.0f}")
    
    # Top performers
    if uploaded > 0:
        uploaded_videos = [v for v in all_videos if v.is_uploaded]
        top_videos = sorted(uploaded_videos, key=lambda v: v.engagement_rate, reverse=True)[:5]
        
        print("\n=== TOP 5 VIDÉOS ===")
        for i, v in enumerate(top_videos, 1):
            print(f"{i}. {v.id} (@{v.author})")
            print(f"   Vues: {v.views:,} | Likes: {v.likes:,}")
            print(f"   Engagement: {v.engagement_rate:.2%}")
    
    db.close()

if __name__ == "__main__":
    main()
```

Utilisation :
```bash
python stats.py
```

### Script 4 : Nettoyage de la Base de Données

Créer `cleanup_db.py` :

```python
"""Nettoyer les anciennes entrées de la base de données"""
from database.db_manager import DatabaseManager
from config import Config
from datetime import datetime, timedelta

def main():
    config = Config()
    db = DatabaseManager(config.DATABASE_URL)
    
    # Supprimer les vidéos de plus de 30 jours
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    old_videos = db.session.query(db.ProcessedVideo).filter(
        db.ProcessedVideo.downloaded_at < cutoff_date
    ).all()
    
    print(f"Trouvé {len(old_videos)} vidéos de plus de 30 jours")
    
    if old_videos:
        confirm = input("Voulez-vous les supprimer ? (oui/non) : ")
        if confirm.lower() == 'oui':
            for video in old_videos:
                db.session.delete(video)
            db.session.commit()
            print(f"✓ {len(old_videos)} vidéos supprimées")
    
    db.close()

if __name__ == "__main__":
    main()
```

## 🔧 Modifications Avancées

### Ajouter des Descriptions Personnalisées

Dans `main.py`, ligne ~160, modifier :

```python
# Au lieu de :
description = video.get('desc', '')[:100]

# Utiliser :
descriptions = [
    "Contenu viral du jour ! 🔥",
    "Tu ne vas pas croire ça... 😱",
    "Incroyable découverte ! 🤯",
    "Regarde jusqu'à la fin ! ⚡",
]
import random
description = random.choice(descriptions)
```

### Rotation de Hashtags

```python
# Dans main.py
hashtag_sets = [
    ['#viral', '#fyp', '#trending'],
    ['#foryou', '#foryoupage', '#viralvideo'],
    ['#tiktok', '#tiktokviral', '#trending'],
]
hashtags = random.choice(hashtag_sets)
```

### Filtrage par Auteur

Dans `scraper/video_filter.py`, ajouter :

```python
BLACKLIST_AUTHORS = ['author1', 'author2']  # Auteurs à éviter

def is_quality_video(self, video: Dict) -> bool:
    # Vérifications existantes...
    
    # Nouvelle vérification
    is_not_blacklisted = video.get('author') not in BLACKLIST_AUTHORS
    
    return has_min_likes and has_min_views and \
           has_min_engagement and has_video_url and is_not_blacklisted
```

### Notification Discord

Ajouter dans `requirements.txt` :
```
discord-webhook
```

Dans `main.py` :

```python
from discord_webhook import DiscordWebhook

DISCORD_WEBHOOK_URL = "votre_webhook_url"

def send_notification(message):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=message)
    webhook.execute()

# Utiliser après chaque upload réussi :
send_notification(f"✓ Vidéo {video['id']} uploadée avec succès!")
```

## 🎛️ Configurations par Profil

Créer `profiles/` avec différents configs :

```bash
mkdir profiles
```

`profiles/aggressive.py` :
```python
from config import Config

class AggressiveConfig(Config):
    MAX_VIDEOS_PER_DAY = 30
    MIN_DELAY_BETWEEN_UPLOADS = 300
    MAX_DELAY_BETWEEN_UPLOADS = 600
```

`profiles/safe.py` :
```python
from config import Config

class SafeConfig(Config):
    MAX_VIDEOS_PER_DAY = 5
    MIN_DELAY_BETWEEN_UPLOADS = 1800
    MAX_DELAY_BETWEEN_UPLOADS = 3600
```

Utilisation :
```python
# Dans main.py
from profiles.safe import SafeConfig
config = SafeConfig()  # Au lieu de Config()
```

## 📈 Monitoring Avancé

### Script de Monitoring en Temps Réel

Créer `monitor.py` :

```python
"""Dashboard de monitoring en temps réel"""
import time
import os
from database.db_manager import DatabaseManager
from config import Config

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def main():
    config = Config()
    
    while True:
        clear_screen()
        db = DatabaseManager(config.DATABASE_URL)
        
        print("=" * 60)
        print("BOT TIKTOK - MONITORING")
        print("=" * 60)
        
        all_videos = db.get_all_processed_videos(limit=10000)
        today_count = db.get_uploaded_count_today()
        
        print(f"\n📊 Statistiques")
        print(f"  Total traité: {len(all_videos)}")
        print(f"  Uploadé aujourd'hui: {today_count}/{config.MAX_VIDEOS_PER_DAY}")
        print(f"  Restant: {config.MAX_VIDEOS_PER_DAY - today_count}")
        
        recent = all_videos[:5]
        if recent:
            print(f"\n📹 5 Dernières Vidéos")
            for v in recent:
                status = "✓" if v.is_uploaded else "⏳"
                print(f"  {status} {v.id} - {v.views:,} vues")
        
        db.close()
        
        print(f"\n🔄 Rafraîchissement dans 10 secondes... (Ctrl+C pour quitter)")
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring arrêté.")
```

---

**Ces exemples vous permettent de personnaliser complètement le bot selon vos besoins !**

