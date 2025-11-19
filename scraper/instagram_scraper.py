"""Scraper Instagram utilisant Selenium pour exécuter JavaScript"""
import logging
from typing import List, Dict
import time
import os
import json
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class InstagramScraper:
    """Scraper qui récupère des vidéos Instagram via Selenium"""

    def __init__(self, config):
        """
        Initialiser le scraper

        Args:
            config: Objet de configuration
        """
        self.config = config
        self.driver = None
        self.authenticated = False
        self.cookies_file = getattr(config, 'INSTAGRAM_COOKIES_FILE', None)

        # Initialiser le driver
        self._init_driver()

        # Charger les cookies si disponibles
        if self.cookies_file and os.path.exists(self.cookies_file):
            self._load_cookies()
        else:
            logger.warning("⚠️  Fichier cookies non trouvé!")
            logger.warning("⚠️  Instagram nécessite des cookies pour fonctionner.")
            logger.info("Créez le fichier instagram_cookies.json avec Cookie-Editor")

    def _init_driver(self):
        """Initialiser le driver Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Mode sans interface
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # User agent réaliste
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Configuration du proxy si spécifié
            proxy_url = getattr(self.config, 'PROXY_URL', None)
            if proxy_url:
                chrome_options.add_argument(f'--proxy-server={proxy_url}')
                logger.info(f"Proxy configuré: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Masquer webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✓ Selenium Chrome initialisé")

        except Exception as e:
            logger.error(f"Erreur initialisation Selenium: {e}")
            raise

    def _load_cookies(self):
        """Charger les cookies depuis le fichier JSON"""
        try:
            logger.info(f"Chargement des cookies depuis: {self.cookies_file}")

            # D'abord naviguer vers Instagram pour pouvoir ajouter les cookies
            self.driver.get("https://www.instagram.com/")
            time.sleep(2)

            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)

            sessionid_found = False
            cookies_added = 0

            for cookie in cookies:
                if isinstance(cookie, dict):
                    # Préparer le cookie pour Selenium
                    selenium_cookie = {
                        'name': cookie.get('name', ''),
                        'value': cookie.get('value', ''),
                        'domain': cookie.get('domain', '.instagram.com'),
                        'path': cookie.get('path', '/'),
                    }

                    # Normaliser le domaine
                    if 'instagram' in selenium_cookie['domain']:
                        selenium_cookie['domain'] = '.instagram.com'

                    try:
                        self.driver.add_cookie(selenium_cookie)
                        cookies_added += 1

                        if cookie.get('name') == 'sessionid':
                            sessionid_found = True
                    except Exception as e:
                        logger.debug(f"Cookie ignoré {cookie.get('name')}: {e}")

            logger.info(f"✓ {cookies_added} cookies chargés")

            if sessionid_found:
                logger.info("✓ sessionid trouvé")
                self.authenticated = True
            else:
                logger.warning("⚠️  Cookie 'sessionid' non trouvé!")

            # Rafraîchir pour appliquer les cookies
            self.driver.refresh()
            time.sleep(2)

        except Exception as e:
            logger.error(f"Erreur chargement cookies: {e}")

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

        if not self.driver:
            logger.error("Driver Selenium non initialisé")
            return videos

        try:
            logger.info(f"Récupération des vidéos Instagram de @{username}...")

            # Naviguer vers le profil
            url = f"https://www.instagram.com/{username}/"
            self.driver.get(url)

            # Attendre que la page charge
            time.sleep(3)

            # Vérifier si on est redirigé vers login
            if 'accounts/login' in self.driver.current_url:
                logger.error("⚠️  Instagram redirige vers la page de login!")
                logger.error("   Vos cookies sont invalides ou expirés.")
                return videos

            # Vérifier si le profil existe
            try:
                self.driver.find_element(By.XPATH, "//h2[contains(text(), \"Cette page n'est pas disponible\")]")
                logger.warning(f"Profil @{username} n'existe pas ou est privé")
                return videos
            except NoSuchElementException:
                pass

            # Attendre que les posts se chargent
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except TimeoutException:
                logger.warning(f"Timeout en attendant les posts de @{username}")
                return videos

            # Faire défiler pour charger plus de posts si nécessaire
            posts_data = []
            scroll_count = 0
            max_scrolls = 3

            while len(posts_data) < count * 2 and scroll_count < max_scrolls:
                # Extraire les données des posts depuis le HTML
                posts_data = self._extract_posts_from_page()

                if len(posts_data) >= count * 2:
                    break

                # Faire défiler vers le bas
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_count += 1

            # Filtrer et formater les vidéos
            video_count = 0
            for post in posts_data:
                try:
                    shortcode = post.get('shortcode', '')
                    is_video = post.get('is_video', False)

                    if is_video and shortcode:
                        video_data = {
                            'id': shortcode,
                            'author': username,
                            'desc': post.get('caption', ''),
                            'likes': post.get('likes', 0),
                            'views': post.get('views', 0),
                            'shares': 0,
                            'comments': post.get('comments', 0),
                            'video_url': f"https://www.instagram.com/p/{shortcode}/",
                            'music': None,
                            'create_time': post.get('timestamp', 0),
                            'platform': 'instagram',
                            'engagement_rate': 0.0
                        }

                        # Calculer engagement
                        if video_data['views'] > 0:
                            video_data['engagement_rate'] = (video_data['likes'] + video_data['comments']) / video_data['views']

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
            logger.error(f"Erreur lors de la récupération des vidéos de @{username}: {e}")
            return videos

    def _extract_posts_from_page(self) -> List[Dict]:
        """Extraire les données des posts depuis la page chargée"""
        posts = []

        try:
            # Méthode 1: Extraire depuis les scripts JSON dans la page
            scripts = self.driver.find_elements(By.TAG_NAME, "script")

            for script in scripts:
                try:
                    content = script.get_attribute('innerHTML')
                    if not content:
                        continue

                    # Chercher les données JSON
                    if 'edge_owner_to_timeline_media' in content or 'xdt_api__v1__feed' in content:
                        # Essayer de parser le JSON
                        json_match = re.search(r'\{[^{}]*"shortcode"[^{}]*\}', content)
                        if json_match:
                            # Parser le contenu complet
                            found = self._find_posts_in_text(content)
                            posts.extend(found)
                except:
                    continue

            # Méthode 2: Extraire les liens des posts depuis le DOM
            if not posts:
                post_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")

                seen_shortcodes = set()
                for link in post_links:
                    href = link.get_attribute('href')
                    if href:
                        # Extraire le shortcode
                        match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', href)
                        if match:
                            shortcode = match.group(1)
                            if shortcode not in seen_shortcodes:
                                seen_shortcodes.add(shortcode)

                                # Vérifier si c'est une vidéo (chercher l'icône vidéo)
                                is_video = False
                                try:
                                    parent = link.find_element(By.XPATH, "./..")
                                    # Chercher un indicateur de vidéo
                                    video_indicators = parent.find_elements(By.XPATH, ".//*[contains(@aria-label, 'Vidéo') or contains(@aria-label, 'Video') or contains(@aria-label, 'Reel')]")
                                    if video_indicators:
                                        is_video = True
                                    # Ou chercher l'icône SVG de vidéo
                                    svg_icons = parent.find_elements(By.TAG_NAME, "svg")
                                    for svg in svg_icons:
                                        if 'video' in str(svg.get_attribute('aria-label')).lower():
                                            is_video = True
                                            break
                                except:
                                    pass

                                # Si c'est un reel, c'est forcément une vidéo
                                if '/reel/' in href:
                                    is_video = True

                                posts.append({
                                    'shortcode': shortcode,
                                    'is_video': is_video,
                                    'likes': 0,
                                    'views': 0,
                                    'comments': 0,
                                    'caption': '',
                                    'timestamp': 0
                                })

            return posts

        except Exception as e:
            logger.debug(f"Erreur extraction posts: {e}")
            return posts

    def _find_posts_in_text(self, text: str) -> List[Dict]:
        """Chercher les posts dans le texte JSON"""
        posts = []

        try:
            # Chercher les patterns de posts
            shortcode_pattern = r'"shortcode"\s*:\s*"([A-Za-z0-9_-]+)"'
            is_video_pattern = r'"is_video"\s*:\s*(true|false)'
            likes_pattern = r'"edge_liked_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)'
            views_pattern = r'"video_view_count"\s*:\s*(\d+)'

            shortcodes = re.findall(shortcode_pattern, text)
            is_videos = re.findall(is_video_pattern, text)
            likes = re.findall(likes_pattern, text)
            views = re.findall(views_pattern, text)

            for i, shortcode in enumerate(shortcodes):
                is_video = is_videos[i].lower() == 'true' if i < len(is_videos) else False
                like_count = int(likes[i]) if i < len(likes) else 0
                view_count = int(views[i]) if i < len(views) else 0

                posts.append({
                    'shortcode': shortcode,
                    'is_video': is_video,
                    'likes': like_count,
                    'views': view_count,
                    'comments': 0,
                    'caption': '',
                    'timestamp': 0
                })

        except Exception as e:
            logger.debug(f"Erreur parsing posts: {e}")

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

    def close(self):
        """Fermer le driver Selenium"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("Driver Selenium fermé")
            except:
                pass

    def __del__(self):
        """Destructeur pour fermer le driver"""
        self.close()
