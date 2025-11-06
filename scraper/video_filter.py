"""Filtre pour sélectionner les meilleures vidéos"""
from typing import List, Dict
import logging
import random

logger = logging.getLogger(__name__)


class VideoFilter:
    """Filtre les vidéos selon des critères d'engagement et de qualité"""
    
    def __init__(self, config):
        """
        Initialiser le filtre
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        logger.info("VideoFilter initialisé")
    
    def calculate_engagement_rate(self, video: Dict) -> float:
        """
        Calculer le taux d'engagement d'une vidéo
        
        Engagement = (likes + comments + shares) / views
        
        Args:
            video: Dictionnaire contenant les données de la vidéo
            
        Returns:
            Taux d'engagement (entre 0 et 1)
        """
        views = video.get('views', 0)
        if views == 0:
            return 0.0
        
        interactions = (
            video.get('likes', 0) + 
            video.get('comments', 0) + 
            video.get('shares', 0)
        )
        
        return interactions / views
    
    def calculate_virality_score(self, video: Dict) -> float:
        """
        Calculer un score de viralité pour prioriser les vidéos
        
        Score = (engagement_rate * 100) + (likes / 10000) + (shares / 1000)
        
        Args:
            video: Dictionnaire contenant les données de la vidéo
            
        Returns:
            Score de viralité
        """
        engagement = self.calculate_engagement_rate(video)
        likes = video.get('likes', 0)
        shares = video.get('shares', 0)
        
        score = (engagement * 100) + (likes / 10000) + (shares / 1000)
        return score
    
    def is_quality_video(self, video: Dict) -> bool:
        """
        Vérifier si la vidéo respecte les critères de qualité minimaux
        
        Args:
            video: Dictionnaire contenant les données de la vidéo
            
        Returns:
            True si la vidéo respecte tous les critères
        """
        likes = video.get('likes', 0)
        views = video.get('views', 0)
        video_url = video.get('video_url')
        engagement_rate = self.calculate_engagement_rate(video)
        
        # Vérifications
        has_min_likes = likes >= self.config.MIN_LIKES
        has_min_views = views >= self.config.MIN_VIEWS
        has_min_engagement = engagement_rate >= self.config.MIN_ENGAGEMENT_RATE
        has_video_url = video_url is not None and video_url != ''
        
        return has_min_likes and has_min_views and has_min_engagement and has_video_url
    
    def filter_videos(self, videos: List[Dict]) -> List[Dict]:
        """
        Filtrer et trier les vidéos selon les critères de qualité
        
        Args:
            videos: Liste de vidéos à filtrer
            
        Returns:
            Liste de vidéos filtrées et triées par score de viralité
        """
        logger.info(f"Filtrage de {len(videos)} vidéos...")
        
        # Filtrer les vidéos qui respectent les critères
        quality_videos = []
        for video in videos:
            if self.is_quality_video(video):
                # Ajouter le taux d'engagement et le score au dictionnaire
                video['engagement_rate'] = self.calculate_engagement_rate(video)
                video['virality_score'] = self.calculate_virality_score(video)
                quality_videos.append(video)
        
        logger.info(f"✓ {len(quality_videos)} vidéos de qualité trouvées")
        
        # Trier par score de viralité décroissant
        quality_videos.sort(key=lambda v: v['virality_score'], reverse=True)
        
        # Log des meilleures vidéos
        if quality_videos:
            top_video = quality_videos[0]
            logger.info(
                f"Meilleure vidéo: {top_video['id']} - "
                f"{top_video['views']} vues, {top_video['likes']} likes, "
                f"engagement: {top_video['engagement_rate']:.2%}"
            )
        
        return quality_videos
    
    def get_top_videos(self, videos: List[Dict], count: int = 10) -> List[Dict]:
        """
        Obtenir les N meilleures vidéos
        
        Args:
            videos: Liste de vidéos
            count: Nombre de vidéos à retourner
            
        Returns:
            Liste des meilleures vidéos
        """
        filtered = self.filter_videos(videos)
        return filtered[:count]
    
    def select_best_video_randomly(self, videos: List[Dict], top_n: int = 10) -> Dict:
        """
        Sélectionner aléatoirement une vidéo parmi les N meilleures
        
        Cette méthode:
        1. Filtre les vidéos selon les critères de qualité
        2. Trie par score d'engagement/viralité
        3. Sélectionne aléatoirement parmi les top_n meilleures
        
        Args:
            videos: Liste de toutes les vidéos récupérées
            top_n: Nombre de meilleures vidéos parmi lesquelles choisir aléatoirement
            
        Returns:
            Une vidéo sélectionnée aléatoirement parmi les meilleures
            
        Raises:
            ValueError: Si aucune vidéo de qualité n'est trouvée
        """
        # Filtrer et trier les vidéos
        quality_videos = self.filter_videos(videos)
        
        if not quality_videos:
            raise ValueError("Aucune vidéo de qualité trouvée")
        
        # Prendre les top_n meilleures
        top_videos = quality_videos[:min(top_n, len(quality_videos))]
        
        # Sélectionner aléatoirement parmi elles
        selected_video = random.choice(top_videos)
        
        logger.info(
            f"🎲 Vidéo sélectionnée aléatoirement parmi les {len(top_videos)} meilleures: "
            f"{selected_video['id']} - {selected_video['author']} - "
            f"{selected_video['views']:,} vues, {selected_video['likes']:,} likes, "
            f"engagement: {selected_video['engagement_rate']:.2%}, "
            f"score: {selected_video['virality_score']:.2f}"
        )
        
        return selected_video
    
    def get_top_videos_by_creator(self, videos: List[Dict], count_per_creator: int = 3) -> List[Dict]:
        """
        Obtenir les meilleures vidéos par créateur pour assurer la diversité
        
        Args:
            videos: Liste de vidéos
            count_per_creator: Nombre de vidéos max par créateur
            
        Returns:
            Liste des vidéos diversifiées par créateur
        """
        # Filtrer d'abord
        filtered = self.filter_videos(videos)
        
        # Grouper par créateur
        by_creator = {}
        for video in filtered:
            author = video.get('author', 'unknown')
            if author not in by_creator:
                by_creator[author] = []
            by_creator[author].append(video)
        
        # Prendre count_per_creator vidéos de chaque créateur
        result = []
        for author, author_videos in by_creator.items():
            # Trier par score pour ce créateur
            author_videos.sort(key=lambda v: v['virality_score'], reverse=True)
            result.extend(author_videos[:count_per_creator])
        
        # Re-trier globalement par score
        result.sort(key=lambda v: v['virality_score'], reverse=True)
        
        logger.info(
            f"✓ {len(result)} vidéos sélectionnées de {len(by_creator)} créateurs "
            f"(max {count_per_creator} par créateur)"
        )
        
        return result

