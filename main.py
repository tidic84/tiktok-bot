"""
Bot TikTok - Récupération et republication automatique de vidéos virales
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

from config import Config
from scraper.tiktok_scraper import TikTokScraper
from scraper.video_filter import VideoFilter
from downloader.video_downloader import VideoDownloader
from processor.video_processor import VideoProcessor  # Traitement vidéo
# NOTE: SeleniumUploader sera importé SEULEMENT quand nécessaire pour éviter les conflits avec Playwright
from database.db_manager import DatabaseManager
from utils.rate_limiter import RateLimiter


# Configuration du logging
def setup_logging(config):
    """Configurer le système de logging"""
    log_folder = Path(config.LOGS_FOLDER)
    log_folder.mkdir(exist_ok=True)
    
    log_file = log_folder / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


logger = logging.getLogger(__name__)


class TikTokBot:
    """Bot principal pour récupérer et republier des vidéos TikTok"""
    
    def __init__(self):
        """Initialiser le bot"""
        self.config = Config()
        self.config.create_folders()
        
        # Initialiser les composants
        self.scraper = TikTokScraper(self.config)
        self.filter = VideoFilter(self.config)
        self.downloader = VideoDownloader(self.config)
        self.processor = VideoProcessor(self.config)  # Traitement vidéo
        # NOTE: uploader sera initialisé seulement quand nécessaire (lazy loading complet)
        self.uploader = None
        self.db = DatabaseManager(self.config.DATABASE_URL)
        self.rate_limiter = RateLimiter(self.config)
        
        logger.info("=" * 60)
        logger.info("TikTok Bot initialisé")
        logger.info("=" * 60)
    
    async def process_videos(self):
        """Processus principal de récupération et republication"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("DÉBUT DU CYCLE DE TRAITEMENT")
            logger.info("=" * 60)
            
            # Vérifier si on est dans les heures actives
            if not self.rate_limiter.is_active_hours():
                self.rate_limiter.wait_until_active_hours()
            
            # Vérifier la limite quotidienne
            uploaded_today = self.db.get_uploaded_count_today()
            logger.info(f"Vidéos uploadées aujourd'hui: {uploaded_today}/{self.config.MAX_VIDEOS_PER_DAY}")
            
            if uploaded_today >= self.config.MAX_VIDEOS_PER_DAY:
                logger.info("✓ Limite quotidienne atteinte")
                return
            
            remaining_slots = self.config.MAX_VIDEOS_PER_DAY - uploaded_today
            
            # 1. Récupérer les vidéos (SEULEMENT trending, quantité réduite)
            logger.info("\n--- Phase 1: Récupération des vidéos ---")
            
            # Utiliser immédiatement la session (pas de délai)
            # TikTok bloque si on attend trop entre init() et utilisation
            all_videos = await self.scraper.get_trending_videos(self.config.TRENDING_VIDEOS_COUNT)
            
            if not all_videos:
                logger.warning("Aucune vidéo récupérée")
                return
            
            # 2. Filtrer les meilleures vidéos
            logger.info("\n--- Phase 2: Filtrage des vidéos ---")
            quality_videos = self.filter.filter_videos(all_videos)
            
            if not quality_videos:
                logger.warning("Aucune vidéo ne correspond aux critères")
                return
            
            # 3. Traiter chaque vidéo
            logger.info(f"\n--- Phase 3: Traitement de {min(len(quality_videos), remaining_slots)} vidéos ---")
            
            uploaded_count = 0
            
            for i, video in enumerate(quality_videos):
                if uploaded_count >= remaining_slots:
                    logger.info(f"✓ Limite de {remaining_slots} vidéos atteinte pour ce cycle")
                    break
                
                logger.info(f"\n[{i+1}/{len(quality_videos)}] Traitement de la vidéo {video['id']}")
                
                # Vérifier si déjà traitée
                if self.db.is_video_processed(video['id']):
                    logger.info(f"⊗ Vidéo {video['id']} déjà traitée, passage à la suivante")
                    continue
                
                # Télécharger la vidéo
                logger.info(f"Téléchargement de la vidéo {video['id']}...")
                video_path = self.downloader.download_video(video)
                
                if not video_path:
                    logger.warning(f"⊗ Échec du téléchargement de {video['id']}")
                    continue
                
                # Traiter la vidéo pour éviter détection de contenu dupliqué
                if self.config.PROCESS_VIDEOS:
                    logger.info(f"Traitement de la vidéo {video['id']} (bypass détection)...")
                    processed_path = self.processor.process_video(video_path)
                    
                    if processed_path:
                        logger.info(f"✓ Vidéo traitée et rendue unique")
                        video_path = processed_path
                        
                        # Ajouter watermark si activé
                        if self.config.ADD_WATERMARK:
                            logger.info(f"Ajout du watermark...")
                            watermarked_path = self.processor.add_watermark(
                                video_path, 
                                self.config.WATERMARK_TEXT
                            )
                            if watermarked_path:
                                logger.info(f"✓ Watermark ajouté")
                                video_path = watermarked_path
                    else:
                        logger.warning(f"⊗ Échec traitement, utilisation de l'original")
                
                # Ajouter à la base de données
                video['local_path'] = video_path
                if not self.db.add_video(video):
                    logger.warning(f"⊗ Échec de l'ajout en base pour {video['id']}")
                    continue
                
                # Initialiser Selenium seulement maintenant (lazy loading COMPLET)
                if not self.uploader_ready:
                    logger.info("Initialisation de Selenium pour l'upload...")
                    
                    # Importer et créer l'uploader SEULEMENT maintenant
                    from uploader.selenium_uploader import SeleniumUploader
                    self.uploader = SeleniumUploader(self.config)
                    
                    if not self.uploader.initialize_browser():
                        logger.error("Échec de l'initialisation du navigateur")
                        continue
                    if not self.uploader.login():
                        logger.error("Échec de la connexion à TikTok")
                        continue
                    self.uploader_ready = True
                    logger.info("✓ Selenium prêt pour les uploads")
                
                # Préparer la description
                description = video.get('desc', '')[:100]  # Limiter la longueur
                hashtags = ['#viral', '#fyp', '#trending', '#foryou']
                
                # Upload sur TikTok
                logger.info(f"Upload de la vidéo {video['id']}...")
                upload_success = self.uploader.upload_video(
                    video_path=video_path,
                    description=description,
                    hashtags=hashtags
                )
                
                if upload_success:
                    self.db.mark_as_uploaded(video['id'])
                    uploaded_count += 1
                    logger.info(
                        f"✓ Vidéo {video['id']} uploadée avec succès "
                        f"({uploaded_count}/{remaining_slots})"
                    )
                    
                    # Pause entre uploads
                    if uploaded_count < remaining_slots:
                        self.rate_limiter.wait_random_delay()
                    
                    # Pause longue tous les 5 uploads
                    if self.rate_limiter.should_take_break(uploaded_count):
                        self.rate_limiter.take_long_break(30, 45)
                else:
                    logger.warning(f"⊗ Échec de l'upload de {video['id']}")
                
                # Vérifier qu'on est toujours dans les heures actives
                if not self.rate_limiter.is_active_hours():
                    logger.info("Hors heures d'activité, arrêt du cycle")
                    break
            
            # Nettoyage des anciennes vidéos
            logger.info("\n--- Nettoyage ---")
            self.downloader.cleanup_old_videos(keep_count=50)
            
            logger.info(f"\n✓ Cycle terminé - {uploaded_count} vidéos uploadées")
            
        except Exception as e:
            logger.error(f"Erreur dans le processus: {e}", exc_info=True)
    
    async def run(self):
        """Lancer le bot en boucle continue"""
        try:
            logger.info("Démarrage du bot TikTok...")
            logger.info("⚠️  IMPORTANT: TikTok limite fortement les requêtes - 1 requête toutes les 2h recommandé")
            
            # NE PAS initialiser le scraper ici - le faire JUSTE AVANT utilisation
            # pour éviter les délais qui déclenchent la détection de bot
            self.uploader_ready = False
            
            logger.info("✓ Bot prêt")
            
            # Boucle principale
            cycle_count = 0
            while True:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"CYCLE #{cycle_count}")
                logger.info(f"{'='*60}")
                
                try:
                    # Initialiser le scraper JUSTE AVANT de l'utiliser
                    logger.info("Initialisation du scraper...")
                    await self.scraper.initialize()
                    
                    # Traiter les vidéos IMMÉDIATEMENT
                    await self.process_videos()
                    
                    # Fermer IMMÉDIATEMENT après utilisation
                    await self.scraper.close()
                    logger.info("✓ Scraper fermé")
                    
                except Exception as e:
                    logger.error(f"Erreur durant le cycle {cycle_count}: {e}", exc_info=True)
                    # S'assurer que le scraper est fermé même en cas d'erreur
                    try:
                        await self.scraper.close()
                    except:
                        pass
                
                # Attendre avant le prochain cycle
                wait_minutes = self.config.CHECK_INTERVAL / 60
                logger.info(f"\n⏳ Attente de {wait_minutes:.0f} minutes avant le prochain cycle...")
                await asyncio.sleep(self.config.CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Arrêt du bot demandé par l'utilisateur")
        
        except Exception as e:
            logger.error(f"Erreur critique: {e}", exc_info=True)
        
        finally:
            # Nettoyage
            logger.info("Fermeture des composants...")
            try:
                await self.scraper.close()
            except:
                pass
            if self.uploader_ready and self.uploader is not None:
                try:
                    self.uploader.close()
                except:
                    pass
            self.db.close()
            logger.info("✓ Bot arrêté proprement")


def main():
    """Point d'entrée principal"""
    # Créer la configuration
    config = Config()
    setup_logging(config)
    
    # Afficher les informations
    logger.info("=" * 60)
    logger.info("BOT TIKTOK - RÉCUPÉRATION ET REPUBLICATION")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"  - Likes minimum: {config.MIN_LIKES:,}")
    logger.info(f"  - Vues minimum: {config.MIN_VIEWS:,}")
    logger.info(f"  - Taux engagement minimum: {config.MIN_ENGAGEMENT_RATE:.1%}")
    logger.info(f"  - Max vidéos/jour: {config.MAX_VIDEOS_PER_DAY}")
    logger.info(f"  - Hashtags ciblés: {', '.join(config.TARGET_HASHTAGS)}")
    logger.info(f"  - Heures actives: {config.ACTIVE_HOURS_START}h-{config.ACTIVE_HOURS_END}h")
    logger.info("=" * 60)
    
    logger.warning("\n⚠️  AVERTISSEMENT:")
    logger.warning("Ce bot peut violer les conditions d'utilisation de TikTok.")
    logger.warning("Les vidéos appartiennent à leurs créateurs originaux.")
    logger.warning("Utilisez ce bot à vos propres risques.\n")
    
    # Lancer le bot
    bot = TikTokBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()

