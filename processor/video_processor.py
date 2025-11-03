"""Processeur vidéo pour modifier les vidéos et éviter la détection de contenu dupliqué"""
import subprocess
import random
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Modifie les vidéos pour les rendre "uniques" et éviter la détection TikTok"""
    
    def __init__(self, config):
        """
        Initialiser le processeur
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        self.ffmpeg_path = '/usr/bin/ffmpeg'
        logger.info("VideoProcessor initialisé")
    
    def process_video(self, input_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Traiter une vidéo pour la rendre unique
        
        Applique plusieurs modifications subtiles :
        - Légère modification de la vitesse (0.98x - 1.02x)
        - Rotation minime (0.5-1°)
        - Ajustement luminosité/contraste
        - Crop/zoom très léger (1-3%)
        - Miroir horizontal aléatoire
        
        Args:
            input_path: Chemin de la vidéo d'entrée
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Chemin de la vidéo modifiée ou None si échec
        """
        try:
            input_file = Path(input_path)
            
            if not output_path:
                # Créer un nom de fichier modifié
                output_path = str(input_file.parent / f"{input_file.stem}_processed{input_file.suffix}")
            
            output_file = Path(output_path)
            
            logger.info(f"Traitement vidéo: {input_file.name}")
            
            # Générer des paramètres aléatoires subtils
            filters = self._generate_filters()
            
            # Construire la commande ffmpeg
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_file),
                '-vf', filters,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',  # Copier l'audio sans modification
                '-y',  # Écraser si existe
                str(output_file)
            ]
            
            # Exécuter la commande
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=180  # 3 minutes max
            )
            
            if result.returncode == 0 and output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)
                logger.info(f"✓ Vidéo traitée: {output_file.name} ({file_size:.2f} MB)")
                return str(output_file)
            else:
                logger.error(f"Échec traitement: {result.stderr.decode()}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors du traitement de {input_path}")
            return None
        except Exception as e:
            logger.error(f"Erreur traitement vidéo: {e}")
            return None
    
    def _generate_filters(self) -> str:
        """
        Générer une chaîne de filtres FFmpeg aléatoires mais subtils
        
        Returns:
            Chaîne de filtres FFmpeg
        """
        filters = []
        
        # 1. Modification de vitesse (très subtile: 98-102%)
        speed = random.uniform(0.98, 1.02)
        filters.append(f"setpts={1/speed:.4f}*PTS")
        
        # 2. Ajustement luminosité/contraste (subtil)
        brightness = random.uniform(-0.05, 0.05)  # -5% à +5%
        contrast = random.uniform(0.98, 1.02)      # 98% à 102%
        filters.append(f"eq=brightness={brightness:.3f}:contrast={contrast:.3f}")
        
        # 3. Crop/zoom très léger (1-3%)
        crop_percent = random.uniform(1, 3)
        filters.append(f"crop=iw*{(100-crop_percent)/100:.4f}:ih*{(100-crop_percent)/100:.4f}")
        filters.append("scale=720:1280")  # Rescale à la taille TikTok
        
        # 4. Rotation minime (0.5-1.5°) - optionnel
        if random.random() > 0.5:  # 50% de chance
            angle = random.uniform(0.5, 1.5) * random.choice([-1, 1])
            filters.append(f"rotate={angle}*PI/180:fillcolor=black")
        
        # 5. Miroir horizontal (20% de chance)
        if random.random() > 0.8:
            filters.append("hflip")
        
        # 6. Saturation (subtile: 95-105%)
        saturation = random.uniform(0.95, 1.05)
        filters.append(f"eq=saturation={saturation:.3f}")
        
        # Combiner tous les filtres
        return ",".join(filters)
    
    def add_watermark(self, input_path: str, text: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Ajouter un watermark texte discret
        
        Args:
            input_path: Chemin de la vidéo
            text: Texte du watermark
            output_path: Chemin de sortie
            
        Returns:
            Chemin de la vidéo avec watermark
        """
        try:
            input_file = Path(input_path)
            
            if not output_path:
                output_path = str(input_file.parent / f"{input_file.stem}_wm{input_file.suffix}")
            
            output_file = Path(output_path)
            
            # Position aléatoire du watermark
            positions = [
                "x=10:y=10",              # Haut gauche
                "x=w-tw-10:y=10",         # Haut droite
                "x=10:y=h-th-10",         # Bas gauche
                "x=w-tw-10:y=h-th-10",    # Bas droite
            ]
            position = random.choice(positions)
            
            # Opacité aléatoire (très discrète: 20-40%)
            opacity = random.uniform(0.2, 0.4)
            
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_file),
                '-vf', f"drawtext=text='{text}':fontsize=20:fontcolor=white@{opacity}:{position}",
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',
                '-y',
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=180)
            
            if result.returncode == 0 and output_file.exists():
                logger.info(f"✓ Watermark ajouté: {output_file.name}")
                return str(output_file)
            else:
                logger.error(f"Échec watermark: {result.stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur watermark: {e}")
            return None
    
    def add_border(self, input_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Ajouter une bordure colorée subtile
        
        Args:
            input_path: Chemin de la vidéo
            output_path: Chemin de sortie
            
        Returns:
            Chemin de la vidéo avec bordure
        """
        try:
            input_file = Path(input_path)
            
            if not output_path:
                output_path = str(input_file.parent / f"{input_file.stem}_border{input_file.suffix}")
            
            output_file = Path(output_path)
            
            # Bordure très fine (2-5 pixels)
            border_size = random.randint(2, 5)
            
            # Couleur aléatoire subtile
            colors = ['black', 'white', '0x1a1a1a', '0xf0f0f0']
            color = random.choice(colors)
            
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_file),
                '-vf', f"pad=width=iw+{border_size*2}:height=ih+{border_size*2}:x={border_size}:y={border_size}:color={color}",
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',
                '-y',
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=180)
            
            if result.returncode == 0 and output_file.exists():
                logger.info(f"✓ Bordure ajoutée: {output_file.name}")
                return str(output_file)
            else:
                logger.error(f"Échec bordure: {result.stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur bordure: {e}")
            return None
    
    def cleanup_processed_video(self, filepath: str):
        """
        Supprimer un fichier traité
        
        Args:
            filepath: Chemin du fichier à supprimer
        """
        try:
            file = Path(filepath)
            if file.exists() and '_processed' in file.name:
                file.unlink()
                logger.info(f"Fichier traité supprimé: {file.name}")
        except Exception as e:
            logger.error(f"Erreur suppression: {e}")

