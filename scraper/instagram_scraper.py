"""Scraper Instagram utilisant yt-dlp"""
import logging
from typing import List, Dict
import subprocess
import json

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
        logger.info("InstagramScraper initialisé")

    def get_user_videos(self, username: str, count: int = 10) -> List[Dict]:
        """
        Récupérer les vidéos d'un utilisateur Instagram via yt-dlp

        Args:
            username: Nom d'utilisateur Instagram (sans @)
            count: Nombre maximum de vidéos à récupérer

        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        videos = []

        try:
            logger.info(f"Récupération des vidéos Instagram de @{username}...")

            # URL du profil Instagram
            profile_url = f"https://www.instagram.com/{username}/"

            # Commande yt-dlp pour récupérer les métadonnées sans télécharger
            # Instagram nécessite parfois des cookies ou des user-agents spécifiques
            cmd = [
                'yt-dlp',
                '--dump-json',  # Sortie JSON
                '--playlist-end', str(count),  # Limiter le nombre de vidéos
                '--no-warnings',
                '--user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                profile_url
            ]

            # Exécuter la commande
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )

            if result.returncode != 0:
                logger.error(f"Erreur yt-dlp pour @{username}: {result.stderr}")
                return videos

            # Parser chaque ligne JSON (une vidéo par ligne)
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue

                try:
                    video_info = json.loads(line)

                    # Instagram fournit des données différentes de TikTok
                    # On adapte le format pour être compatible avec le reste du bot
                    description = video_info.get('description', '') or video_info.get('title', '')

                    video_data = {
                        'id': video_info.get('id', ''),
                        'author': username,
                        'desc': description,  # Description COMPLÈTE avec hashtags originaux
                        'likes': video_info.get('like_count', 0),
                        'views': video_info.get('view_count', 0) or video_info.get('play_count', 0),
                        'shares': 0,  # Instagram ne fournit pas toujours le nombre de partages
                        'comments': video_info.get('comment_count', 0),
                        'video_url': video_info.get('webpage_url', ''),
                        'music': None,  # Instagram gère la musique différemment
                        'create_time': video_info.get('timestamp', 0),
                        'platform': 'instagram'  # Identifier la plateforme source
                    }
                    videos.append(video_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Erreur parsing JSON: {e}")
                    continue

            logger.info(f"✓ {len(videos)} vidéos Instagram récupérées de @{username}")
            return videos

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de la récupération des vidéos Instagram de @{username}")
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

        for creator in creators:
            videos = self.get_user_videos(creator, count_per_creator)
            all_videos.extend(videos)

        # Retirer les doublons
        unique_videos = {v['id']: v for v in all_videos if v.get('id')}.values()
        logger.info(f"📊 Total: {len(unique_videos)} vidéos Instagram uniques de {len(creators)} créateurs")

        return list(unique_videos)
