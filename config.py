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
    MIN_LIKES = int(os.getenv('MIN_LIKES', 500))  # Réduit de 50000
    MIN_VIEWS = int(os.getenv('MIN_VIEWS', 1000))  # Réduit de 100000
    MIN_ENGAGEMENT_RATE = float(os.getenv('MIN_ENGAGEMENT_RATE', 0.03))  # 3% (réduit de 5%)
    
    # Mots-clés/hashtags ciblés pour la recherche (utilisé si SCRAPING_MODE = 'search' ou 'api')
    # Peut être des hashtags (avec ou sans #) ou des mots-clés simples
    # Exemples: ['recipes', 'food', 'cooking'] ou ['#Recipes', '#Foodtok']
    TARGET_KEYWORDS = ['recipes', 'food cooking', 'easy recipes']
    
    # Nombre de vidéos à récupérer par mot-clé (mode 'search')
    VIDEOS_PER_KEYWORD = 10
    
    # PLATEFORME SOURCE: 'tiktok' ou 'instagram'
    # Détermine depuis quelle plateforme scraper les vidéos
    SOURCE_PLATFORM = os.getenv('SOURCE_PLATFORM', 'tiktok')

    # MODE DE SCRAPING: 'api', 'creators' ou 'search'
    # 'api' = utilise l'API TikTok (peut être bloqué) - SEULEMENT pour TikTok
    # 'creators' = récupère des vidéos de créateurs spécifiques (RECOMMANDÉ - fonctionne bien!)
    # 'search' = recherche par mots-clés/hashtags avec yt-dlp (EXPÉRIMENTAL - peut ne pas fonctionner)
    SCRAPING_MODE = 'creators'
    
    # Créateurs TikTok à suivre (utilisé si SCRAPING_MODE = 'creators')
    # Trouvez des créateurs populaires dans votre niche
    # Peut être configuré dans .env avec TARGET_CREATORS (séparés par des virgules)
    # Exemples pour food/recipes:
    _creators_env = os.getenv('TARGET_CREATORS', '')
    if _creators_env.strip():
        # Charger depuis .env (séparés par des virgules)
        TARGET_CREATORS = [c.strip() for c in _creators_env.split(',') if c.strip()]
    else:
        # Valeurs par défaut
        TARGET_CREATORS = [
            'aflavorfulbite',  # Gordon Ramsay - chef célèbre
            'joandbart',          # Recettes simples et rapides
            'feelgoodfoodie',         # Recettes healthy
            'cookingwithshereen',     # Recettes moyen-orientales
            'freshfitfood_',
            'malcomsfood2'                # Recettes virales
        ]
    
    # Nombre de vidéos à récupérer par créateur (mode 'creators')
    VIDEOS_PER_CREATOR = 10

    # Créateurs Instagram à suivre (utilisé si SOURCE_PLATFORM = 'instagram' et SCRAPING_MODE = 'creators')
    # Trouvez des créateurs populaires Instagram dans votre niche
    # Peut être configuré dans .env avec INSTAGRAM_CREATORS (séparés par des virgules)
    # Exemples pour food/recipes:
    _instagram_creators_env = os.getenv('INSTAGRAM_CREATORS', '')
    if _instagram_creators_env.strip():
        # Charger depuis .env (séparés par des virgules)
        INSTAGRAM_CREATORS = [c.strip() for c in _instagram_creators_env.split(',') if c.strip()]
    else:
        # Valeurs par défaut
        INSTAGRAM_CREATORS = [
            'gordonramsayofficial',  # Gordon Ramsay - chef célèbre
            'foodnetwork',           # Food Network
            'buzzfeedtasty',         # BuzzFeed Tasty
            'cookinglight',          # Recettes healthy
            'bonappetitmag',         # Bon Appétit Magazine
            'thefeedfeed'            # The Feed Feed
        ]
    
    # COMPATIBILITÉ: Alias pour TARGET_KEYWORDS
    @property
    def TARGET_HASHTAGS(self):
        """Alias pour TARGET_KEYWORDS (compatibilité)"""
        return self.TARGET_KEYWORDS
    
    # Limites et délais
    MAX_VIDEOS_PER_DAY = int(os.getenv('MAX_VIDEOS_PER_DAY', 10))
    MIN_DELAY_BETWEEN_UPLOADS = 10800  # 3 heure en secondes
    MAX_DELAY_BETWEEN_UPLOADS = 21600  # 6 heures en secondes
    CHECK_INTERVAL = 7200  # 2 heures entre chaque cycle (TikTok rate limiting)
    
    # Heures d'activité (pour paraître humain)
    ACTIVE_HOURS_START = int(os.getenv('ACTIVE_HOURS_START', 8))  # 8h du matin
    ACTIVE_HOURS_END = int(os.getenv('ACTIVE_HOURS_END', 23))   # 23h le soir
    
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
    ADD_WATERMARK = True   # Ajouter un watermark discret (ACTIVÉ pour plus d'unicité)
    WATERMARK_TEXT = "🔥"  # Emoji discret (changez si vous voulez)
    
    # Nettoyage automatique des vieilles vidéos
    AUTO_CLEANUP_VIDEOS = True  # Supprimer automatiquement les vieilles vidéos
    KEEP_VIDEOS_DAYS = 0.03  # Conserver les vidéos pendant 0.03 jours (environ 0.72 heures)
    CLEANUP_ON_STARTUP = True  # Nettoyer au démarrage du bot
    
    # Sélection intelligente des vidéos
    SMART_SELECTION = True  # Activer la sélection intelligente
    TOP_N_SELECTION = 10  # Sélectionner aléatoirement parmi les N meilleures vidéos
    CLEANUP_PENDING_VIDEOS_DAYS = 7  # Supprimer les vidéos en attente après N jours
    
    # Gestion des avertissements TikTok
    SKIP_RESTRICTED_CONTENT = True  # Ignorer automatiquement les vidéos avec avertissement de contenu restreint
    
    # Gestion des descriptions TikTok
    MAX_HASHTAGS = int(os.getenv('MAX_HASHTAGS', 5))  # Nombre maximum de hashtags autorisés dans la description
    
    @classmethod
    def create_folders(cls):
        """Créer les dossiers nécessaires s'ils n'existent pas"""
        os.makedirs(cls.DOWNLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.LOGS_FOLDER, exist_ok=True)

