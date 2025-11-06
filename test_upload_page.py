#!/usr/bin/env python3
"""
Script de diagnostic pour tester l'accès à la page d'upload TikTok
"""
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from uploader.cookie_manager import CookieManager

print("=" * 80)
print("TEST D'ACCÈS À LA PAGE D'UPLOAD TIKTOK")
print("=" * 80)

# Initialiser le navigateur
print("\n1. Initialisation du navigateur Chrome...")
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

try:
    print("✓ Navigateur initialisé")
    
    # Charger les cookies
    print("\n2. Chargement des cookies...")
    cookie_manager = CookieManager()
    driver.get('https://www.tiktok.com')
    time.sleep(2)
    
    cookies = cookie_manager.load_cookies()
    if cookies:
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        print(f"✓ {len(cookies)} cookies chargés")
    else:
        print("⚠️  Aucun cookie trouvé")
    
    # Rafraîchir pour appliquer les cookies
    driver.refresh()
    time.sleep(3)
    
    # Vérifier la connexion
    print("\n3. Vérification de la connexion...")
    current_url = driver.current_url
    print(f"   URL actuelle: {current_url}")
    print(f"   Titre: {driver.title}")
    
    # Aller sur la page d'upload
    print("\n4. Accès à la page d'upload...")
    driver.get('https://www.tiktok.com/upload')
    time.sleep(5)
    
    print(f"   URL après redirection: {driver.current_url}")
    print(f"   Titre: {driver.title}")
    
    # Vérifier si on est bien sur la page d'upload
    if 'upload' not in driver.current_url.lower():
        print("❌ ERREUR: Redirection inattendue !")
        print("   → TikTok a probablement redirigé vers la page de login")
        print("   → Les cookies sont peut-être invalides ou expirés")
        
        # Sauvegarder un screenshot
        screenshot_path = "/tmp/tiktok_upload_redirect.png"
        driver.save_screenshot(screenshot_path)
        print(f"   → Screenshot sauvegardé: {screenshot_path}")
    else:
        print("✓ Page d'upload atteinte")
    
    # Rechercher l'input file
    print("\n5. Recherche de l'input file...")
    try:
        # Essayer plusieurs sélecteurs
        selectors = [
            "input[type='file']",
            "input[type='file'][accept*='video']",
            "input[name='upload']",
            "//input[@type='file']",
        ]
        
        found = False
        for i, selector in enumerate(selectors, 1):
            try:
                if selector.startswith('//'):
                    file_input = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    file_input = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                
                print(f"✓ Input file trouvé avec sélecteur #{i}: {selector}")
                print(f"   → visible: {file_input.is_displayed()}")
                print(f"   → enabled: {file_input.is_enabled()}")
                found = True
                break
            except TimeoutException:
                print(f"   Sélecteur #{i} échoué: {selector}")
        
        if not found:
            print("❌ ERREUR: Aucun input file trouvé !")
            
            # Afficher tous les inputs
            print("\n   Tous les <input> trouvés:")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs[:10]:  # Limiter à 10
                input_type = inp.get_attribute('type') or 'N/A'
                input_name = inp.get_attribute('name') or 'N/A'
                input_id = inp.get_attribute('id') or 'N/A'
                print(f"      - type={input_type}, name={input_name}, id={input_id}")
            
            # Screenshot
            screenshot_path = "/tmp/tiktok_upload_no_input.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n   → Screenshot sauvegardé: {screenshot_path}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n6. Attente de 10 secondes pour observation...")
    print("   (Le navigateur reste ouvert, vous pouvez inspecter la page)")
    time.sleep(10)
    
    print("\n✓ Test terminé")
    
except Exception as e:
    print(f"\n❌ ERREUR CRITIQUE: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\nFermeture du navigateur...")
    driver.quit()
    print("✓ Terminé")

print("\n" + "=" * 80)
print("FIN DU TEST")
print("=" * 80)

