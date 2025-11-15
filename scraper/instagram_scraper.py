"""Scraper Instagram utilisant instaloader"""
import logging
from typing import List, Dict
import instaloader
import time

logger = logging.getLogger(__name__)


class InstagramScraper:
    """Scraper qui récupère des vidéos Instagram depuis des créateurs spécifiques"""

    def __init__(self, config):
        """
        Initialiser le scraper

        Args:
            config: Objet de configuration
        """
        self.config = config
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True  # Moins de logs
        )
        logger.info("InstagramScraper initialisé (instaloader)")

    def get_user_videos(self, username: str, count: int = 10) -> List[Dict]:
        """
        Récupérer les vidéos d'un utilisateur Instagram via instaloader

        Args:
            username: Nom d'utilisateur Instagram (sans @)
            count: Nombre maximum de vidéos à récupérer

        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        videos = []

        try:
            logger.info(f"Récupération des vidéos Instagram de @{username}...")

            # Charger le profil
            profile = instaloader.Profile.from_username(self.loader.context, username)

            # Parcourir les posts (limité à count vidéos)
            video_count = 0
            for post in profile.get_posts():
                # Ne garder que les vidéos (Reels ou IGTV)
                if post.is_video:
                    try:
                        # Calculer le taux d'engagement
                        engagement_rate = 0.0
                        if post.video_view_count and post.video_view_count > 0:
                            interactions = post.likes + post.comments
                            engagement_rate = interactions / post.video_view_count

                        video_data = {
                            'id': post.shortcode,
                            'author': username,
                            'desc': post.caption or '',  # Description avec hashtags
                            'likes': post.likes,
                            'views': post.video_view_count or 0,
                            'shares': 0,  # Instagram ne fournit pas cette donnée
                            'comments': post.comments,
                            'video_url': f"https://www.instagram.com/p/{post.shortcode}/",
                            'music': None,
                            'create_time': int(post.date_utc.timestamp()),
                            'platform': 'instagram',
                            'engagement_rate': engagement_rate
                        }
                        videos.append(video_data)
                        video_count += 1

                        if video_count >= count:
                            break

                    except Exception as e:
                        logger.warning(f"Erreur extraction post {post.shortcode}: {e}")
                        continue

                # Pause pour éviter rate limiting
                time.sleep(0.5)

            logger.info(f"✓ {len(videos)} vidéos Instagram récupérées de @{username}")
            return videos

        except instaloader.exceptions.ProfileNotExistsException:
            logger.error(f"Le profil Instagram @{username} n'existe pas")
            return videos
        except instaloader.exceptions.ConnectionException as e:
            logger.error(f"Erreur de connexion Instagram pour @{username}: {e}")
            logger.warning("⚠️  Instagram bloque peut-être vos requêtes. Attendez quelques minutes.")
            return videos
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos Instagram de @{username}: {e}")
            return videos

    def get_videos_from_creators(self, creators: List[str], count_per_creator: int = 10) -> List[Dict]:
        """
        Récupérer des vidéos depuis une liste de créateurs Instagram

        Args:
            creators: Liste de noms d'utilisateurs Instagram
            count_per_creator: Nombre de vidéos par créateur

        Returns:
            Liste combinée de toutes les vidéos
        """
        all_videos = []

        for i, creator in enumerate(creators):
            videos = self.get_user_videos(creator, count_per_creator)
            all_videos.extend(videos)

            # Pause entre créateurs pour éviter rate limiting
            if i < len(creators) - 1:
                logger.info("Pause de 2 secondes avant le prochain créateur...")
                time.sleep(2)

        # Retirer les doublons
        unique_videos = {v['id']: v for v in all_videos if v.get('id')}.values()
        logger.info(f"📊 Total: {len(unique_videos)} vidéos Instagram uniques de {len(creators)} créateurs")

        return list(unique_videos)
