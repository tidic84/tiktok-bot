"""Test spécifique pour la popup de confirmation d'upload"""
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_popup_detection():
    """Tester la détection de la popup sur la page d'upload TikTok"""
    
    print("=" * 60)
    print("TEST DE DÉTECTION DE POPUP")
    print("=" * 60)
    
    # Initialiser le navigateur
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        # Aller sur TikTok upload
        print("\n1️⃣ Ouverture de la page TikTok Studio...")
        driver.get('https://www.tiktok.com/tiktokstudio/upload')
        
        print("\n✋ INSTRUCTIONS:")
        print("1. Connectez-vous si nécessaire")
        print("2. Uploadez une vidéo de test")
        print("3. Remplissez la description")
        print("4. Cliquez sur 'Publier'")
        print("5. Attendez que la popup apparaisse")
        print("\nQuand la popup 'Continuer à publier ?' apparaît,")
        print("le script va essayer de la détecter automatiquement.\n")
        
        input("Appuyez sur Entrée quand la popup est visible...")
        
        print("\n2️⃣ Recherche de la popup...")
        
        # Liste de tous les XPath possibles
        xpaths = [
            "//button[contains(text(), 'Publier maintenant')]",
            "//button[contains(text(), 'Post now')]",
            "//button[contains(translate(text(), 'PUBLIER', 'publier'), 'publier maintenant')]",
            "//button[contains(., 'Publier maintenant')]",
            "//button[contains(., 'Post now')]",
            "//div[@role='button' and contains(., 'Publier')]",
        ]
        
        # Chercher tous les boutons visibles
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n📊 {len(all_buttons)} boutons trouvés sur la page\n")
        
        print("Boutons visibles avec du texte:")
        for i, btn in enumerate(all_buttons, 1):
            try:
                if btn.is_displayed():
                    text = btn.text.strip()
                    if text:
                        print(f"  {i}. '{text}' (enabled: {btn.is_enabled()})")
                        
                        # Vérifier si c'est le bon bouton
                        text_lower = text.lower()
                        if any(keyword in text_lower for keyword in ['publier', 'post', 'continuer', 'continue']):
                            if 'maintenant' in text_lower or 'now' in text_lower:
                                print(f"     ✅ CECI RESSEMBLE AU BOUTON DE POPUP !")
            except:
                pass
        
        print("\n3️⃣ Test des XPath...")
        for xpath in xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"\n✅ XPath trouvé: {xpath}")
                    for elem in elements:
                        if elem.is_displayed():
                            print(f"   Texte: '{elem.text}'")
                            print(f"   Visible: {elem.is_displayed()}")
                            print(f"   Activé: {elem.is_enabled()}")
                else:
                    print(f"❌ Rien trouvé: {xpath}")
            except Exception as e:
                print(f"❌ Erreur avec {xpath}: {e}")
        
        print("\n4️⃣ Test des classes CSS...")
        css_selectors = [
            "button[class*='Button--primary']",
            "button[class*='TUXButton']",
            "button[class*='confirm']",
        ]
        
        for css in css_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, css)
                if elements:
                    print(f"\n✅ CSS trouvé: {css} ({len(elements)} éléments)")
                    for elem in elements:
                        if elem.is_displayed():
                            print(f"   Texte: '{elem.text}'")
            except Exception as e:
                print(f"❌ Erreur avec {css}: {e}")
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC TERMINÉ")
        print("=" * 60)
        
        input("\nAppuyez sur Entrée pour fermer...")
        
    finally:
        driver.quit()
        print("Navigateur fermé")

if __name__ == "__main__":
    test_popup_detection()

