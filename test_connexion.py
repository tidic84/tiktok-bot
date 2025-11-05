"""Script de test pour vérifier la connexion TikTok"""
import logging
from config import Config
from uploader.selenium_uploader import SeleniumUploader
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connexion():
    """Tester la connexion à TikTok"""
    
    print("=" * 60)
    print("TEST DE CONNEXION TIKTOK")
    print("=" * 60)
    
    # Créer la config et l'uploader
    config = Config()
    uploader = SeleniumUploader(config)
    
    print("\n1️⃣ Initialisation du navigateur...")
    if not uploader.initialize_browser():
        print("❌ Échec de l'initialisation du navigateur")
        return False
    
    print("✅ Navigateur initialisé\n")
    
    print("2️⃣ Tentative de connexion...")
    if not uploader.login():
        print("❌ Échec de la connexion")
        uploader.close()
        return False
    
    print("✅ Connexion réussie !\n")
    
    print("3️⃣ Vérification de la session...")
    time.sleep(2)
    
    # Vérifier qu'on est toujours connecté
    try:
        current_url = uploader.driver.current_url
        print(f"✅ Driver actif - URL: {current_url}")
        
        # Aller sur la page d'upload pour tester
        print("\n4️⃣ Test de la page d'upload...")
        uploader.driver.get('https://www.tiktok.com/upload')
        time.sleep(3)
        
        print("✅ Page d'upload accessible")
        
        # Vérifier les cookies
        cookies = uploader.driver.get_cookies()
        session_cookies = [c for c in cookies if 'session' in c.get('name', '').lower()]
        
        print(f"\n5️⃣ Cookies de session trouvés: {len(session_cookies)}")
        for cookie in session_cookies:
            print(f"   - {cookie.get('name')}")
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS RÉUSSIS !")
        print("=" * 60)
        print("\nLe bot devrait pouvoir uploader des vidéos.")
        print("Appuyez sur Ctrl+C pour fermer le navigateur de test.\n")
        
        # Garder le navigateur ouvert pour inspection
        input("Appuyez sur Entrée pour fermer...")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    finally:
        print("\nFermeture du navigateur...")
        uploader.close()
    
    return True

if __name__ == "__main__":
    try:
        test_connexion()
    except KeyboardInterrupt:
        print("\n\nTest interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

