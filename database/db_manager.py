"""Gestionnaire de base de données pour tracker les vidéos"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, Optional, List
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
        Vérifier si une vidéo a déjà été traitée
        
        Args:
            video_id: ID de la vidéo TikTok
            
        Returns:
            True si la vidéo existe déjà en base
        """
        return self.session.query(ProcessedVideo).filter_by(id=video_id).first() is not None
    
    def add_video(self, video_data: Dict) -> bool:
        """
        Ajouter une vidéo à la base de données
        
        Args:
            video_data: Dictionnaire contenant les données de la vidéo
            
        Returns:
            True si l'ajout a réussi
        """
        try:
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
            logger.info(f"Vidéo {video_data['id']} ajoutée à la base de données")
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
    
    def close(self):
        """Fermer la session de base de données"""
        self.session.close()
        logger.info("Session de base de données fermée")

