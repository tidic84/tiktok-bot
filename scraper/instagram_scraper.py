"""Scraper Instagram utilisant instaloader pour récupérer des vidéos"""
import logging
from typing import List, Dict, Optional
import time
import random
import os

import instaloader
from instaloader import Instaloader, Profile, Post, RateController
from instaloader.exceptions import (
    ProfileNotExistsException,
    LoginRequiredException,
    ConnectionException,
    QueryReturnedBadRequestException,
    TooManyRequestsException
)

logger = logging.getLogger(__name__)


class ConservativeRateController(RateController):
    """RateController très conservateur pour éviter le rate limiting Instagram"""

    def sleep(self, secs):
        """Dormir avec un multiplicateur pour être plus conservateur"""
        # Multiplier par 2-3 le temps de sleep recommandé par instaloader
        actual_sleep = secs * random.uniform(2.0, 3.0)
        logger.debug(f"Sleep {actual_sleep:.1f}s (recommandé: {secs}s)")
        time.sleep(actual_sleep)

    def count_per_slidingwindow(self, query_type):
        """Réduire le nombre de requêtes par fenêtre glissante"""
        # Instaloader par défaut permet ~200 requêtes/heure
        # On divise par 4 pour être ultra conservateur : ~50 requêtes/heure
        default_count = super().count_per_slidingwindow(query_type)
        return max(1, default_count // 4)


class InstagramScraper:
    """Scraper qui récupère des vidéos Instagram via instaloader"""

    def __init__(self, config):
        """
        Initialiser le scraper

        Args:
            config: Objet de configuration
        """
        self.config = config

        # Créer le dossier de téléchargement
        from pathlib import Path
        self.download_folder = Path(config.DOWNLOAD_FOLDER)
        self.download_folder.mkdir(exist_ok=True)

        # CRITIQUE: Monkeypatch requests AVANT de créer l'Instaloader
        # Pour désactiver SSL avec les proxies (Bright Data, etc.)
        import requests
        import urllib3

        # Sauvegarder la méthode originale
        original_request = requests.Session.request

        # Créer une version qui force verify=False
        def patched_request(self, method, url, **kwargs):
            kwargs['verify'] = False
            return original_request(self, method, url, **kwargs)

        # Appliquer le patch
        requests.Session.request = patched_request
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.info("✓ SSL désactivé globalement pour les proxies")

        # Utiliser un RateController conservateur
        self.loader = Instaloader(
            download_pictures=False,
            download_videos=False,  # DÉSACTIVER - on télécharge manuellement pour éviter les problèmes
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,  # Réduire les logs d'instaloader
            rate_controller=lambda ctx: ConservativeRateController(ctx)
        )

        logger.info("✓ RateController conservateur activé (délais x2-3)")

        # NE PAS configurer de headers personnalisés pour GraphQL
        # Les proxies Bright Data ont des règles strictes sur les headers
        # Laisser instaloader gérer les headers par défaut
        # On configurera des headers spécifiques seulement pour le téléchargement des vidéos

        logger.info("✓ Configuration initiale terminée")

        # Configurer le proxy si disponible
        self._setup_proxy()

        # MODE ANONYME: Ne pas utiliser d'authentification pour éviter les rate limits
        # Les profils publics peuvent être scrapés sans authentification
        # Cela contourne le rate limit actuel sur le compte authentifié

        self.authenticated = False

        logger.warning("⚠️  Mode ANONYME activé (pas d'authentification)")
        logger.info("   Les profils privés ne seront pas accessibles")
        logger.info("   Mais les profils publics fonctionneront sans rate limit")

        # Note: On pourrait réactiver l'authentification plus tard
        # Pour l'instant, on privilégie le fonctionnement immédiat

    def _setup_proxy(self):
        """Configurer le proxy pour instaloader"""
        # Récupérer la configuration proxy
        proxy_list = getattr(self.config, 'INSTAGRAM_PROXIES', [])
        single_proxy = getattr(self.config, 'INSTAGRAM_PROXY', None)

        # Si un proxy unique est fourni, le convertir en liste
        if single_proxy and not proxy_list:
            proxy_list = [single_proxy]

        if not proxy_list:
            return  # Pas de proxy configuré

        # Initialiser la rotation de proxies
        self.proxy_list = proxy_list
        self.proxy_index = 0
        self.current_proxy = None

        # Configurer le premier proxy
        self._rotate_proxy()

    def _rotate_proxy(self):
        """Changer de proxy (rotation)"""
        if not hasattr(self, 'proxy_list') or not self.proxy_list:
            return

        # Prendre le prochain proxy dans la liste
        self.current_proxy = self.proxy_list[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)

        # IMPORTANT: Configurer le proxy via variables d'environnement
        # C'est la SEULE méthode qui fonctionne correctement avec instaloader
        os.environ['HTTP_PROXY'] = self.current_proxy
        os.environ['HTTPS_PROXY'] = self.current_proxy

        # Aussi mettre à jour la session (au cas où)
        proxies = {
            'http': self.current_proxy,
            'https': self.current_proxy,
        }
        self.loader.context._session.proxies = proxies

        # Masquer le mot de passe dans les logs
        proxy_display = self.current_proxy
        if '@' in proxy_display:
            # Format: http://user:pass@host:port -> http://user:***@host:port
            parts = proxy_display.split('@')
            if len(parts) == 2:
                credentials = parts[0].split('//')[-1]
                if ':' in credentials:
                    user = credentials.split(':')[0]
                    proxy_display = proxy_display.replace(credentials, f"{user}:***")

        logger.info(f"🔄 Proxy configuré: {proxy_display}")
        if len(self.proxy_list) > 1:
            logger.info(f"   (Proxy {self.proxy_index}/{len(self.proxy_list)} - rotation activée)")

    def _download_video_with_instaloader(self, post: Post, video_data: Dict) -> Optional[str]:
        """
        Télécharger une vidéo Instagram directement via l'URL

        Args:
            post: Objet Post d'instaloader
            video_data: Dictionnaire de données de la vidéo

        Returns:
            Chemin local du fichier téléchargé ou None si échec
        """
        import requests
        from pathlib import Path

        try:
            # Obtenir l'URL de la vidéo
            video_url = post.video_url
            if not video_url:
                logger.warning(f"Pas d'URL vidéo pour {post.shortcode}")
                return None

            # Générer un nom de fichier propre
            desc = video_data.get('desc', '')
            filename = self._sanitize_filename(desc)

            # Si le nom est vide ou générique, utiliser des emojis
            if not filename or filename == 'video' or len(filename) < 3:
                filename = self._generate_emoji_name()

            # Chemin final
            final_path = self.download_folder / f"{filename}.mp4"

            # Gérer les collisions de noms
            if final_path.exists():
                counter = 1
                while final_path.exists():
                    final_path = self.download_folder / f"{filename}_{counter}.mp4"
                    counter += 1

            # Télécharger directement avec requests
            # Utiliser les proxies configurés et désactiver SSL
            proxies = {
                'http': self.current_proxy,
                'https': self.current_proxy,
            } if hasattr(self, 'current_proxy') and self.current_proxy else None

            # Headers pour simuler un navigateur et éviter les erreurs 502
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': f'https://www.instagram.com/p/{post.shortcode}/',
                'Origin': 'https://www.instagram.com',
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }

            logger.debug(f"Téléchargement direct de {video_url[:80]}...")

            # Essayer d'abord avec proxy
            try:
                response = requests.get(
                    video_url,
                    headers=headers,
                    proxies=proxies,
                    verify=False,  # Désactiver SSL
                    stream=True,
                    timeout=60
                )
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # Si erreur 402 (proxy rejected), réessayer sans proxy
                if '402' in str(e):
                    logger.debug(f"Erreur 402 avec proxy, retry sans proxy...")
                    response = requests.get(
                        video_url,
                        headers=headers,
                        proxies=None,  # Sans proxy
                        verify=False,
                        stream=True,
                        timeout=60
                    )
                    response.raise_for_status()
                else:
                    raise

            # Écrire le fichier
            with open(final_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = final_path.stat().st_size / (1024 * 1024)

            if file_size < 0.1:  # Fichier trop petit, probablement une erreur
                logger.warning(f"Fichier trop petit ({file_size:.2f} MB), probablement invalide")
                final_path.unlink()
                return None

            logger.info(f"✓ Vidéo {post.shortcode} téléchargée ({file_size:.2f} MB) -> {final_path.name}")
            return str(final_path.absolute())

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur HTTP lors du téléchargement de {post.shortcode}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur téléchargement vidéo {post.shortcode}: {e}")
            logger.debug(f"Détails:", exc_info=True)
            return None

    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """
        Nettoyer un texte pour en faire un nom de fichier valide

        Args:
            text: Texte à nettoyer
            max_length: Longueur max du nom

        Returns:
            Nom de fichier nettoyé
        """
        import re

        if not text:
            return "video"

        # Supprimer les hashtags pour le nom de fichier (garder les emojis)
        text = re.sub(r'#\w+', '', text)  # Supprimer hashtags
        text = re.sub(r'[^\w\s\U0001F300-\U0001F9FF-]', '', text)  # Garder alphanumériques, espaces et emojis
        text = re.sub(r'\s+', ' ', text.strip())  # Normaliser espaces
        text = text[:max_length]  # Limiter la longueur

        return text if text else "video"

    def _generate_emoji_name(self) -> str:
        """
        Générer un nom basé sur des vrais emojis aléatoires

        Returns:
            Chaîne d'emojis pour le nom de fichier
        """
        import random

        # Liste d'emojis populaires sur Instagram
        emojis = [
            '🔥', '⭐', '❤️', '✨', '🚀',
            '💃', '🎵', '📹', '🔝', '💯',
            '😎', '🤩', '👏', '💪', '🎉'
        ]

        # Choisir 3-5 emojis au hasard
        num_emojis = random.randint(3, 5)
        selected = random.sample(emojis, num_emojis)

        return ''.join(selected)

    def _disable_proxy_temporarily(self):
        """Désactiver temporairement le proxy pour les requêtes GraphQL"""
        if 'HTTP_PROXY' in os.environ:
            self._saved_http_proxy = os.environ.pop('HTTP_PROXY', None)
        if 'HTTPS_PROXY' in os.environ:
            self._saved_https_proxy = os.environ.pop('HTTPS_PROXY', None)

        # Sauvegarder et retirer les proxies de la session
        self._saved_session_proxies = self.loader.context._session.proxies.copy()
        self.loader.context._session.proxies = {}

        logger.debug("🔓 Proxies désactivés temporairement pour GraphQL")

    def _restore_proxy(self):
        """Restaurer les proxies après les requêtes GraphQL"""
        if hasattr(self, '_saved_http_proxy') and self._saved_http_proxy:
            os.environ['HTTP_PROXY'] = self._saved_http_proxy
        if hasattr(self, '_saved_https_proxy') and self._saved_https_proxy:
            os.environ['HTTPS_PROXY'] = self._saved_https_proxy

        if hasattr(self, '_saved_session_proxies'):
            self.loader.context._session.proxies = self._saved_session_proxies

        logger.debug("🔒 Proxies restaurés pour le téléchargement")

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

            # IMPORTANT: Désactiver les proxies pour les requêtes GraphQL
            # Les proxies Bright Data rejettent les requêtes GraphQL avec "Bad headers: referer"
            # On utilisera les proxies SEULEMENT pour télécharger les vidéos
            self._disable_proxy_temporarily()

            # Récupérer le profil avec retry en cas de rate limit temporaire
            max_retries = 3
            retry_delay = 60  # 60 secondes entre les retries
            profile = None

            for attempt in range(max_retries):
                try:
                    profile = Profile.from_username(self.loader.context, username)
                    break  # Succès, sortir de la boucle
                except ProfileNotExistsException:
                    logger.warning(f"❌ Profil @{username} n'existe pas")
                    return videos
                except LoginRequiredException:
                    logger.error("❌ Authentification requise pour accéder à ce profil")
                    logger.error("   Configurez INSTAGRAM_USERNAME et INSTAGRAM_PASSWORD")
                    return videos
                except ConnectionException as e:
                    error_msg = str(e).lower()
                    # Détecter rate limiting
                    if ('401' in error_msg or 'wait a few minutes' in error_msg) and attempt < max_retries - 1:
                        logger.warning(f"⏳ Rate limit détecté (tentative {attempt + 1}/{max_retries})")
                        logger.info(f"   Attente de {retry_delay} secondes avant nouvelle tentative...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"❌ Erreur de connexion: {e}")
                        return videos
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'accès au profil @{username}: {e}")
                    return videos

            if not profile:
                logger.error(f"❌ Impossible de récupérer le profil @{username} après {max_retries} tentatives")
                return videos

            # Vérifier si le profil est privé
            if profile.is_private and not profile.followed_by_viewer:
                logger.warning(f"⚠️  Profil @{username} est privé et non suivi")
                return videos

            # Parcourir les posts du profil LENTEMENT
            video_count = 0
            post_count = 0
            max_posts = count * 3  # Parcourir plus de posts pour trouver assez de vidéos

            # Délais entre posts (configuration)
            min_delay_between_posts = getattr(self.config, 'INSTAGRAM_MIN_DELAY_BETWEEN_POSTS', 3)
            max_delay_between_posts = getattr(self.config, 'INSTAGRAM_MAX_DELAY_BETWEEN_POSTS', 7)

            for post in profile.get_posts():
                post_count += 1

                # IMPORTANT: Délai AVANT de traiter chaque post (sauf le premier)
                if post_count > 1:
                    delay = random.uniform(min_delay_between_posts, max_delay_between_posts)
                    logger.debug(f"Pause {delay:.1f}s avant post #{post_count}")
                    time.sleep(delay)

                # Limiter le nombre de posts parcourus
                if post_count > max_posts:
                    logger.debug(f"Limite de {max_posts} posts atteinte")
                    break

                # Filtrer uniquement les vidéos
                if not post.is_video:
                    continue

                try:
                    # Extraire les métadonnées AVANT de télécharger
                    video_data = {
                        'id': post.shortcode,
                        'author': username,
                        'desc': post.caption or '',
                        'likes': post.likes,
                        'views': post.video_view_count if post.video_view_count else 0,
                        'shares': 0,  # Instagram ne fournit pas ce chiffre
                        'comments': post.comments,
                        'video_url': post.video_url,  # Garder l'URL pour référence
                        'music': None,
                        'create_time': int(post.date_utc.timestamp()),
                        'platform': 'instagram',
                        'engagement_rate': 0.0,
                        'local_path': None  # Sera rempli après téléchargement
                    }

                    # Calculer le taux d'engagement
                    if video_data['views'] > 0:
                        video_data['engagement_rate'] = (
                            (video_data['likes'] + video_data['comments']) / video_data['views']
                        )

                    logger.debug(
                        f"✓ Vidéo {post.shortcode}: "
                        f"{video_data['likes']:,} likes, "
                        f"{video_data['views']:,} vues, "
                        f"{video_data['comments']:,} commentaires"
                    )

                    # TÉLÉCHARGER la vidéo IMMÉDIATEMENT avec instaloader
                    local_path = self._download_video_with_instaloader(post, video_data)

                    if local_path:
                        video_data['local_path'] = local_path
                        videos.append(video_data)
                        video_count += 1
                    else:
                        logger.warning(f"⚠️  Échec du téléchargement de {post.shortcode}, ignorée")

                    # Arrêter si on a assez de vidéos
                    if video_count >= count:
                        break

                except Exception as e:
                    logger.debug(f"Erreur extraction/téléchargement post {post.shortcode}: {e}")
                    continue

            # Restaurer les proxies
            self._restore_proxy()

            logger.info(f"✓ {len(videos)} vidéos Instagram récupérées de @{username}")
            return videos

        except QueryReturnedBadRequestException as e:
            self._restore_proxy()
            logger.error(f"❌ Instagram a retourné une erreur (rate limit?): {e}")
            logger.info("💡 Attendez quelques minutes avant de réessayer")
            raise  # Propager l'erreur pour arrêter le scraping

        except TooManyRequestsException as e:
            self._restore_proxy()
            logger.error(f"❌ Rate limit Instagram détecté: {e}")
            logger.info("💡 Instagram limite le nombre de requêtes. Attendez 1-2 heures.")
            raise  # Propager l'erreur pour arrêter le scraping

        except ConnectionException as e:
            self._restore_proxy()
            logger.error(f"❌ Erreur de connexion Instagram: {e}")
            return videos

        except Exception as e:
            self._restore_proxy()
            error_msg = str(e).lower()
            # Détecter les erreurs 401 (rate limiting)
            if '401' in error_msg or 'unauthorized' in error_msg or 'wait a few minutes' in error_msg:
                logger.error(f"❌ Rate limit Instagram détecté: {e}")
                logger.info("💡 Instagram limite le nombre de requêtes. Attendez 1-2 heures.")
                raise  # Propager l'erreur pour arrêter le scraping

            logger.error(f"❌ Erreur lors de la récupération des vidéos de @{username}: {e}")
            logger.debug("Détails de l'erreur:", exc_info=True)
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

        if not creators:
            logger.warning("⚠️  Aucun créateur Instagram configuré")
            return all_videos

        logger.info(f"📥 Récupération depuis {len(creators)} créateur(s) Instagram...")

        # Récupérer le délai depuis la config (30-60 secondes par défaut)
        min_delay = getattr(self.config, 'INSTAGRAM_MIN_DELAY_BETWEEN_CREATORS', 30)
        max_delay = getattr(self.config, 'INSTAGRAM_MAX_DELAY_BETWEEN_CREATORS', 60)

        for i, creator in enumerate(creators):
            # Nettoyer le nom d'utilisateur (enlever @ si présent)
            creator = creator.lstrip('@')

            # Rotation de proxy si plusieurs proxies configurés
            if hasattr(self, 'proxy_list') and len(self.proxy_list) > 1:
                logger.info(f"[{i+1}/{len(creators)}] Rotation du proxy...")
                self._rotate_proxy()

            try:
                logger.info(f"[{i+1}/{len(creators)}] Récupération de @{creator}...")
                videos = self.get_user_videos(creator, count_per_creator)
                all_videos.extend(videos)

                # Pause PLUS LONGUE entre créateurs pour éviter rate limiting
                if i < len(creators) - 1:
                    # Délai aléatoire pour paraître plus humain
                    wait_time = random.randint(min_delay, max_delay)
                    logger.info(f"⏳ Pause de {wait_time} secondes avant le prochain créateur...")
                    logger.info(f"   (Instagram limite les requêtes rapides)")
                    time.sleep(wait_time)

            except (QueryReturnedBadRequestException, TooManyRequestsException):
                # Rate limiting détecté, arrêter complètement
                logger.error(f"⚠️  Rate limiting détecté lors du scraping de @{creator}")
                logger.error(f"⚠️  Arrêt du scraping pour éviter le bannissement du compte")
                logger.info(f"💡 {len(all_videos)} vidéos récupérées avant le rate limit")
                break

            except Exception as e:
                error_msg = str(e).lower()
                # Détecter les erreurs 401 (rate limiting)
                if '401' in error_msg or 'unauthorized' in error_msg or 'wait a few minutes' in error_msg:
                    logger.error(f"⚠️  Rate limiting détecté lors du scraping de @{creator}")
                    logger.error(f"⚠️  Arrêt du scraping pour éviter le bannissement du compte")
                    logger.info(f"💡 {len(all_videos)} vidéos récupérées avant le rate limit")
                    break

                logger.error(f"❌ Erreur pour le créateur @{creator}: {e}")
                logger.info(f"   Passage au créateur suivant...")
                continue

        # Retirer les doublons basés sur l'ID
        unique_videos = {v['id']: v for v in all_videos if v.get('id')}.values()
        logger.info(f"📊 Total: {len(unique_videos)} vidéos Instagram uniques de {len(creators)} créateurs")

        return list(unique_videos)

    def close(self):
        """Fermer le scraper (pour compatibilité avec l'ancienne interface)"""
        # Instaloader n'a pas besoin de fermeture explicite
        logger.debug("Instagram scraper fermé")

    def __del__(self):
        """Destructeur pour fermer le scraper"""
        self.close()
