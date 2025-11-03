"""Configuration centralisée pour le bot TikTok"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration principale du bot"""
    
    # Credentials TikTok
    TIKTOK_USERNAME = os.getenv('TIKTOK_USERNAME', '')
    TIKTOK_PASSWORD = os.getenv('TIKTOK_PASSWORD', '')
    
    # Critères de sélection des vidéos (RÉDUITS pour avoir plus de résultats)
    MIN_LIKES = 5000  # Réduit de 10000
    MIN_VIEWS = 50000  # Réduit de 100000
    MIN_ENGAGEMENT_RATE = 0.03  # 3% (réduit de 5%)
    
    # Hashtags ciblés pour la recherche
    TARGET_HASHTAGS = ['#viral', '#fyp', '#trending', '#foryou', '#tiktok']
    
    # Limites et délais
    MAX_VIDEOS_PER_DAY = 20
    MIN_DELAY_BETWEEN_UPLOADS = 300  # 5 minutes en secondes
    MAX_DELAY_BETWEEN_UPLOADS = 900  # 15 minutes en secondes
    CHECK_INTERVAL = 7200  # 2 heures entre chaque cycle (TikTok rate limiting)
    
    # Heures d'activité (pour paraître humain)
    ACTIVE_HOURS_START = 0 # 8h du matin
    ACTIVE_HOURS_END = 24   # 23h le soir
    
    # Base de données
    DATABASE_URL = 'sqlite:///tiktok_bot.db'
    
    # Dossiers
    DOWNLOAD_FOLDER = 'downloaded_videos'
    LOGS_FOLDER = 'logs'
    COOKIES_FILE = 'tiktok_cookies.pkl'
    
    # Options Selenium
    HEADLESS_MODE = False  # Mettre à True pour mode invisible
    
    # Scraping (RÉDUIT pour éviter rate limiting de TikTok)
    TRENDING_VIDEOS_COUNT = 15  # Réduit de 50 pour éviter détection
    HASHTAG_VIDEOS_COUNT = 10  # Réduit de 30
    
    # Traitement vidéo (pour éviter détection de contenu dupliqué)
    PROCESS_VIDEOS = True  # Modifier les vidéos avant upload
    ADD_WATERMARK = False  # Ajouter un watermark discret
    WATERMARK_TEXT = "@YourHandle"  # Texte du watermark
    
    @classmethod
    def create_folders(cls):
        """Créer les dossiers nécessaires s'ils n'existent pas"""
        os.makedirs(cls.DOWNLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.LOGS_FOLDER, exist_ok=True)

