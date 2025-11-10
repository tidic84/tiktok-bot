"""Gestionnaire de base de données pour tracker les vidéos"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, Optional, List, Set
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)


class ProcessedVideo(Base):
    """Modèle de vidéo traitée"""
    __tablename__ = 'processed_videos'
    
    id = Column(String, primary_key=True)
    author = Column(String)
    description = Column(String)
    original_url = Column(String)
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime, nullable=True)
    is_uploaded = Column(Boolean, default=False)
    likes = Column(Integer)
    views = Column(Integer)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement_rate = Column(Float)
    local_path = Column(String, nullable=True)


class DatabaseManager:
    """Gestionnaire de la base de données SQLite"""
    
    def __init__(self, database_url: str):
        """
        Initialiser le gestionnaire de base de données
        
        Args:
            database_url: URL de connexion à la base de données
        """
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info("Base de données initialisée")
    
    def is_video_processed(self, video_id: str) -> bool:
        """
        Vérifier si une vidéo a déjà été traitée (uploadée)
        
        Une vidéo n'est considérée comme "traitée" que si elle a été UPLOADÉE.
        Les vidéos téléchargées mais non uploadées peuvent être retraitées.
        
        Args:
            video_id: ID de la vidéo TikTok
            
        Returns:
            True si la vidéo a déjà été uploadée
        """
        video = self.session.query(ProcessedVideo).filter_by(id=video_id).first()
        # Seules les vidéos UPLOADÉES sont considérées comme traitées
        return video is not None and video.is_uploaded
    
    def add_video(self, video_data: Dict) -> bool:
        """
        Ajouter une vidéo à la base de données
        
        Args:
            video_data: Dictionnaire contenant les données de la vidéo
            
        Returns:
            True si l'ajout a réussi
        """
        try:
            video = self.session.query(ProcessedVideo).filter_by(id=video_data['id']).first()
            is_new = video is None
            
            if video:
                # Mettre à jour les métadonnées existantes
                video.author = video_data.get('author', video.author)
                video.description = video_data.get('desc', video.description)
                video.original_url = video_data.get('video_url', video.original_url)
                video.likes = video_data.get('likes', video.likes)
                video.views = video_data.get('views', video.views)
                video.shares = video_data.get('shares', video.shares)
                video.comments = video_data.get('comments', video.comments)
                video.engagement_rate = video_data.get('engagement_rate', video.engagement_rate)
                if video_data.get('local_path'):
                    video.local_path = video_data.get('local_path')
                # Rafraîchir la date de téléchargement
                video.downloaded_at = datetime.utcnow()
            else:
                video = ProcessedVideo(
                    id=video_data['id'],
                    author=video_data.get('author', ''),
                    description=video_data.get('desc', ''),
                    original_url=video_data.get('video_url', ''),
                    likes=video_data.get('likes', 0),
                    views=video_data.get('views', 0),
                    shares=video_data.get('shares', 0),
                    comments=video_data.get('comments', 0),
                    engagement_rate=video_data.get('engagement_rate', 0.0),
                    local_path=video_data.get('local_path', None)
                )
                self.session.add(video)
            
            self.session.commit()
            if is_new:
                logger.info(f"Vidéo {video_data['id']} ajoutée à la base de données")
            else:
                logger.info(f"Vidéo {video_data['id']} mise à jour dans la base de données")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors de l'ajout de la vidéo {video_data.get('id')}: {e}")
            return False
    
    def mark_as_uploaded(self, video_id: str) -> bool:
        """
        Marquer une vidéo comme uploadée
        
        Args:
            video_id: ID de la vidéo
            
        Returns:
            True si la mise à jour a réussi
        """
        try:
            video = self.session.query(ProcessedVideo).filter_by(id=video_id).first()
            if video:
                video.is_uploaded = True
                video.uploaded_at = datetime.utcnow()
                self.session.commit()
                logger.info(f"Vidéo {video_id} marquée comme uploadée")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors de la mise à jour de {video_id}: {e}")
            return False
    
    def get_uploaded_count_today(self) -> int:
        """
        Obtenir le nombre de vidéos uploadées aujourd'hui
        
        Returns:
            Nombre de vidéos uploadées aujourd'hui
        """
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            count = self.session.query(ProcessedVideo).filter(
                ProcessedVideo.is_uploaded == True,
                ProcessedVideo.uploaded_at >= today_start
            ).count()
            return count
        except Exception as e:
            logger.error(f"Erreur lors du comptage des uploads: {e}")
            return 0
    
    def get_recent_uploaded_ids(self, limit: Optional[int] = None) -> Set[str]:
        """
        Récupérer les identifiants des vidéos déjà uploadées récemment.
        
        Args:
            limit: Nombre maximum d'identifiants à retourner (None pour tout récupérer)
            
        Returns:
            Ensemble des identifiants de vidéos marquées comme uploadées
        """
        try:
            query = self.session.query(ProcessedVideo.id).filter(
                ProcessedVideo.is_uploaded == True
            )
            if limit is not None:
                query = query.order_by(ProcessedVideo.uploaded_at.desc()).limit(limit)
            return {row[0] for row in query.all()}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos uploadées: {e}")
            return set()
    
    def get_all_processed_videos(self, limit: int = 100) -> List[ProcessedVideo]:
        """
        Obtenir toutes les vidéos traitées
        
        Args:
            limit: Nombre maximum de vidéos à retourner
            
        Returns:
            Liste des vidéos traitées
        """
        return self.session.query(ProcessedVideo).order_by(
            ProcessedVideo.downloaded_at.desc()
        ).limit(limit).all()
    
    def is_video_uploaded(self, video_id: str) -> bool:
        """
        Vérifier si une vidéo a déjà été uploadée
        
        Args:
            video_id: ID de la vidéo TikTok
            
        Returns:
            True si la vidéo a déjà été uploadée
        """
        video = self.session.query(ProcessedVideo).filter_by(id=video_id).first()
        return video is not None and video.is_uploaded
    
    def get_video(self, video_id: str) -> Optional[ProcessedVideo]:
        """
        Récupérer une vidéo par son identifiant.
        
        Args:
            video_id: ID de la vidéo TikTok
            
        Returns:
            L'objet ProcessedVideo ou None s'il n'est pas trouvé
        """
        try:
            return self.session.query(ProcessedVideo).filter_by(id=video_id).first()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de {video_id}: {e}")
            return None
    
    def get_known_video_ids(self) -> Set[str]:
        """
        Obtenir l'ensemble des identifiants de vidéos déjà connues (uploadées ou en attente).
        
        Returns:
            Ensemble des identifiants présents dans la base
        """
        try:
            rows = self.session.query(ProcessedVideo.id).all()
            return {row[0] for row in rows}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des identifiants connus: {e}")
            return set()
    
    def get_pending_videos(self, limit: int = 100) -> List[ProcessedVideo]:
        """
        Obtenir les vidéos téléchargées mais non uploadées
        
        Ces vidéos peuvent être retraitées au prochain cycle.
        
        Args:
            limit: Nombre maximum de vidéos à retourner
            
        Returns:
            Liste des vidéos en attente
        """
        return self.session.query(ProcessedVideo).filter(
            ProcessedVideo.is_uploaded == False
        ).order_by(
            ProcessedVideo.downloaded_at.desc()
        ).limit(limit).all()
    
    def cleanup_old_pending_videos(self, days: int = 7) -> int:
        """
        Supprimer les vidéos en attente trop anciennes
        
        Args:
            days: Âge en jours au-delà duquel supprimer
            
        Returns:
            Nombre de vidéos supprimées
        """
        from datetime import timedelta
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            count = self.session.query(ProcessedVideo).filter(
                ProcessedVideo.is_uploaded == False,
                ProcessedVideo.downloaded_at < cutoff_date
            ).delete()
            self.session.commit()
            if count > 0:
                logger.info(f"✓ {count} vidéo(s) en attente supprimée(s) (>{days} jours)")
            return count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors du nettoyage des vidéos en attente: {e}")
            return 0
    
    def close(self):
        """Fermer la session de base de données"""
        self.session.close()
        logger.info("Session de base de données fermée")

