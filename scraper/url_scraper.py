"""Scraper alternatif utilisant des URLs ou créateurs TikTok spécifiques"""
import logging
from typing import List, Dict
import subprocess
import json
import re

logger = logging.getLogger(__name__)


class URLScraper:
    """Scraper qui récupère des vidéos depuis des URLs ou créateurs spécifiques"""
    
    def __init__(self, config):
        """
        Initialiser le scraper
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        logger.info("URLScraper initialisé")
    
    def get_user_videos(self, username: str, count: int = 10) -> List[Dict]:
        """
        Récupérer les vidéos d'un utilisateur TikTok via yt-dlp
        
        Args:
            username: Nom d'utilisateur TikTok (sans @)
            count: Nombre maximum de vidéos à récupérer
            
        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        videos = []
        
        try:
            logger.info(f"Récupération des vidéos de @{username}...")
            
            # URL du profil TikTok
            profile_url = f"https://www.tiktok.com/@{username}"
            
            # Commande yt-dlp pour récupérer les métadonnées sans télécharger
            cmd = [
                'yt-dlp',
                '--dump-json',  # Sortie JSON
                '--playlist-end', str(count),  # Limiter le nombre de vidéos
                '--no-warnings',
                profile_url
            ]
            
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
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
                    # Récupérer la description COMPLÈTE (yt-dlp la fournit complète)
                    description = video_info.get('description', '')
                    video_data = {
                        'id': video_info.get('id', ''),
                        'author': username,
                        'desc': description,  # Description COMPLÈTE avec hashtags originaux
                        'likes': video_info.get('like_count', 0),
                        'views': video_info.get('view_count', 0),
                        'shares': video_info.get('repost_count', 0),
                        'comments': video_info.get('comment_count', 0),
                        'video_url': video_info.get('webpage_url', ''),
                        'music': video_info.get('track', None),
                        'create_time': video_info.get('timestamp', 0)
                    }
                    videos.append(video_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Erreur parsing JSON: {e}")
                    continue
            
            logger.info(f"✓ {len(videos)} vidéos récupérées de @{username}")
            return videos
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de la récupération des vidéos de @{username}")
            return videos
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos de @{username}: {e}")
            return videos

    def get_videos_from_creators(self, creators: List[str], count_per_creator: int = 10) -> List[Dict]:
        """
        Récupérer des vidéos depuis une liste de créateurs
        
        Args:
            creators: Liste de noms d'utilisateurs TikTok
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
        logger.info(f"📊 Total: {len(unique_videos)} vidéos uniques de {len(creators)} créateurs")
        
        return list(unique_videos)
    
    def search_by_keyword(self, keyword: str, count: int = 10) -> List[Dict]:
        """
        Rechercher des vidéos TikTok par mot-clé avec yt-dlp
        
        LIMITATION: yt-dlp ne supporte pas la recherche TikTok directement.
        Cette méthode utilise l'URL de recherche TikTok, mais cela nécessite
        que TikTok permette l'accès sans connexion.
        
        RECOMMANDATION: Utilisez plutôt le mode 'creators' pour plus de fiabilité.
        
        Args:
            keyword: Mot-clé ou hashtag à rechercher
            count: Nombre de vidéos à récupérer
            
        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        videos = []
        
        try:
            logger.info(f"🔍 Recherche de '{keyword}' sur TikTok...")
            
            # Nettoyer le mot-clé (enlever # si présent et encoder pour URL)
            clean_keyword = keyword.lstrip('#')
            
            # Essayer différentes approches
            
            # Approche 1: URL de hashtag TikTok
            if keyword.startswith('#') or not ' ' in clean_keyword:
                hashtag_url = f"https://www.tiktok.com/tag/{clean_keyword}"
                logger.info(f"Tentative avec hashtag URL: {hashtag_url}")
                
                cmd = [
                    'yt-dlp',
                    '--dump-json',
                    '--playlist-end', str(count),
                    '--no-warnings',
                    '--extractor-args', 'tiktok:webpage_download=true',
                    hashtag_url
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=90
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Parser les résultats
                    for line in result.stdout.strip().split('\n'):
                        if not line.strip():
                            continue
                        
                        try:
                            video_info = json.loads(line)
                            # Récupérer la description COMPLÈTE
                            description = video_info.get('description', '')
                            video_data = {
                                'id': video_info.get('id', ''),
                                'author': video_info.get('uploader_id', 'unknown'),
                                'desc': description,  # Description COMPLÈTE avec hashtags originaux
                                'likes': video_info.get('like_count', 0),
                                'views': video_info.get('view_count', 0),
                                'shares': video_info.get('repost_count', 0),
                                'comments': video_info.get('comment_count', 0),
                                'video_url': video_info.get('webpage_url', ''),
                                'music': video_info.get('track', None),
                                'create_time': video_info.get('timestamp', 0),
                                'search_keyword': keyword
                            }
                            videos.append(video_data)
                        except json.JSONDecodeError:
                            continue
            
            if not videos:
                logger.warning(
                    f"⚠️  La recherche par mot-clé ne fonctionne pas bien avec yt-dlp.\n"
                    f"   RECOMMANDATION: Utilisez le mode 'creators' à la place.\n"
                    f"   Exemple: SCRAPING_MODE = 'creators' et ajoutez des créateurs dans votre niche."
                )
            
            logger.info(f"✓ {len(videos)} vidéos trouvées pour '{keyword}'")
            return videos
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de la recherche de '{keyword}'")
            return videos
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de '{keyword}': {e}")
            return videos
    
    def get_videos_from_search(self, keywords: List[str], count_per_keyword: int = 10) -> List[Dict]:
        """
        Rechercher des vidéos depuis une liste de mots-clés
        
        Args:
            keywords: Liste de mots-clés/hashtags à rechercher
            count_per_keyword: Nombre de vidéos par mot-clé
            
        Returns:
            Liste combinée de toutes les vidéos
        """
        all_videos = []
        
        for keyword in keywords:
            videos = self.search_by_keyword(keyword, count_per_keyword)
            all_videos.extend(videos)
        
        # Retirer les doublons
        unique_videos = {v['id']: v for v in all_videos if v.get('id')}.values()
        logger.info(f"📊 Total: {len(unique_videos)} vidéos uniques pour {len(keywords)} mots-clés")
        
        return list(unique_videos)

