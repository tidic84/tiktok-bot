"""Configuration centralisée pour le bot TikTok"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration principale du bot"""
    
    # Credentials TikTok
    TIKTOK_USERNAME = os.getenv('TIKTOK_USERNAME', '')
    TIKTOK_PASSWORD = os.getenv('TIKTOK_PASSWORD', '')

    # Credentials Instagram (optionnel, pour éviter le rate limiting)
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')

    # Proxy (optionnel, pour contourner les blocages d'IP)
    # Format: http://user:pass@host:port ou http://host:port
    PROXY_URL = os.getenv('PROXY_URL', '')

    # Fichier de cookies Instagram (optionnel, alternative à username/password)
    # Format JSON exporté depuis le navigateur (extension "Get cookies.txt" ou similaire)
    INSTAGRAM_COOKIES_FILE = os.getenv('INSTAGRAM_COOKIES_FILE', '')

    # Fichier de session Instagram (RECOMMANDÉ, créé par instaloader)
    # Créer avec: instaloader -l USERNAME
    # Le fichier sera nommé automatiquement: session-USERNAME
    INSTAGRAM_SESSION_FILE = os.getenv('INSTAGRAM_SESSION_FILE', '')

    # ========================================
    # PROXIES INSTAGRAM
    # ========================================
    # Les proxies aident à éviter le rate limiting et les bannissements Instagram
    # RECOMMANDÉ: Utilisez des proxies RÉSIDENTIELS pour Instagram (pas datacenter)
    # Instagram détecte et bannit facilement les proxies datacenter

    # Option 1: Proxy unique
    # Format: http://user:pass@host:port ou http://host:port
    # Exemple: 'http://user:pass@123.45.67.89:8080'
    INSTAGRAM_PROXY = os.getenv('INSTAGRAM_PROXY', '')

    # Option 2: Rotation de proxies (liste de proxies)
    # Le scraper changera de proxy pour chaque créateur
    # Format: liste de proxies au format http://user:pass@host:port
    # RECOMMANDÉ: Utilisez au moins 3-5 proxies résidentiels pour une rotation efficace
    _instagram_proxies_env = os.getenv('INSTAGRAM_PROXIES', '')
    if _instagram_proxies_env.strip():
        # Charger depuis .env (séparés par des virgules)
        INSTAGRAM_PROXIES = [p.strip() for p in _instagram_proxies_env.split(',') if p.strip()]
    else:
        # Pas de proxies par défaut - À configurer selon vos besoins
        INSTAGRAM_PROXIES = []
        # Exemples (NE PAS UTILISER TELS QUELS - remplacez par vos vrais proxies):
        # INSTAGRAM_PROXIES = [
        #     'http://user:pass@proxy1.example.com:8080',
        #     'http://user:pass@proxy2.example.com:8080',
        #     'http://user:pass@proxy3.example.com:8080',
        # ]

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

    # Délais entre les créateurs Instagram (pour éviter rate limiting)
    # Instagram limite fortement les requêtes - utilisez des délais longs !
    # Recommandations :
    # - 1-3 créateurs : 30-60 secondes (par défaut)
    # - 4-9 créateurs : 60-120 secondes
    # - 10+ créateurs : 120-180 secondes ou divisez en plusieurs sessions
    INSTAGRAM_MIN_DELAY_BETWEEN_CREATORS = 30  # Minimum 30 secondes
    INSTAGRAM_MAX_DELAY_BETWEEN_CREATORS = 60  # Maximum 60 secondes (aléatoire)

    # Délais entre les POSTS Instagram (CRITIQUE pour éviter rate limiting)
    # Instagram détecte si on parcourt les posts trop vite
    # Chaque post = 1 requête API, donc il faut des délais
    # IMPORTANT: Ne réduisez PAS ces valeurs, Instagram bannit sinon !
    INSTAGRAM_MIN_DELAY_BETWEEN_POSTS = 3  # Minimum 3 secondes entre posts
    INSTAGRAM_MAX_DELAY_BETWEEN_POSTS = 7  # Maximum 7 secondes entre posts

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
    # NOTE: FFmpeg requis pour le traitement. Si pas installé, les vidéos originales seront utilisées
    PROCESS_VIDEOS = False  # Désactivé temporairement (FFmpeg non installé)
    ADD_WATERMARK = False   # Désactivé temporairement
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

