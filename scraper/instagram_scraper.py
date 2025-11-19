"""Scraper Instagram utilisant instascrape"""
import logging
from typing import List, Dict
import time
import os
import json
import requests

logger = logging.getLogger(__name__)

# Import instascrape
try:
    from instascrape import Profile, Post
    INSTASCRAPE_AVAILABLE = True
except ImportError:
    INSTASCRAPE_AVAILABLE = False
    logger.warning("instascrape non installé. Installez avec: pip install insta-scrape")


class InstagramScraper:
    """Scraper qui récupère des vidéos Instagram depuis des créateurs spécifiques"""

    def __init__(self, config):
        """
        Initialiser le scraper

        Args:
            config: Objet de configuration
        """
        self.config = config
        self.session = requests.Session()
        self.authenticated = False

        if not INSTASCRAPE_AVAILABLE:
            logger.error("instascrape n'est pas disponible")
            return

        # Configuration du proxy si spécifié
        proxy_url = getattr(config, 'PROXY_URL', None)
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"Proxy configuré: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")

        # Headers pour simuler un navigateur
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Authentification par cookies JSON (prioritaire)
        cookies_file = getattr(config, 'INSTAGRAM_COOKIES_FILE', None)
        if cookies_file and os.path.exists(cookies_file):
            try:
                logger.info(f"Chargement des cookies Instagram depuis: {cookies_file}")
                self._load_cookies_from_json(cookies_file)
                self.authenticated = True
                logger.info("✓ Authentification Instagram par cookies réussie")
            except Exception as e:
                logger.warning(f"⚠️  Impossible de charger les cookies: {e}")
        else:
            logger.info("InstagramScraper initialisé en mode anonyme (peut être limité par Instagram)")
            logger.info("Ajoutez INSTAGRAM_COOKIES_FILE dans .env pour éviter les limitations")

    def _load_cookies_from_json(self, cookies_file: str):
        """
        Charger les cookies depuis un fichier JSON exporté du navigateur

        Args:
            cookies_file: Chemin vers le fichier JSON des cookies
        """
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)

        # Convertir les cookies JSON en format requests
        for cookie in cookies:
            if isinstance(cookie, dict):
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                domain = cookie.get('domain', '.instagram.com')

                self.session.cookies.set(
                    name,
                    value,
                    domain=domain,
                    path=cookie.get('path', '/')
                )

        logger.info(f"✓ {len(cookies)} cookies chargés")

    def get_user_videos(self, username: str, count: int = 10) -> List[Dict]:
        """
        Récupérer les vidéos d'un utilisateur Instagram via instascrape

        Args:
            username: Nom d'utilisateur Instagram (sans @)
            count: Nombre maximum de vidéos à récupérer

        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        videos = []

        if not INSTASCRAPE_AVAILABLE:
            logger.error("instascrape n'est pas disponible")
            return videos

        try:
            logger.info(f"Récupération des vidéos Instagram de @{username}...")

            # Créer le profil avec instascrape
            profile_url = f"https://www.instagram.com/{username}/"
            profile = Profile(profile_url)

            # Scraper le profil avec notre session authentifiée
            profile.scrape(session=self.session)

            # Récupérer les posts récents
            posts = profile.get_posts(session=self.session, amt=count * 2)  # Récupérer plus pour filtrer les vidéos

            video_count = 0
            for post_data in posts:
                try:
                    # Créer l'objet Post et scraper ses détails
                    post = Post(post_data.url)
                    post.scrape(session=self.session)

                    # Vérifier si c'est une vidéo
                    if post.is_video:
                        # Calculer le taux d'engagement
                        engagement_rate = 0.0
                        if hasattr(post, 'video_view_count') and post.video_view_count and post.video_view_count > 0:
                            interactions = post.likes + post.comments
                            engagement_rate = interactions / post.video_view_count

                        video_data = {
                            'id': post.shortcode,
                            'author': username,
                            'desc': post.caption if hasattr(post, 'caption') else '',
                            'likes': post.likes if hasattr(post, 'likes') else 0,
                            'views': post.video_view_count if hasattr(post, 'video_view_count') else 0,
                            'shares': 0,
                            'comments': post.comments if hasattr(post, 'comments') else 0,
                            'video_url': f"https://www.instagram.com/p/{post.shortcode}/",
                            'music': None,
                            'create_time': int(post.timestamp.timestamp()) if hasattr(post, 'timestamp') else 0,
                            'platform': 'instagram',
                            'engagement_rate': engagement_rate
                        }
                        videos.append(video_data)
                        video_count += 1

                        if video_count >= count:
                            break

                    # Pause pour éviter rate limiting
                    time.sleep(1)

                except Exception as e:
                    logger.warning(f"Erreur extraction post: {e}")
                    continue

            logger.info(f"✓ {len(videos)} vidéos Instagram récupérées de @{username}")
            return videos

        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or '403' in error_msg or 'Unauthorized' in error_msg:
                logger.error(f"Erreur de connexion Instagram pour @{username}: {e}")
                logger.warning("⚠️  Instagram bloque peut-être vos requêtes. Vérifiez vos cookies.")
            else:
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
                logger.info("Pause de 3 secondes avant le prochain créateur...")
                time.sleep(3)

        # Retirer les doublons
        unique_videos = {v['id']: v for v in all_videos if v.get('id')}.values()
        logger.info(f"📊 Total: {len(unique_videos)} vidéos Instagram uniques de {len(creators)} créateurs")

        return list(unique_videos)
