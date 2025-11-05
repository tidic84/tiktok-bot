"""Téléchargeur de vidéos TikTok"""
import requests
import os
import subprocess
import re
import random
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Télécharge les vidéos TikTok en MP4"""
    
    def __init__(self, config):
        """
        Initialiser le téléchargeur
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        self.download_folder = Path(config.DOWNLOAD_FOLDER)
        self.download_folder.mkdir(exist_ok=True)
        logger.info(f"VideoDownloader initialisé - Dossier: {self.download_folder}")
    
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """
        Nettoyer un texte pour en faire un nom de fichier valide
        
        Args:
            text: Texte à nettoyer
            max_length: Longueur max du nom
            
        Returns:
            Nom de fichier nettoyé
        """
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
        # Liste d'emojis populaires sur TikTok
        emojis = [
            '🔥', '⭐', '❤️', '✨', '🚀', 
            '💃', '🎵', '📹', '🔝', '💯',
            '😎', '🤩', '👏', '💪', '🎉'
        ]
        
        # Choisir 3-5 emojis au hasard
        num_emojis = random.randint(3, 5)
        selected = random.sample(emojis, num_emojis)
        
        return ''.join(selected)
    
    def download_video(self, video_data: Dict) -> Optional[str]:
        """
        Télécharger une vidéo TikTok
        
        Args:
            video_data: Dictionnaire contenant les données de la vidéo
            
        Returns:
            Chemin local du fichier téléchargé ou None si échec
        """
        video_id = video_data.get('id')
        author = video_data.get('author', 'unknown')
        desc = video_data.get('desc', '')
        
        # Créer un nom de fichier basé sur la description
        clean_desc = self._sanitize_filename(desc, max_length=50)
        
        # Si la description est vide après nettoyage, utiliser des emojis
        if clean_desc == "video" or not clean_desc or len(clean_desc) < 3:
            clean_desc = self._generate_emoji_name()
            logger.debug(f"Description vide, génération nom emojis: {clean_desc}")
        
        # Nom de fichier : description SEULEMENT (sans ID, sans underscore)
        filename = f"{clean_desc}.mp4"
        filepath = self.download_folder / filename
        
        # Si le fichier existe déjà (collision), ajouter un suffixe
        if filepath.exists():
            counter = 1
            while filepath.exists():
                filename = f"{clean_desc}{counter}.mp4"
                filepath = self.download_folder / filename
                counter += 1
            logger.debug(f"Nom existant, suffixe ajouté: {filename}")
        
        # Vérifier si le fichier existe déjà
        if filepath.exists():
            logger.info(f"Vidéo {video_id} déjà téléchargée")
            return str(filepath.absolute())
        
        # Méthode 1 : Essayer avec yt-dlp (le meilleur pour TikTok)
        if self._download_with_ytdlp(video_id, author, filepath):
            return str(filepath.absolute())
        
        # Méthode 2 : Fallback avec requests si URL disponible
        video_url = video_data.get('video_url')
        if video_url and self._download_with_requests(video_id, video_url, filepath):
            return str(filepath.absolute())
        
        logger.error(f"Échec du téléchargement de {video_id} avec toutes les méthodes")
        return None
    
    def _download_with_ytdlp(self, video_id: str, author: str, filepath: Path) -> bool:
        """
        Télécharger avec yt-dlp (RECOMMANDÉ pour TikTok)
        
        Args:
            video_id: ID de la vidéo
            author: Auteur de la vidéo
            filepath: Chemin de destination
            
        Returns:
            True si succès
        """
        try:
            # Construire l'URL TikTok
            tiktok_url = f"https://www.tiktok.com/@{author}/video/{video_id}"
            
            logger.info(f"Téléchargement avec yt-dlp: {video_id}...")
            
            # Commande yt-dlp simple (téléchargement)
            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '--ffmpeg-location', '/usr/bin/ffmpeg',
                '-o', str(filepath),
                '--no-playlist',
                '--no-check-certificate',
                tiktok_url
            ]
            
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 and filepath.exists():
                file_size = filepath.stat().st_size / (1024 * 1024)
                logger.info(f"✓ Vidéo {video_id} téléchargée ({file_size:.2f} MB)")
                
                # Vérifier le codec et convertir si nécessaire (HEVC -> H.264)
                if self._convert_to_h264_if_needed(filepath):
                    logger.info(f"✓ Vidéo {video_id} convertie en H.264 (compatible)")
                
                return True
            else:
                logger.warning(f"yt-dlp a échoué pour {video_id}: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.warning("yt-dlp non installé, utilisez: pip install yt-dlp")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors du téléchargement de {video_id}")
            return False
        except Exception as e:
            logger.error(f"Erreur yt-dlp pour {video_id}: {e}")
            return False
    
    def _convert_to_h264_if_needed(self, filepath: Path) -> bool:
        """
        Convertir la vidéo en H.264 si elle est en HEVC (pour compatibilité)
        
        Args:
            filepath: Chemin du fichier vidéo
            
        Returns:
            True si conversion effectuée
        """
        try:
            # Vérifier le codec actuel
            cmd_check = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(filepath)
            ]
            
            result = subprocess.run(cmd_check, capture_output=True, text=True, timeout=10)
            codec = result.stdout.strip()
            
            # Si c'est déjà H.264, rien à faire
            if codec in ['h264', 'avc', 'avc1']:
                logger.info(f"Codec H.264 détecté - pas de conversion nécessaire")
                return False
            
            # Si c'est HEVC ou autre, convertir
            if codec in ['hevc', 'h265', 'hvc1']:
                logger.info(f"Codec {codec} détecté - conversion en H.264...")
                
                # Fichier temporaire
                temp_filepath = filepath.with_suffix('.tmp.mp4')
                
                # Conversion avec ffmpeg (rapide avec preset ultrafast)
                cmd_convert = [
                    'ffmpeg',
                    '-i', str(filepath),
                    '-c:v', 'libx264',      # Codec H.264
                    '-preset', 'ultrafast', # Très rapide
                    '-crf', '23',           # Qualité (18-28, 23=bon équilibre)
                    '-c:a', 'copy',         # Copier audio sans ré-encoder
                    '-y',                   # Écraser si existe
                    str(temp_filepath)
                ]
                
                result = subprocess.run(cmd_convert, capture_output=True, timeout=60)
                
                if result.returncode == 0 and temp_filepath.exists():
                    # Remplacer l'original par la version convertie
                    filepath.unlink()
                    temp_filepath.rename(filepath)
                    logger.info(f"✓ Conversion H.264 réussie")
                    return True
                else:
                    logger.warning(f"Échec conversion: {result.stderr}")
                    if temp_filepath.exists():
                        temp_filepath.unlink()
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification/conversion: {e}")
            return False
    
    def _download_with_requests(self, video_id: str, video_url: str, filepath: Path) -> bool:
        """
        Télécharger avec requests (Fallback)
        
        Args:
            video_id: ID de la vidéo
            video_url: URL de téléchargement
            filepath: Chemin de destination
            
        Returns:
            True si succès
        """
        try:
            logger.info(f"Téléchargement avec requests: {video_id}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/',
            }
            
            response = requests.get(
                video_url, 
                headers=headers,
                stream=True, 
                timeout=60
            )
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Vidéo {video_id} téléchargée avec requests ({file_size:.2f} MB)")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur HTTP pour {video_id}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
        
        except Exception as e:
            logger.error(f"Erreur requests pour {video_id}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
    
    def delete_video(self, video_path: str) -> bool:
        """
        Supprimer un fichier vidéo
        
        Args:
            video_path: Chemin du fichier à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        try:
            path = Path(video_path)
            if path.exists():
                path.unlink()
                logger.info(f"Vidéo {path.name} supprimée")
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de {video_path}: {e}")
            return False
    
    def get_video_size(self, video_path: str) -> float:
        """
        Obtenir la taille d'une vidéo en MB
        
        Args:
            video_path: Chemin du fichier vidéo
            
        Returns:
            Taille en MB
        """
        try:
            path = Path(video_path)
            if path.exists():
                return path.stat().st_size / (1024 * 1024)
            return 0.0
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la taille: {e}")
            return 0.0
    
    def cleanup_old_videos(self, keep_count: int = 50):
        """
        Nettoyer les anciennes vidéos pour libérer de l'espace
        
        Args:
            keep_count: Nombre de vidéos récentes à conserver
        """
        try:
            videos = sorted(
                self.download_folder.glob("*.mp4"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if len(videos) > keep_count:
                for video in videos[keep_count:]:
                    video.unlink()
                    logger.info(f"Ancienne vidéo supprimée: {video.name}")
                
                logger.info(f"Nettoyage effectué: {len(videos) - keep_count} vidéos supprimées")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")

