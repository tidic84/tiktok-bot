#!/usr/bin/env python3
"""Script de validation complète de la configuration du bot"""
import logging
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def validate_setup():
    """Valider la configuration complète du bot"""
    logger.info("=" * 70)
    logger.info("VALIDATION DE LA CONFIGURATION DU BOT INSTAGRAM COSPLAY")
    logger.info("=" * 70)

    all_valid = True

    # 1. Configuration de base
    logger.info("\n[1/7] Vérification de la configuration de base...")
    try:
        config = Config()
        config.create_folders()

        if config.SOURCE_PLATFORM == 'instagram':
            logger.info("   ✅ Plateforme source: INSTAGRAM")
        else:
            logger.warning(f"   ⚠️  Plateforme source: {config.SOURCE_PLATFORM} (devrait être 'instagram')")
            all_valid = False

        if config.SCRAPING_MODE == 'creators':
            logger.info("   ✅ Mode de scraping: CREATORS")
        else:
            logger.warning(f"   ⚠️  Mode de scraping: {config.SCRAPING_MODE} (devrait être 'creators')")
            all_valid = False

    except Exception as e:
        logger.error(f"   ❌ Erreur configuration: {e}")
        all_valid = False

    # 2. Créateurs Instagram
    logger.info("\n[2/7] Vérification des créateurs Instagram...")
    try:
        creators = config.INSTAGRAM_CREATORS
        if creators and len(creators) > 0:
            logger.info(f"   ✅ {len(creators)} créateur(s) configuré(s):")
            for creator in creators:
                logger.info(f"      - @{creator}")
        else:
            logger.warning("   ⚠️  Aucun créateur Instagram configuré")
            all_valid = False
    except Exception as e:
        logger.error(f"   ❌ Erreur créateurs: {e}")
        all_valid = False

    # 3. Proxies Bright Data
    logger.info("\n[3/7] Vérification des proxies Bright Data...")
    try:
        proxies = config.INSTAGRAM_PROXIES
        if proxies and len(proxies) > 0:
            logger.info(f"   ✅ {len(proxies)} proxy(ies) configuré(s)")
            for i, proxy in enumerate(proxies, 1):
                # Masquer le mot de passe
                if '@' in proxy:
                    parts = proxy.split('@')
                    if len(parts) == 2:
                        credentials = parts[0].split('//')[-1]
                        if ':' in credentials:
                            user = credentials.split(':')[0]
                            proxy_display = proxy.replace(credentials, f"{user}:***")
                            logger.info(f"      {i}. {proxy_display}")
                else:
                    logger.info(f"      {i}. {proxy}")
        else:
            logger.warning("   ⚠️  Aucun proxy configuré")
            logger.info("      (Les proxies aident à éviter le rate limiting)")
    except Exception as e:
        logger.error(f"   ❌ Erreur proxies: {e}")

    # 4. Session Instagram
    logger.info("\n[4/7] Vérification de la session Instagram...")
    try:
        username = config.INSTAGRAM_USERNAME
        session_file = config.INSTAGRAM_SESSION_FILE

        if username:
            logger.info(f"   ✅ Username Instagram: {username}")
        else:
            logger.warning("   ⚠️  Aucun username Instagram configuré")
            all_valid = False

        if session_file:
            session_path = Path(session_file)
            if session_path.exists():
                logger.info(f"   ✅ Fichier de session trouvé: {session_file}")
                size = session_path.stat().st_size
                logger.info(f"      Taille: {size} octets")
            else:
                logger.error(f"   ❌ Fichier de session introuvable: {session_file}")
                logger.info(f"      Créez la session avec: instaloader -l {username}")
                all_valid = False
        else:
            logger.warning("   ⚠️  Aucun fichier de session configuré")
            all_valid = False

    except Exception as e:
        logger.error(f"   ❌ Erreur session: {e}")
        all_valid = False

    # 5. Dossiers
    logger.info("\n[5/7] Vérification des dossiers...")
    try:
        download_folder = Path(config.DOWNLOAD_FOLDER)
        logs_folder = Path(config.LOGS_FOLDER)

        if download_folder.exists():
            logger.info(f"   ✅ Dossier de téléchargement: {config.DOWNLOAD_FOLDER}")
        else:
            logger.warning(f"   ⚠️  Dossier de téléchargement manquant (sera créé)")

        if logs_folder.exists():
            logger.info(f"   ✅ Dossier de logs: {config.LOGS_FOLDER}")
        else:
            logger.warning(f"   ⚠️  Dossier de logs manquant (sera créé)")

    except Exception as e:
        logger.error(f"   ❌ Erreur dossiers: {e}")

    # 6. Modules Python
    logger.info("\n[6/7] Vérification des modules Python...")
    try:
        import instaloader
        logger.info(f"   ✅ instaloader: {instaloader.__version__}")
    except ImportError:
        logger.error("   ❌ instaloader non installé")
        logger.info("      Installez avec: pip install instaloader")
        all_valid = False

    try:
        import requests
        logger.info(f"   ✅ requests installé")
    except ImportError:
        logger.error("   ❌ requests non installé")
        all_valid = False

    # 7. Test de connexion (sans proxy pour éviter rate limit)
    logger.info("\n[7/7] Test de connexion Instagram...")
    try:
        from scraper.instagram_scraper import InstagramScraper
        scraper = InstagramScraper(config)

        if scraper.authenticated:
            logger.info("   ✅ Authentification Instagram réussie")
        else:
            logger.warning("   ⚠️  Instagram non authentifié")
            logger.info("      Le bot pourra avoir des limitations")

        scraper.close()

    except Exception as e:
        logger.error(f"   ❌ Erreur test connexion: {e}")

    # Résumé
    logger.info("\n" + "=" * 70)
    if all_valid:
        logger.info("✅ VALIDATION COMPLÈTE - Le bot est prêt à fonctionner!")
        logger.info("=" * 70)
        logger.info("\nCommandes pour lancer le bot:")
        logger.info("  - Test simple:   python3 test_instagram.py")
        logger.info("  - Bot complet:   python3 main.py")
        logger.info("\nNote: Si vous obtenez '401 Unauthorized', attendez 15-30 minutes")
        logger.info("      (Instagram rate limit normal après plusieurs tests)")
        return True
    else:
        logger.error("❌ VALIDATION ÉCHOUÉE - Corrigez les problèmes ci-dessus")
        logger.info("=" * 70)
        return False

if __name__ == "__main__":
    success = validate_setup()
    sys.exit(0 if success else 1)
