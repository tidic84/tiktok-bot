"""Scraper Instagram utilisant l'API GraphQL d'Instagram"""
import logging
from typing import List, Dict
import time
import os
import json
import requests
import re

logger = logging.getLogger(__name__)


class InstagramScraper:
    """Scraper qui récupère des vidéos Instagram via l'API GraphQL"""

    def __init__(self, config):
        """
        Initialiser le scraper

        Args:
            config: Objet de configuration
        """
        self.config = config
        self.session = requests.Session()
        self.authenticated = False

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
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-IG-App-ID': '936619743392459',  # Instagram Web App ID
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
        })

        # Charger les cookies si disponibles (améliore le taux de succès)
        cookies_file = getattr(config, 'INSTAGRAM_COOKIES_FILE', None)
        if cookies_file and os.path.exists(cookies_file):
            try:
                logger.info(f"Chargement des cookies Instagram depuis: {cookies_file}")
                self._load_cookies_from_json(cookies_file)
                self.authenticated = True
                logger.info("✓ Cookies chargés (améliore le taux de succès)")
            except Exception as e:
                logger.warning(f"⚠️  Impossible de charger les cookies: {e}")
                logger.info("Scraping en mode anonyme via GraphQL")
        else:
            logger.info("InstagramScraper initialisé (API GraphQL)")

    def _load_cookies_from_json(self, cookies_file: str):
        """Charger les cookies depuis un fichier JSON"""
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)

        sessionid_found = False
        cookie_pairs = []

        for cookie in cookies:
            if isinstance(cookie, dict):
                name = cookie.get('name', '')
                value = cookie.get('value', '')

                if name and value:
                    cookie_pairs.append(f"{name}={value}")

                    # Ajouter aux cookies de session
                    domain = cookie.get('domain', '.instagram.com')
                    if 'instagram' in domain:
                        domain = '.instagram.com'

                    self.session.cookies.set(
                        name, value, domain=domain, path=cookie.get('path', '/')
                    )

                    if name == 'sessionid':
                        sessionid_found = True

        # Ajouter le header Cookie
        if cookie_pairs:
            self.session.headers['Cookie'] = "; ".join(cookie_pairs)

        logger.info(f"✓ {len(cookies)} cookies chargés")
        if sessionid_found:
            logger.info("✓ sessionid trouvé")

    def _get_user_id(self, username: str) -> str:
        """Obtenir l'ID utilisateur depuis le nom d'utilisateur"""
        try:
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data['data']['user']['id']
            else:
                # Fallback: scraper la page profil
                url = f"https://www.instagram.com/{username}/"
                response = self.session.get(url, timeout=10)

                # Chercher l'ID dans le HTML
                match = re.search(r'"user_id":"(\d+)"', response.text)
                if match:
                    return match.group(1)

                match = re.search(r'"profilePage_(\d+)"', response.text)
                if match:
                    return match.group(1)

        except Exception as e:
            logger.debug(f"Erreur obtention user_id pour {username}: {e}")

        return None

    def _get_user_posts_graphql(self, user_id: str, count: int = 12) -> List[Dict]:
        """Récupérer les posts d'un utilisateur via GraphQL"""
        posts = []

        try:
            # Variables pour la requête GraphQL
            variables = {
                "id": user_id,
                "first": count
            }

            # doc_id pour récupérer les posts d'un utilisateur
            # Ce doc_id est pour la requête PolarisProfilePostsQuery
            params = {
                "variables": json.dumps(variables),
                "doc_id": "17991233890457762"  # Posts query
            }

            url = "https://www.instagram.com/graphql/query/"
            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Parser les edges
                edges = data.get('data', {}).get('user', {}).get('edge_owner_to_timeline_media', {}).get('edges', [])

                for edge in edges:
                    node = edge.get('node', {})
                    posts.append(node)

            return posts

        except Exception as e:
            logger.debug(f"Erreur GraphQL posts: {e}")
            return posts

    def _get_post_details(self, shortcode: str) -> Dict:
        """Obtenir les détails d'un post via GraphQL"""
        try:
            variables = {
                "shortcode": shortcode
            }

            params = {
                "variables": json.dumps(variables),
                "doc_id": "10015901848480474"  # Post details query
            }

            url = "https://www.instagram.com/graphql/query/"
            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('xdt_shortcode_media', {})

        except Exception as e:
            logger.debug(f"Erreur détails post {shortcode}: {e}")

        return {}

    def get_user_videos(self, username: str, count: int = 10) -> List[Dict]:
        """
        Récupérer les vidéos d'un utilisateur Instagram

        Args:
            username: Nom d'utilisateur Instagram (sans @)
            count: Nombre maximum de vidéos à récupérer

        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        videos = []

        try:
            logger.info(f"Récupération des vidéos Instagram de @{username}...")

            # Méthode 1: Essayer l'API web_profile_info
            user_id = self._get_user_id(username)

            if user_id:
                logger.debug(f"User ID trouvé: {user_id}")
                posts = self._get_user_posts_graphql(user_id, count * 2)
            else:
                # Méthode 2: Scraper directement la page profil
                posts = self._scrape_profile_page(username, count * 2)

            video_count = 0
            for post in posts:
                try:
                    # Vérifier si c'est une vidéo
                    is_video = post.get('is_video', False)

                    if is_video:
                        shortcode = post.get('shortcode', '')

                        # Récupérer les vues (peut nécessiter un appel supplémentaire)
                        view_count = post.get('video_view_count', 0)
                        like_count = post.get('edge_liked_by', {}).get('count', 0) or post.get('like_count', 0)
                        comment_count = post.get('edge_media_to_comment', {}).get('count', 0) or post.get('comment_count', 0)

                        # Calculer le taux d'engagement
                        engagement_rate = 0.0
                        if view_count and view_count > 0:
                            engagement_rate = (like_count + comment_count) / view_count

                        # Description
                        caption = ''
                        edges = post.get('edge_media_to_caption', {}).get('edges', [])
                        if edges:
                            caption = edges[0].get('node', {}).get('text', '')

                        video_data = {
                            'id': shortcode,
                            'author': username,
                            'desc': caption,
                            'likes': like_count,
                            'views': view_count,
                            'shares': 0,
                            'comments': comment_count,
                            'video_url': f"https://www.instagram.com/p/{shortcode}/",
                            'music': None,
                            'create_time': post.get('taken_at_timestamp', 0),
                            'platform': 'instagram',
                            'engagement_rate': engagement_rate
                        }
                        videos.append(video_data)
                        video_count += 1

                        if video_count >= count:
                            break

                except Exception as e:
                    logger.debug(f"Erreur extraction post: {e}")
                    continue

            logger.info(f"✓ {len(videos)} vidéos Instagram récupérées de @{username}")
            return videos

        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or '403' in error_msg:
                logger.error(f"Erreur d'accès Instagram pour @{username}: {e}")
                logger.warning("⚠️  Instagram bloque les requêtes. Essayez avec des cookies.")
            else:
                logger.error(f"Erreur lors de la récupération des vidéos de @{username}: {e}")
            return videos

    def _scrape_profile_page(self, username: str, count: int) -> List[Dict]:
        """Scraper la page profil pour obtenir les posts"""
        posts = []

        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                # Chercher les données JSON dans la page
                # Pattern pour trouver les données de posts
                patterns = [
                    r'window\._sharedData\s*=\s*({.+?});</script>',
                    r'window\.__additionalDataLoaded\s*\([^,]+,\s*({.+?})\);',
                ]

                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            # Extraire les posts selon la structure
                            user_data = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {})
                            edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])

                            for edge in edges[:count]:
                                posts.append(edge.get('node', {}))
                            break
                        except:
                            continue

        except Exception as e:
            logger.debug(f"Erreur scraping page profil: {e}")

        return posts

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
