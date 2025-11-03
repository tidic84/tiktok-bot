"""
Script de test pour vérifier que l'installation est correcte
"""
import sys
import asyncio

def test_imports():
    """Tester que tous les modules peuvent être importés"""
    print("Test des imports...")
    
    try:
        from config import Config
        print("✓ config.py")
        
        from scraper.tiktok_scraper import TikTokScraper
        print("✓ scraper/tiktok_scraper.py")
        
        from scraper.video_filter import VideoFilter
        print("✓ scraper/video_filter.py")
        
        from downloader.video_downloader import VideoDownloader
        print("✓ downloader/video_downloader.py")
        
        from uploader.selenium_uploader import SeleniumUploader
        print("✓ uploader/selenium_uploader.py")
        
        from database.db_manager import DatabaseManager
        print("✓ database/db_manager.py")
        
        from utils.rate_limiter import RateLimiter
        print("✓ utils/rate_limiter.py")
        
        print("\n✓ Tous les modules importés avec succès!")
        return True
    
    except ImportError as e:
        print(f"\n❌ Erreur d'import: {e}")
        return False


def test_dependencies():
    """Tester que toutes les dépendances sont installées"""
    print("\nTest des dépendances...")
    
    dependencies = [
        ('TikTokApi', 'TikTokApi'),
        ('playwright', 'playwright'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv'),
        ('sqlalchemy', 'sqlalchemy'),
        ('selenium', 'selenium'),
        ('webdriver_manager', 'webdriver-manager'),
        ('fake_useragent', 'fake-useragent'),
    ]
    
    all_ok = True
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - Installez avec: pip install {package}")
            all_ok = False
    
    if all_ok:
        print("\n✓ Toutes les dépendances sont installées!")
    else:
        print("\n❌ Certaines dépendances manquent. Lancez: pip install -r requirements.txt")
    
    return all_ok


def test_config():
    """Tester la configuration"""
    print("\nTest de la configuration...")
    
    try:
        from config import Config
        config = Config()
        
        print(f"✓ MIN_LIKES: {config.MIN_LIKES:,}")
        print(f"✓ MIN_VIEWS: {config.MIN_VIEWS:,}")
        print(f"✓ MIN_ENGAGEMENT_RATE: {config.MIN_ENGAGEMENT_RATE:.1%}")
        print(f"✓ MAX_VIDEOS_PER_DAY: {config.MAX_VIDEOS_PER_DAY}")
        print(f"✓ TARGET_HASHTAGS: {', '.join(config.TARGET_HASHTAGS)}")
        print(f"✓ ACTIVE_HOURS: {config.ACTIVE_HOURS_START}h-{config.ACTIVE_HOURS_END}h")
        
        print("\n✓ Configuration valide!")
        return True
    
    except Exception as e:
        print(f"\n❌ Erreur de configuration: {e}")
        return False


def test_database():
    """Tester la base de données"""
    print("\nTest de la base de données...")
    
    try:
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager('sqlite:///test_tiktok_bot.db')
        print("✓ Base de données créée")
        
        # Test d'ajout
        test_video = {
            'id': 'test123',
            'author': 'test_user',
            'desc': 'Test video',
            'video_url': 'https://example.com/video.mp4',
            'likes': 10000,
            'views': 100000,
            'shares': 500,
            'comments': 200,
            'engagement_rate': 0.106,
        }
        
        db.add_video(test_video)
        print("✓ Ajout de vidéo réussi")
        
        # Test de vérification
        exists = db.is_video_processed('test123')
        if exists:
            print("✓ Vérification de vidéo réussie")
        
        db.close()
        
        # Nettoyer
        import os
        if os.path.exists('test_tiktok_bot.db'):
            os.remove('test_tiktok_bot.db')
            print("✓ Base de données test nettoyée")
        
        print("\n✓ Base de données fonctionnelle!")
        return True
    
    except Exception as e:
        print(f"\n❌ Erreur base de données: {e}")
        return False


def test_folders():
    """Vérifier que les dossiers nécessaires existent"""
    print("\nTest des dossiers...")
    
    import os
    from pathlib import Path
    
    folders = [
        'downloaded_videos',
        'logs',
    ]
    
    all_ok = True
    for folder in folders:
        path = Path(folder)
        if path.exists():
            print(f"✓ {folder}/ existe")
        else:
            print(f"⚠️  {folder}/ n'existe pas - sera créé au lancement")
            path.mkdir(exist_ok=True)
    
    print("\n✓ Dossiers vérifiés!")
    return True


def test_env_file():
    """Vérifier le fichier .env"""
    print("\nTest du fichier .env...")
    
    import os
    from pathlib import Path
    
    if not Path('.env').exists():
        print("⚠️  Fichier .env non trouvé")
        print("   Copiez .env.example vers .env et remplissez vos identifiants")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    username = os.getenv('TIKTOK_USERNAME', '')
    password = os.getenv('TIKTOK_PASSWORD', '')
    
    if not username or username == 'votre_username':
        print("⚠️  TIKTOK_USERNAME non configuré dans .env")
        return False
    
    if not password or password == 'votre_mot_de_passe':
        print("⚠️  TIKTOK_PASSWORD non configuré dans .env")
        return False
    
    print("✓ Fichier .env configuré")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)}")
    
    return True


def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("TEST D'INSTALLATION DU BOT TIKTOK")
    print("=" * 60)
    
    results = []
    
    # Tests
    results.append(('Imports', test_imports()))
    results.append(('Dépendances', test_dependencies()))
    results.append(('Configuration', test_config()))
    results.append(('Base de données', test_database()))
    results.append(('Dossiers', test_folders()))
    results.append(('Fichier .env', test_env_file()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ OK" if result else "❌ ÉCHEC"
        print(f"{test_name:20} : {status}")
    
    all_passed = all(r for _, r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ TOUS LES TESTS RÉUSSIS!")
        print("Vous pouvez lancer le bot avec: python main.py")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Corrigez les erreurs ci-dessus avant de lancer le bot")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

