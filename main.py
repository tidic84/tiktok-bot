"""
Bot TikTok - Récupération et republication automatique de vidéos virales
"""
import asyncio
import logging
import re
import sys
from pathlib import Path
from datetime import datetime

from config import Config
from scraper.tiktok_scraper import TikTokScraper
from scraper.url_scraper import URLScraper
from scraper.video_filter import VideoFilter
from downloader.video_downloader import VideoDownloader
from processor.video_processor import VideoProcessor  # Traitement vidéo
# NOTE: SeleniumUploader sera importé SEULEMENT quand nécessaire pour éviter les conflits avec Playwright
from database.db_manager import DatabaseManager
from utils.rate_limiter import RateLimiter
from utils.video_cleaner import VideoCleaner  # Nettoyage automatique


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

HASHTAG_PATTERN = re.compile(r'#(\w+)', re.UNICODE)


def sanitize_description(description: str, max_hashtags: int = 5) -> str:
    """
    Supprimer les hashtags en double et limiter leur nombre, en évitant les répétitions.
    
    Args:
        description: Description originale
        max_hashtags: Nombre maximum de hashtags autorisés
        
    Returns:
        Description nettoyée respectant la limite de hashtags
    """
    if not description:
        return ""
    
    text = description.strip()
    
    # Extraire les hashtags dans l'ordre d'apparition
    unique_hashtags = []
    seen = set()
    for match in HASHTAG_PATTERN.finditer(text):
        hashtag = match.group(0)
        key = hashtag.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_hashtags.append(hashtag)
        if len(unique_hashtags) >= max_hashtags:
            break
    
    # Supprimer tous les hashtags du texte original
    text_without_tags = HASHTAG_PATTERN.sub(' ', text)
    text_without_tags = re.sub(r'\s+', ' ', text_without_tags).strip()
    
    # Recomposer la description: texte + hashtags filtrés
    # IMPORTANT: Mettre les hashtags sur une NOUVELLE LIGNE pour que TikTok les détecte
    parts = []
    if text_without_tags:
        parts.append(text_without_tags)
    if unique_hashtags:
        # Hashtags séparés par des espaces, sur une nouvelle ligne
        parts.append(' '.join(unique_hashtags[:max_hashtags]))
    
    # Joindre avec un saut de ligne entre texte et hashtags
    sanitized = '\n'.join(parts).strip()
    return sanitized


class TikTokBot:
    """Bot principal pour récupérer et republier des vidéos TikTok"""
    
    def __init__(self):
        """Initialiser le bot"""
        self.config = Config()
        self.config.create_folders()
        
        # Initialiser les composants
        self.scraper = TikTokScraper(self.config)
        self.url_scraper = URLScraper(self.config)  # Scraper alternatif plus fiable
        self.filter = VideoFilter(self.config)
        self.downloader = VideoDownloader(self.config)
        self.processor = VideoProcessor(self.config)  # Traitement vidéo
        # NOTE: uploader sera initialisé seulement quand nécessaire (lazy loading complet)
        self.uploader = None
        self.db = DatabaseManager(self.config.DATABASE_URL)
        self.rate_limiter = RateLimiter(self.config)
        self.cleaner = VideoCleaner(self.config)  # Nettoyeur de vidéos
        
        logger.info("=" * 60)
        logger.info("TikTok Bot initialisé")
        logger.info("=" * 60)
    
    async def process_videos(self):
        """Processus principal de récupération et republication"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("DÉBUT DU CYCLE DE TRAITEMENT")
            logger.info("=" * 60)
            
            # Nettoyer les fichiers temporaires
            self.cleaner.cleanup_temp_files()
            
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
            
            # 1. Récupérer les vidéos selon le mode configuré
            logger.info("\n--- Phase 1: Récupération des vidéos ---")
            logger.info(f"Mode de scraping: {self.config.SCRAPING_MODE.upper()}")
            
            if self.config.SCRAPING_MODE == 'search':
                # Recherche par mots-clés avec yt-dlp (RECOMMANDÉ)
                logger.info(f"🔍 Recherche par mots-clés: {', '.join(self.config.TARGET_KEYWORDS)}")
                all_videos = self.url_scraper.get_videos_from_search(
                    self.config.TARGET_KEYWORDS,
                    self.config.VIDEOS_PER_KEYWORD
                )
            elif self.config.SCRAPING_MODE == 'creators':
                # Utiliser le scraper URL pour récupérer depuis des créateurs
                logger.info(f"🔍 Récupération depuis les créateurs: {', '.join(self.config.TARGET_CREATORS)}")
                all_videos = self.url_scraper.get_videos_from_creators(
                    self.config.TARGET_CREATORS,
                    self.config.VIDEOS_PER_CREATOR
                )
            else:
                # Utiliser l'API TikTok (peut être bloqué)
                logger.info(f"🔍 Recherche API dans les hashtags: {', '.join(self.config.TARGET_HASHTAGS)}")
                # Utiliser immédiatement la session (pas de délai)
                # TikTok bloque si on attend trop entre init() et utilisation
                all_videos = await self.scraper.get_videos_by_hashtags()
            
            if not all_videos:
                logger.warning("Aucune vidéo récupérée")
                return
            
            # 2. Sélection intelligente de la meilleure vidéo
            logger.info("\n--- Phase 2: Sélection de la vidéo ---")

            # Si AUTO_PUBLISH est activé, vérifier d'abord les vidéos en attente
            if self.config.AUTO_PUBLISH:
                pending_records = self.db.get_pending_videos(limit=remaining_slots)
                if pending_records:
                    logger.info(f"🔁 AUTO_PUBLISH activé - Reprise de {len(pending_records)} vidéo(s) en attente")
                    videos_to_upload = []
                    for record in pending_records:
                        videos_to_upload.append({
                            'id': record.id,
                            'author': record.author,
                            'desc': record.description or '',
                            'likes': record.likes or 0,
                            'views': record.views or 0,
                            'shares': record.shares or 0,
                            'comments': record.comments or 0,
                            'engagement_rate': record.engagement_rate or 0.0,
                            'video_url': record.original_url or '',
                            'local_path': record.local_path,
                            'create_time': 0
                        })
                    logger.info(f"✓ {len(videos_to_upload)} vidéo(s) en attente prêtes pour publication")
                    # Passer directement à la phase d'upload (sauter la sélection)
                    if videos_to_upload:
                        # Aller directement à la phase 3
                        logger.info(f"\n--- Phase 3: Traitement de {len(videos_to_upload)} vidéo(s) ---")
                        uploaded_count = 0

                        for i, video in enumerate(videos_to_upload):
                            if uploaded_count >= remaining_slots:
                                logger.info(f"✓ Limite de {remaining_slots} vidéos atteinte pour ce cycle")
                                break

                            logger.info(f"\n[{i+1}/{len(videos_to_upload)}] Traitement de la vidéo {video['id']}")

                            # Vérifier si la vidéo est déjà en base
                            existing_record = self.db.get_video(video['id'])
                            if existing_record and existing_record.is_uploaded:
                                logger.info(f"⊗ Vidéo {video['id']} déjà uploadée, passage à la suivante")
                                continue

                            # Vérifier que le fichier existe
                            video_path = video.get('local_path')
                            if not video_path or not Path(video_path).exists():
                                logger.warning(f"⊗ Fichier local introuvable pour {video['id']}")
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
                            original_description = video.get('desc', '')
                            max_hashtags = getattr(self.config, 'MAX_HASHTAGS', 5)
                            sanitized_description = sanitize_description(
                                original_description,
                                max_hashtags=max_hashtags
                            )

                            video['desc'] = sanitized_description

                            # Upload sur TikTok
                            logger.info(f"Upload de la vidéo {video['id']}...")
                            upload_success = self.uploader.upload_video(
                                video_path=video_path,
                                title="",
                                description=sanitized_description,
                                hashtags=None
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
                        return

            if self.config.SMART_SELECTION:
                try:
                    known_ids = self.db.get_known_video_ids()
                    selected_video = self.filter.select_best_video_randomly(
                        all_videos,
                        top_n=self.config.TOP_N_SELECTION,
                        exclude_ids=known_ids
                    )
                    videos_to_upload = [selected_video]
                    logger.info(f"✓ 1 vidéo sélectionnée intelligemment (parmi top {self.config.TOP_N_SELECTION})")
                except ValueError as e:
                    logger.warning(f"Aucune vidéo ne correspond aux critères ou toutes déjà connues: {e}")
                    
                    pending_records = self.db.get_pending_videos(limit=remaining_slots)
                    if pending_records:
                        logger.info(f"🔁 Reprise de {len(pending_records)} vidéo(s) en attente dans la base")
                        videos_to_upload = []
                        for record in pending_records:
                            videos_to_upload.append({
                                'id': record.id,
                                'author': record.author,
                                'desc': record.description or '',
                                'likes': record.likes or 0,
                                'views': record.views or 0,
                                'shares': record.shares or 0,
                                'comments': record.comments or 0,
                                'engagement_rate': record.engagement_rate or 0.0,
                                'video_url': record.original_url or '',
                                'local_path': record.local_path,
                                'create_time': 0  # valeur par défaut si inconnue
                            })
                        logger.info(f"✓ {len(videos_to_upload)} vidéo(s) récupérée(s) depuis les enregistrements en attente")
                    else:
                        logger.info("Aucune vidéo en attente à reprendre. Cycle sans action.")
                        return
            else:
                # Ancienne méthode: traiter plusieurs vidéos
                quality_videos = self.filter.filter_videos(all_videos)
                
                if not quality_videos:
                    logger.warning("Aucune vidéo ne correspond aux critères")
                    return
                
                videos_to_upload = quality_videos[:remaining_slots]
                logger.info(f"✓ {len(videos_to_upload)} vidéos sélectionnées (mode classique)")
            
            # 3. Traiter la/les vidéo(s) sélectionnée(s)
            logger.info(f"\n--- Phase 3: Traitement de {len(videos_to_upload)} vidéo(s) ---")
            
            uploaded_count = 0
            
            for i, video in enumerate(videos_to_upload):
                if uploaded_count >= remaining_slots:
                    logger.info(f"✓ Limite de {remaining_slots} vidéos atteinte pour ce cycle")
                    break
                
                logger.info(f"\n[{i+1}/{len(videos_to_upload)}] Traitement de la vidéo {video['id']}")
                
                # Vérifier si la vidéo est déjà en base
                existing_record = self.db.get_video(video['id'])
                if existing_record and existing_record.is_uploaded:
                    logger.info(f"⊗ Vidéo {video['id']} déjà uploadée, passage à la suivante")
                    continue
                
                # Télécharger la vidéo
                video_path = video.get('local_path')
                if video_path and not Path(video_path).exists():
                    logger.info(
                        f"Fichier existant introuvable pour {video['id']} ({video_path}), nouveau téléchargement..."
                    )
                    video_path = None
                
                if not video_path:
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
                    logger.warning(f"⊗ Échec de l'enregistrement en base pour {video['id']}")
                    continue

                # Vérifier si l'auto-publication est activée
                if not self.config.AUTO_PUBLISH:
                    logger.info(f"ℹ️  Auto-publication désactivée - vidéo {video['id']} mise en file d'attente")
                    logger.info(f"   La vidéo sera publiée lors du prochain cycle avec AUTO_PUBLISH=True")
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
                
                # Préparer la description en respectant les limites de TikTok
                original_description = video.get('desc', '')  # Description complète originale
                max_hashtags = getattr(self.config, 'MAX_HASHTAGS', 5)
                sanitized_description = sanitize_description(
                    original_description,
                    max_hashtags=max_hashtags
                )
                
                if sanitized_description != original_description:
                    logger.info(
                        f"🧹 Description nettoyée (hashtags uniques ≤ {max_hashtags}): "
                        f"{sanitized_description[:100]}{'...' if len(sanitized_description) > 100 else ''}"
                    )
                else:
                    logger.info(
                        f"📝 Description conservée ({len(sanitized_description)} caractères): "
                        f"{sanitized_description[:100]}{'...' if len(sanitized_description) > 100 else ''}"
                    )
                
                video['desc'] = sanitized_description
                
                # Upload sur TikTok avec la description nettoyée
                logger.info(f"Upload de la vidéo {video['id']}...")
                upload_success = self.uploader.upload_video(
                    video_path=video_path,
                    title="",  # Pas de titre séparé
                    description=sanitized_description,
                    hashtags=None  # Pas de hashtags supplémentaires (déjà dans la description)
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
            
            # Nettoyage au démarrage si activé
            if self.config.CLEANUP_ON_STARTUP:
                logger.info("\n🧹 Nettoyage automatique au démarrage...")
                stats = self.cleaner.get_folder_stats()
                logger.info(
                    f"📊 Dossier vidéos: {stats['count']} fichier(s), "
                    f"{stats['total_size_mb']:.2f} MB"
                )
                
                files_deleted, space_freed = self.cleaner.cleanup_old_videos()
                
                if files_deleted > 0:
                    logger.info(f"✓ {files_deleted} vidéo(s) supprimée(s), {space_freed:.2f} MB libérés")
                
                # Nettoyage des vidéos en attente trop anciennes
                pending_deleted = self.db.cleanup_old_pending_videos(
                    days=self.config.CLEANUP_PENDING_VIDEOS_DAYS
                )
                if pending_deleted > 0:
                    logger.info(f"✓ {pending_deleted} vidéo(s) en attente supprimée(s) de la DB")
            
            # Boucle principale
            cycle_count = 0
            while True:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"CYCLE #{cycle_count}")
                logger.info(f"{'='*60}")
                
                try:
                    # Nettoyage périodique toutes les 10 cycles
                    if cycle_count % 10 == 0 and self.config.AUTO_CLEANUP_VIDEOS:
                        logger.info("\n🧹 Nettoyage périodique...")
                        self.cleaner.cleanup_old_videos()
                        # Nettoyage des vidéos en attente
                        self.db.cleanup_old_pending_videos(days=self.config.CLEANUP_PENDING_VIDEOS_DAYS)
                    
                    # Initialiser le scraper seulement si mode API
                    if self.config.SCRAPING_MODE == 'api':
                        logger.info("Initialisation du scraper API...")
                        await self.scraper.initialize()
                    
                    # Traiter les vidéos IMMÉDIATEMENT
                    await self.process_videos()
                    
                    # Fermer IMMÉDIATEMENT après utilisation (si mode API)
                    if self.config.SCRAPING_MODE == 'api':
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
    logger.info(f"  - Mode de scraping: {config.SCRAPING_MODE.upper()}")
    if config.SCRAPING_MODE == 'search':
        logger.info(f"  - Mots-clés de recherche: {', '.join(config.TARGET_KEYWORDS)}")
        logger.info(f"  - Vidéos par mot-clé: {config.VIDEOS_PER_KEYWORD}")
    elif config.SCRAPING_MODE == 'creators':
        logger.info(f"  - Créateurs suivis: {', '.join(config.TARGET_CREATORS)}")
        logger.info(f"  - Vidéos par créateur: {config.VIDEOS_PER_CREATOR}")
    else:
        logger.info(f"  - Hashtags API: {', '.join(config.TARGET_HASHTAGS)}")
    logger.info(f"  - Likes minimum: {config.MIN_LIKES:,}")
    logger.info(f"  - Vues minimum: {config.MIN_VIEWS:,}")
    logger.info(f"  - Taux engagement minimum: {config.MIN_ENGAGEMENT_RATE:.1%}")
    logger.info(f"  - Max vidéos/jour: {config.MAX_VIDEOS_PER_DAY}")
    logger.info(f"  - Heures actives: {config.ACTIVE_HOURS_START}h-{config.ACTIVE_HOURS_END}h")
    logger.info(f"  - Auto-publication: {'ACTIVÉE' if config.AUTO_PUBLISH else 'DÉSACTIVÉE'}")
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

