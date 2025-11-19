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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })

        # Charger les cookies si disponibles (REQUIS pour Instagram)
        cookies_file = getattr(config, 'INSTAGRAM_COOKIES_FILE', None)
        if cookies_file and os.path.exists(cookies_file):
            try:
                logger.info(f"Chargement des cookies Instagram depuis: {cookies_file}")
                self._load_cookies_from_json(cookies_file)
                self.authenticated = True
                logger.info("✓ Cookies chargés")
            except Exception as e:
                logger.warning(f"⚠️  Impossible de charger les cookies: {e}")
                logger.warning("⚠️  Les cookies sont REQUIS pour scraper Instagram!")
        else:
            logger.warning("⚠️  Fichier cookies non trouvé!")
            logger.warning("⚠️  Instagram nécessite des cookies pour fonctionner.")
            logger.info("Créez le fichier instagram_cookies.json avec Cookie-Editor")

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
                        logger.info("✓ sessionid trouvé")

        logger.info(f"✓ {len(cookies)} cookies chargés")

        if not sessionid_found:
            logger.warning("⚠️  Cookie 'sessionid' non trouvé!")
            logger.warning("   Assurez-vous d'être connecté à Instagram avant d'exporter les cookies.")

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

            # Récupérer la page profil
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                logger.error(f"Erreur HTTP {response.status_code} pour @{username}")
                return videos

            # Chercher les données JSON dans la page HTML
            posts = self._extract_posts_from_html(response.text, username)

            if not posts:
                logger.warning(f"Aucun post trouvé pour @{username}")
                # Debug: afficher un extrait de la réponse
                if 'login' in response.url.lower() or 'accounts/login' in response.text.lower():
                    logger.error("⚠️  Instagram redirige vers la page de login!")
                    logger.error("   Vos cookies sont invalides ou expirés.")
                return videos

            video_count = 0
            for post in posts:
                try:
                    # Vérifier si c'est une vidéo
                    is_video = post.get('is_video', False)

                    if is_video:
                        shortcode = post.get('shortcode', '')

                        # Récupérer les stats
                        view_count = post.get('video_view_count', 0)
                        like_count = post.get('edge_liked_by', {}).get('count', 0) or post.get('edge_media_preview_like', {}).get('count', 0)
                        comment_count = post.get('edge_media_to_comment', {}).get('count', 0) or post.get('edge_media_preview_comment', {}).get('count', 0)

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

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau pour @{username}: {e}")
            return videos
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos de @{username}: {e}")
            return videos

    def _extract_posts_from_html(self, html: str, username: str) -> List[Dict]:
        """Extraire les posts depuis le HTML de la page profil"""
        posts = []

        # Méthode 1: Chercher dans window._sharedData (ancien format)
        match = re.search(r'window\._sharedData\s*=\s*({.+?});</script>', html)
        if match:
            try:
                data = json.loads(match.group(1))
                user_data = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {})
                edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                for edge in edges:
                    posts.append(edge.get('node', {}))
                if posts:
                    logger.debug(f"Trouvé {len(posts)} posts via _sharedData")
                    return posts
            except Exception as e:
                logger.debug(f"Erreur parsing _sharedData: {e}")

        # Méthode 2: Chercher dans les scripts JSON (nouveau format)
        # Instagram stocke maintenant les données dans des balises script avec type="application/json"
        json_patterns = [
            r'<script type="application/json"[^>]*>({.+?})</script>',
            r'"xdt_api__v1__feed__user_timeline_graphql_connection":\s*({.+?})\s*[,}]',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match_str in matches:
                try:
                    data = json.loads(match_str)
                    # Chercher récursivement les posts
                    found_posts = self._find_posts_in_data(data)
                    if found_posts:
                        posts.extend(found_posts)
                except:
                    continue

        if posts:
            logger.debug(f"Trouvé {len(posts)} posts via scripts JSON")
            return posts

        # Méthode 3: Chercher les shortcodes directement dans le HTML
        shortcodes = re.findall(r'/p/([A-Za-z0-9_-]+)/', html)
        shortcodes = list(set(shortcodes))  # Dédupliquer

        if shortcodes:
            logger.debug(f"Trouvé {len(shortcodes)} shortcodes dans le HTML")
            # Créer des posts basiques avec juste le shortcode
            for sc in shortcodes[:20]:  # Limiter à 20
                posts.append({
                    'shortcode': sc,
                    'is_video': True,  # On suppose que c'est une vidéo, sera filtré plus tard
                })

        return posts

    def _find_posts_in_data(self, data, depth=0) -> List[Dict]:
        """Chercher récursivement les posts dans une structure JSON"""
        posts = []

        if depth > 10:  # Éviter la récursion infinie
            return posts

        if isinstance(data, dict):
            # Chercher les clés qui contiennent des posts
            if 'edges' in data:
                edges = data['edges']
                if isinstance(edges, list):
                    for edge in edges:
                        if isinstance(edge, dict) and 'node' in edge:
                            node = edge['node']
                            if isinstance(node, dict) and ('shortcode' in node or 'id' in node):
                                posts.append(node)

            # Chercher dans edge_owner_to_timeline_media
            if 'edge_owner_to_timeline_media' in data:
                media = data['edge_owner_to_timeline_media']
                if isinstance(media, dict) and 'edges' in media:
                    for edge in media['edges']:
                        if isinstance(edge, dict) and 'node' in edge:
                            posts.append(edge['node'])

            # Récursion dans les valeurs
            for value in data.values():
                posts.extend(self._find_posts_in_data(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                posts.extend(self._find_posts_in_data(item, depth + 1))

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
