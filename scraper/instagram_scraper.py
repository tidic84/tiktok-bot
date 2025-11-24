"""Scraper Instagram utilisant instaloader pour récupérer des vidéos"""
import logging
from typing import List, Dict
import time

import instaloader
from instaloader import Instaloader, Profile, Post
from instaloader.exceptions import (
    ProfileNotExistsException,
    LoginRequiredException,
    ConnectionException,
    QueryReturnedBadRequestException
)

logger = logging.getLogger(__name__)


class InstagramScraper:
    """Scraper qui récupère des vidéos Instagram via instaloader"""

    def __init__(self, config):
        """
        Initialiser le scraper

        Args:
            config: Objet de configuration
        """
        self.config = config
        self.loader = Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True  # Réduire les logs d'instaloader
        )

        # Charger la session si disponible
        username = getattr(config, 'INSTAGRAM_USERNAME', None)
        password = getattr(config, 'INSTAGRAM_PASSWORD', None)
        session_file = getattr(config, 'INSTAGRAM_SESSION_FILE', None)

        self.authenticated = False

        # Méthode 1 : Charger depuis un fichier de session
        if session_file and username:
            try:
                logger.info(f"Chargement de la session Instagram pour {username}...")
                self.loader.load_session_from_file(username, session_file)
                self.authenticated = True
                logger.info("✓ Session Instagram chargée avec succès")
            except FileNotFoundError:
                logger.warning(f"⚠️  Fichier de session non trouvé: {session_file}")
            except Exception as e:
                logger.warning(f"⚠️  Erreur chargement session: {e}")

        # Méthode 2 : Se connecter avec username/password
        if not self.authenticated and username and password:
            try:
                logger.info(f"Connexion à Instagram avec {username}...")
                self.loader.login(username, password)
                self.authenticated = True
                logger.info("✓ Connexion Instagram réussie")

                # Sauvegarder la session pour les prochaines fois
                if session_file:
                    try:
                        self.loader.save_session_to_file(session_file)
                        logger.info(f"✓ Session sauvegardée dans {session_file}")
                    except Exception as e:
                        logger.debug(f"Impossible de sauvegarder la session: {e}")
            except Exception as e:
                logger.error(f"❌ Erreur de connexion Instagram: {e}")

        if not self.authenticated:
            logger.warning("⚠️  Instagram non authentifié!")
            logger.warning("   Ajoutez INSTAGRAM_USERNAME et INSTAGRAM_PASSWORD dans config.py")
            logger.warning("   OU créez une session avec: instaloader -l USERNAME")

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

            # Récupérer le profil
            try:
                profile = Profile.from_username(self.loader.context, username)
            except ProfileNotExistsException:
                logger.warning(f"❌ Profil @{username} n'existe pas")
                return videos
            except LoginRequiredException:
                logger.error("❌ Authentification requise pour accéder à ce profil")
                logger.error("   Configurez INSTAGRAM_USERNAME et INSTAGRAM_PASSWORD")
                return videos
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'accès au profil @{username}: {e}")
                return videos

            # Vérifier si le profil est privé
            if profile.is_private and not profile.followed_by_viewer:
                logger.warning(f"⚠️  Profil @{username} est privé et non suivi")
                return videos

            # Parcourir les posts du profil
            video_count = 0
            post_count = 0
            max_posts = count * 3  # Parcourir plus de posts pour trouver assez de vidéos

            for post in profile.get_posts():
                post_count += 1

                # Limiter le nombre de posts parcourus
                if post_count > max_posts:
                    logger.debug(f"Limite de {max_posts} posts atteinte")
                    break

                # Filtrer uniquement les vidéos
                if not post.is_video:
                    continue

                try:
                    # Extraire les métadonnées
                    video_data = {
                        'id': post.shortcode,
                        'author': username,
                        'desc': post.caption or '',
                        'likes': post.likes,
                        'views': post.video_view_count if post.video_view_count else 0,
                        'shares': 0,  # Instagram ne fournit pas ce chiffre
                        'comments': post.comments,
                        'video_url': post.video_url,
                        'music': None,
                        'create_time': int(post.date_utc.timestamp()),
                        'platform': 'instagram',
                        'engagement_rate': 0.0
                    }

                    # Calculer le taux d'engagement
                    if video_data['views'] > 0:
                        video_data['engagement_rate'] = (
                            (video_data['likes'] + video_data['comments']) / video_data['views']
                        )

                    videos.append(video_data)
                    video_count += 1

                    logger.debug(
                        f"✓ Vidéo {post.shortcode}: "
                        f"{video_data['likes']:,} likes, "
                        f"{video_data['views']:,} vues, "
                        f"{video_data['comments']:,} commentaires"
                    )

                    # Arrêter si on a assez de vidéos
                    if video_count >= count:
                        break

                except Exception as e:
                    logger.debug(f"Erreur extraction post {post.shortcode}: {e}")
                    continue

            logger.info(f"✓ {len(videos)} vidéos Instagram récupérées de @{username}")
            return videos

        except QueryReturnedBadRequestException as e:
            logger.error(f"❌ Instagram a retourné une erreur (rate limit?): {e}")
            logger.info("💡 Attendez quelques minutes avant de réessayer")
            return videos

        except ConnectionException as e:
            logger.error(f"❌ Erreur de connexion Instagram: {e}")
            return videos

        except Exception as e:
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

        for i, creator in enumerate(creators):
            # Nettoyer le nom d'utilisateur (enlever @ si présent)
            creator = creator.lstrip('@')

            try:
                videos = self.get_user_videos(creator, count_per_creator)
                all_videos.extend(videos)

                # Pause entre créateurs pour éviter rate limiting
                if i < len(creators) - 1 and videos:
                    wait_time = 5
                    logger.info(f"⏳ Pause de {wait_time} secondes avant le prochain créateur...")
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"❌ Erreur pour le créateur @{creator}: {e}")
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
