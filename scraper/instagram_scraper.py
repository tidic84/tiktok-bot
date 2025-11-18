"""Scraper Instagram utilisant instaloader"""
import logging
from typing import List, Dict
import instaloader
import time
import os
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

        # Configuration du proxy si spécifié
        proxy_url = getattr(config, 'PROXY_URL', None)
        if proxy_url:
            self.loader.context._session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"Proxy configuré: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")

        # Authentification optionnelle pour éviter le rate limiting
        self.authenticated = False

        # Méthode 1: Authentification par cookies JSON (prioritaire)
        cookies_file = getattr(config, 'INSTAGRAM_COOKIES_FILE', None)
        if cookies_file and os.path.exists(cookies_file):
            try:
                logger.info(f"Chargement des cookies Instagram depuis: {cookies_file}")
                self._load_cookies_from_json(cookies_file)
                self.authenticated = True
                logger.info("✓ Authentification Instagram par cookies réussie")
            except Exception as e:
                logger.warning(f"⚠️  Impossible de charger les cookies: {e}")
                logger.info("Tentative d'authentification par username/password...")

        # Méthode 2: Authentification par username/password (fallback)
        if not self.authenticated:
            instagram_username = getattr(config, 'INSTAGRAM_USERNAME', None)
            instagram_password = getattr(config, 'INSTAGRAM_PASSWORD', None)

            if instagram_username and instagram_password:
                try:
                    logger.info(f"Connexion à Instagram avec le compte: {instagram_username}")
                    self.loader.login(instagram_username, instagram_password)
                    self.authenticated = True
                    logger.info("✓ Authentification Instagram réussie")
                except Exception as e:
                    logger.warning(f"⚠️  Impossible de se connecter à Instagram: {e}")
                    logger.info("Scraping en mode anonyme (peut être limité)")
            else:
                logger.info("InstagramScraper initialisé en mode anonyme (peut être limité par Instagram)")
                logger.info("Ajoutez INSTAGRAM_COOKIES_FILE ou INSTAGRAM_USERNAME/PASSWORD dans .env")

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
            # Format standard des extensions de navigateur
            if isinstance(cookie, dict):
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                domain = cookie.get('domain', '.instagram.com')

                # Ajouter le cookie à la session
                self.loader.context._session.cookies.set(
                    name,
                    value,
                    domain=domain,
                    path=cookie.get('path', '/')
                )

        logger.info(f"✓ {len(cookies)} cookies chargés")

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
