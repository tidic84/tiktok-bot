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
                # Créer un fichier temporaire
                output_path = str(input_file.parent / f"{input_file.stem}_temp.mp4")
            
            output_file = Path(output_path)
            
            logger.info(f"Traitement vidéo: {input_file.name}")
            
            # Générer des paramètres aléatoires subtils
            filters = self._generate_filters()
            
            # Générer des filtres audio pour changer l'empreinte sonore
            audio_filters = self._generate_audio_filters()
            
            # Construire la commande ffmpeg avec modification AUDIO+VIDÉO
            cmd = [
                self.ffmpeg_path,
                '-i', str(input_file),
                '-vf', filters,  # Filtres vidéo
                '-af', audio_filters,  # Filtres audio (NOUVEAU)
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',  # Re-encoder l'audio (pas de copie)
                '-b:a', '128k',  # Bitrate audio
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
                
                # Remplacer le fichier original par le fichier traité
                if "_temp" in output_file.name:
                    final_path = input_file.parent / f"{input_file.stem}.mp4"
                    if input_file.exists():
                        input_file.unlink()  # Supprimer l'original
                    output_file.rename(final_path)  # Renommer temp -> nom original
                    logger.info(f"✓ Fichier remplacé: {final_path.name}")
                    return str(final_path)
                
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
        Générer une chaîne de filtres FFmpeg - VERSION ULTRA AGRESSIVE
        Basé sur les techniques de bypass de détection perceptuelle
        
        Returns:
            Chaîne de filtres FFmpeg
        """
        filters = []
        
        # 1. Modification de vitesse FORTE (92-108%)
        speed = random.uniform(0.92, 1.08)
        filters.append(f"setpts={1/speed:.4f}*PTS")
        
        # 2. Ajustement luminosité/contraste TRÈS MARQUÉ
        brightness = random.uniform(-0.15, 0.15)  # -15% à +15%
        contrast = random.uniform(0.90, 1.15)     # 90% à 115%
        filters.append(f"eq=brightness={brightness:.3f}:contrast={contrast:.3f}")
        
        # 3. Crop/zoom AGRESSIF (5-12%) + décalage aléatoire
        crop_percent = random.uniform(5, 12)
        # Décalage X et Y aléatoire pour changer la composition
        x_offset = random.randint(-20, 20)
        y_offset = random.randint(-30, 30)
        filters.append(
            f"crop=iw*{(100-crop_percent)/100:.4f}:ih*{(100-crop_percent)/100:.4f}:"
            f"(iw-iw*{(100-crop_percent)/100:.4f})/2+{x_offset}:"
            f"(ih-ih*{(100-crop_percent)/100:.4f})/2+{y_offset}"
        )
        filters.append("scale=720:1280")  # Rescale à la taille TikTok
        
        # 4. Rotation FORTE (0.5-4°) + bordure noire variable
        angle = random.uniform(0.5, 4.0) * random.choice([-1, 1])
        filters.append(f"rotate={angle}*PI/180:fillcolor=black")
        
        # 5. Miroir horizontal (50% de chance)
        if random.random() > 0.5:
            filters.append("hflip")
        
        # 6. Miroir vertical occasionnel (15% de chance - NOUVEAU)
        if random.random() > 0.85:
            filters.append("vflip")
        
        # 7. Saturation TRÈS VARIABLE (85-115%)
        saturation = random.uniform(0.85, 1.15)
        filters.append(f"eq=saturation={saturation:.3f}")
        
        # 8. Ajout de bruit PLUS FORT
        noise_level = random.randint(3, 8)
        filters.append(f"noise=alls={noise_level}:allf=t")
        
        # 9. Gamma correction MARQUÉE
        gamma = random.uniform(0.90, 1.10)
        filters.append(f"eq=gamma={gamma:.3f}")
        
        # 10. Modification de teinte PLUS FORTE
        hue = random.uniform(-0.10, 0.10)
        filters.append(f"hue=h={hue:.3f}")
        
        # 11. NOUVEAU: Changement de température de couleur
        temperature = random.uniform(4500, 7500)
        filters.append(f"colortemperature={temperature:.0f}")
        
        # 12. NOUVEAU: Vibrance (renforce les couleurs désaturées)
        vibrance = random.uniform(-0.1, 0.1)
        filters.append(f"vibrance=intensity={vibrance:.3f}")
        
        # 13. NOUVEAU: Flou subtil puis sharpen (change le perceptual hash)
        if random.random() > 0.5:
            blur = random.uniform(0.3, 0.8)
            filters.append(f"unsharp=5:5:{blur}:5:5:0.0")
        
        # 14. NOUVEAU: Ajout de grain vidéo (change l'empreinte)
        grain = random.randint(15, 35)
        filters.append(f"noise=alls={grain}:allf=t+u")
        
        # Combiner tous les filtres
        return ",".join(filters)
    
    def _generate_audio_filters(self) -> str:
        """
        Générer des filtres audio pour modifier l'empreinte sonore
        (CRITIQUE pour éviter la détection)
        
        Returns:
            Chaîne de filtres audio FFmpeg
        """
        audio_filters = []
        
        # 1. Changement de vitesse audio (doit correspondre à la vidéo, environ)
        speed = random.uniform(0.98, 1.02)
        audio_filters.append(f"atempo={speed:.4f}")
        
        # 2. Légère modification du pitch (quasi imperceptible)
        pitch_shift = random.uniform(-50, 50)  # centièmes
        audio_filters.append(f"asetrate=44100*{1+pitch_shift/10000:.6f},aresample=44100")
        
        # 3. Égalisation subtile (change le spectre audio)
        bass = random.uniform(-2, 2)
        treble = random.uniform(-2, 2)
        audio_filters.append(f"bass=g={bass:.1f},treble=g={treble:.1f}")
        
        # 4. Ajout de bruit audio TRÈS LÉGER
        noise_amount = random.uniform(0.001, 0.003)
        audio_filters.append(f"anoisesrc=a={noise_amount}:c=white:d=1[noise];[0:a][noise]amix=inputs=2:duration=shortest")
        
        # 5. Compression dynamique (change l'enveloppe sonore)
        audio_filters.append("acompressor=threshold=-20dB:ratio=3:attack=5:release=50")
        
        # 6. Normalisation du volume
        audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        
        return ",".join(audio_filters)
    
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
                # Créer un fichier temporaire
                output_path = str(input_file.parent / f"{input_file.stem}_temp_wm.mp4")
            
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
                
                # Remplacer le fichier original par le fichier avec watermark
                if "_temp_wm" in output_file.name:
                    final_path = input_file.parent / f"{input_file.stem.replace('_temp', '')}.mp4"
                    if input_file.exists():
                        input_file.unlink()  # Supprimer l'original
                    output_file.rename(final_path)  # Renommer temp_wm -> nom final
                    logger.info(f"✓ Fichier remplacé: {final_path.name}")
                    return str(final_path)
                
                return str(output_file)
            else:
                logger.error(f"Échec watermark: {result.stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur watermark: {e}")
            return None

