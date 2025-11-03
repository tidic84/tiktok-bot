"""Scraper TikTok utilisant TikTokApi"""
from TikTokApi import TikTokApi
import asyncio
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TikTokScraper:
    """Scraper pour récupérer les vidéos TikTok via l'API non-officielle"""
    
    def __init__(self, config):
        """
        Initialiser le scraper
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        self.api = None
        self._api_context = None
        logger.info("TikTokScraper initialisé")
    
    async def initialize(self):
        """Initialiser l'API TikTok avec Playwright"""
        try:
            # Utiliser async with pour une meilleure gestion
            self.api = TikTokApi()
            self._api_context = self.api
            await self.api.create_sessions(
                num_sessions=1,
                sleep_after=3,
                headless=self.config.HEADLESS_MODE,
                context_options={
                    "locale": "en-US",
                    "timezone_id": "America/New_York"
                }
            )
            logger.info("API TikTok initialisée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'API TikTok: {e}")
            raise
    
    async def get_trending_videos(self, count: int = 50) -> List[Dict]:
        """
        Récupérer les vidéos tendances
        
        Args:
            count: Nombre de vidéos à récupérer
            
        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        if not self.api:
            logger.error("API non initialisée. Appelez initialize() d'abord.")
            return []
        
        videos = []
        try:
            logger.info(f"Récupération de {count} vidéos tendances...")
            async for video in self.api.trending.videos(count=count):
                try:
                    video_data = self._extract_video_data(video)
                    videos.append(video_data)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction d'une vidéo: {e}")
                    continue
            
            logger.info(f"✓ {len(videos)} vidéos tendances récupérées")
            return videos
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos tendances: {e}")
            return videos
    
    async def search_by_hashtag(self, hashtag: str, count: int = 30) -> List[Dict]:
        """
        Rechercher des vidéos par hashtag
        
        Args:
            hashtag: Hashtag à rechercher (avec ou sans #)
            count: Nombre de vidéos à récupérer
            
        Returns:
            Liste de dictionnaires contenant les données des vidéos
        """
        if not self.api:
            logger.error("API non initialisée. Appelez initialize() d'abord.")
            return []
        
        # Nettoyer le hashtag
        hashtag = hashtag.lstrip('#')
        videos = []
        
        try:
            logger.info(f"Recherche de vidéos pour #{hashtag}...")
            tag = self.api.hashtag(name=hashtag)
            async for video in tag.videos(count=count):
                try:
                    video_data = self._extract_video_data(video)
                    video_data['hashtag'] = hashtag
                    videos.append(video_data)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction d'une vidéo: {e}")
                    continue
            
            logger.info(f"✓ {len(videos)} vidéos trouvées pour #{hashtag}")
            return videos
        except Exception as e:
            logger.error(f"Erreur lors de la recherche pour #{hashtag}: {e}")
            return videos
    
    def _extract_video_data(self, video) -> Dict:
        """
        Extraire les données pertinentes d'une vidéo
        
        Args:
            video: Objet vidéo de TikTokApi
            
        Returns:
            Dictionnaire avec les données de la vidéo
        """
        try:
            stats = video.stats if hasattr(video, 'stats') else {}
            
            # Convertir en int si nécessaire
            def to_int(value, default=0):
                if isinstance(value, (int, float)):
                    return int(value)
                if isinstance(value, str):
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return default
                return default
            
            # Récupérer l'URL de la vidéo
            video_url = None
            if hasattr(video, 'as_dict') and 'video' in video.as_dict:
                video_data_dict = video.as_dict['video']
                # Essayer différentes clés pour l'URL
                video_url = (
                    video_data_dict.get('downloadAddr') or
                    video_data_dict.get('playAddr') or
                    video_data_dict.get('download_addr') or
                    video_data_dict.get('play_addr')
                )
            
            # Fallback vers les attributs de l'objet
            if not video_url and hasattr(video, 'video') and video.video:
                if hasattr(video.video, 'download_addr'):
                    video_url = video.video.download_addr
                elif hasattr(video.video, 'downloadAddr'):
                    video_url = video.video.downloadAddr
                elif hasattr(video.video, 'playAddr'):
                    video_url = video.video.playAddr
            
            video_data = {
                'id': str(video.id),
                'author': video.author.username if hasattr(video.author, 'username') else 'unknown',
                'desc': video.desc if hasattr(video, 'desc') else '',
                'likes': to_int(stats.get('diggCount', 0)),
                'views': to_int(stats.get('playCount', 0)),
                'shares': to_int(stats.get('shareCount', 0)),
                'comments': to_int(stats.get('commentCount', 0)),
                'video_url': video_url,
                'music': video.music.title if hasattr(video, 'music') and video.music else None,
                'create_time': to_int(stats.get('createTime', 0))
            }
            
            return video_data
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des données: {e}")
            raise
    
    async def get_all_videos(self) -> List[Dict]:
        """
        Récupérer toutes les vidéos (trending + hashtags)
        
        Returns:
            Liste combinée de toutes les vidéos
        """
        all_videos = []
        
        # Récupérer les vidéos trending
        trending = await self.get_trending_videos(self.config.TRENDING_VIDEOS_COUNT)
        all_videos.extend(trending)
        
        # Récupérer les vidéos par hashtag
        for hashtag in self.config.TARGET_HASHTAGS:
            hashtag_videos = await self.search_by_hashtag(
                hashtag, 
                self.config.HASHTAG_VIDEOS_COUNT
            )
            all_videos.extend(hashtag_videos)
            
            # Petite pause entre les hashtags
            await asyncio.sleep(2)
        
        # Retirer les doublons basés sur l'ID
        unique_videos = {v['id']: v for v in all_videos}.values()
        logger.info(f"Total: {len(unique_videos)} vidéos uniques récupérées")
        
        return list(unique_videos)
    
    async def close(self):
        """Fermer les sessions de l'API"""
        if self.api:
            try:
                await self.api.close_sessions()
                logger.info("Sessions TikTok API fermées")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture des sessions: {e}")

