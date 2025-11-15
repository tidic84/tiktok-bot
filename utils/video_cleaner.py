"""Nettoyeur automatique de vidéos"""
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class VideoCleaner:
    """Gestionnaire de nettoyage des vieilles vidéos"""
    
    def __init__(self, config):
        """
        Initialiser le nettoyeur
        
        Args:
            config: Configuration du bot
        """
        self.config = config
        self.download_folder = Path(config.DOWNLOAD_FOLDER)
        self.keep_days = config.KEEP_VIDEOS_DAYS
        logger.info(f"VideoCleaner initialisé (conservation: {self.keep_days} jours)")
    
    def cleanup_old_videos(self) -> Tuple[int, float]:
        """
        Supprimer les vidéos plus vieilles que KEEP_VIDEOS_DAYS
        
        Returns:
            Tuple (nombre de fichiers supprimés, espace libéré en MB)
        """
        if not self.config.AUTO_CLEANUP_VIDEOS:
            logger.info("Nettoyage automatique désactivé")
            return 0, 0.0
        
        logger.info(f"🧹 Nettoyage des vidéos > {self.keep_days} jours...")
        
        try:
            cutoff_time = time.time() - (self.keep_days * 24 * 60 * 60)
            files_deleted = 0
            space_freed = 0.0
            
            # Parcourir tous les fichiers du dossier
            for file_path in self.download_folder.glob("*.mp4"):
                try:
                    # Vérifier l'âge du fichier
                    file_mtime = file_path.stat().st_mtime
                    
                    if file_mtime < cutoff_time:
                        # Fichier trop vieux, le supprimer
                        file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                        file_age_days = (time.time() - file_mtime) / (24 * 60 * 60)
                        
                        logger.info(
                            f"🗑️  Suppression: {file_path.name} "
                            f"(âge: {file_age_days:.1f} jours, taille: {file_size:.2f} MB)"
                        )
                        
                        file_path.unlink()
                        files_deleted += 1
                        space_freed += file_size
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression de {file_path.name}: {e}")
                    continue
            
            if files_deleted > 0:
                logger.info(
                    f"✓ Nettoyage terminé: {files_deleted} fichier(s) supprimé(s), "
                    f"{space_freed:.2f} MB libérés"
                )
            else:
                logger.info("✓ Aucune vidéo à supprimer")
            
            return files_deleted, space_freed
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            return 0, 0.0
    
    def get_folder_stats(self) -> dict:
        """
        Obtenir des statistiques sur le dossier de vidéos
        
        Returns:
            Dictionnaire avec les stats
        """
        try:
            files = list(self.download_folder.glob("*.mp4"))
            total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)  # MB
            
            if not files:
                return {
                    'count': 0,
                    'total_size_mb': 0.0,
                    'oldest_days': 0,
                    'newest_days': 0
                }
            
            now = time.time()
            mtimes = [f.stat().st_mtime for f in files]
            oldest = (now - min(mtimes)) / (24 * 60 * 60) if mtimes else 0
            newest = (now - max(mtimes)) / (24 * 60 * 60) if mtimes else 0
            
            return {
                'count': len(files),
                'total_size_mb': total_size,
                'oldest_days': oldest,
                'newest_days': newest
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats: {e}")
            return {
                'count': 0,
                'total_size_mb': 0.0,
                'oldest_days': 0,
                'newest_days': 0
            }
    
    def cleanup_temp_files(self) -> int:
        """
        Supprimer les fichiers temporaires (_temp, _temp_wm)
        
        Returns:
            Nombre de fichiers supprimés
        """
        logger.info("🧹 Nettoyage des fichiers temporaires...")
        
        try:
            files_deleted = 0
            temp_patterns = ["*_temp.mp4", "*_temp_wm.mp4"]
            
            for pattern in temp_patterns:
                for file_path in self.download_folder.glob(pattern):
                    try:
                        logger.info(f"🗑️  Suppression fichier temp: {file_path.name}")
                        file_path.unlink()
                        files_deleted += 1
                    except Exception as e:
                        logger.error(f"Erreur suppression temp {file_path.name}: {e}")
            
            if files_deleted > 0:
                logger.info(f"✓ {files_deleted} fichier(s) temporaire(s) supprimé(s)")
            else:
                logger.info("✓ Aucun fichier temporaire à supprimer")
            
            return files_deleted
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des fichiers temp: {e}")
            return 0

