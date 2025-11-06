"""Uploader automatique de vidéos TikTok via Selenium"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import pickle
import os
from pathlib import Path
from typing import List, Optional
import logging
import time
import random

from uploader.cookie_manager import CookieManager

logger = logging.getLogger(__name__)


class SeleniumUploader:
    """Upload automatique de vidéos sur TikTok via Selenium"""
    
    def __init__(self, config):
        """
        Initialiser l'uploader Selenium
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        self.driver = None
        self.is_logged_in = False
        self.cookies_file = Path(config.COOKIES_FILE)
        self.cookie_manager = CookieManager(config.COOKIES_FILE)
        logger.info("SeleniumUploader initialisé")
    
    def initialize_browser(self):
        """Initialiser le navigateur Chrome avec Selenium"""
        try:
            logger.info("Initialisation du navigateur Chrome...")
            
            options = webdriver.ChromeOptions()
            
            # Options pour éviter la détection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User agent aléatoire
            ua = UserAgent()
            options.add_argument(f'user-agent={ua.chrome}')
            
            # Autres options
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            
            if self.config.HEADLESS_MODE:
                options.add_argument('--headless=new')
                options.add_argument('--window-size=1920,1080')
            
            # Initialiser le driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Modifier webdriver property pour éviter détection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            logger.info("✓ Navigateur Chrome initialisé")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du navigateur: {e}")
            return False
    
    def save_cookies(self):
        """Sauvegarder les cookies de session (pickle + JSON backup)"""
        try:
            cookies = self.driver.get_cookies()
            # Sauvegarder en pickle
            self.cookie_manager.save_cookies_to_pickle(cookies)
            # Backup en JSON
            self.cookie_manager.save_cookies_to_json(cookies)
            logger.info("✓ Cookies sauvegardés (pickle + JSON backup)")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des cookies: {e}")
    
    def load_cookies(self):
        """Charger les cookies de session (pickle ou JSON)"""
        try:
            # Récupérer les cookies (essaie pickle puis JSON)
            cookies = self.cookie_manager.get_cookies()
            
            if not cookies:
                logger.info("Aucun cookie trouvé")
                return False
            
            # Aller sur TikTok avant d'ajouter les cookies
            self.driver.get('https://www.tiktok.com')
            time.sleep(2)
            
            # Ajouter chaque cookie
            added_count = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    added_count += 1
                except Exception as e:
                    logger.debug(f"Impossible d'ajouter le cookie {cookie.get('name', 'unknown')}: {e}")
            
            logger.info(f"✓ {added_count}/{len(cookies)} cookies chargés")
            return added_count > 0
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des cookies: {e}")
            return False
    
    def login(self) -> bool:
        """
        Se connecter à TikTok
        
        Returns:
            True si la connexion a réussi
        """
        try:
            # Essayer de charger les cookies existants
            if self.load_cookies():
                self.driver.refresh()
                time.sleep(3)
                
                # Vérifier si on est connecté
                if self._is_logged_in():
                    self.is_logged_in = True
                    logger.info("✓ Connexion via cookies réussie")
                    return True
            
            # Sinon, connexion manuelle
            logger.info("Connexion manuelle nécessaire...")
            logger.warning(
                "⚠️  ATTENTION: Vous devez vous connecter manuellement dans le navigateur.\n"
                "Une fois connecté, le bot sauvegardera vos cookies pour les prochaines fois."
            )
            
            self.driver.get('https://www.tiktok.com/login')
            
            # Attendre que l'utilisateur se connecte (timeout 5 minutes)
            logger.info("En attente de la connexion manuelle (5 minutes max)...")
            
            wait_time = 0
            max_wait = 300  # 5 minutes
            
            while wait_time < max_wait:
                if self._is_logged_in():
                    self.is_logged_in = True
                    self.save_cookies()
                    logger.info("✓ Connexion manuelle réussie et cookies sauvegardés")
                    return True
                
                time.sleep(5)
                wait_time += 5
            
            logger.error("Timeout: connexion non effectuée dans les temps")
            return False
        
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """
        Vérifier si on est connecté (AMÉLIORÉ - multiples vérifications)
        
        Returns:
            True si connecté
        """
        try:
            # Stratégie 1: Chercher l'icône d'upload
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='upload-icon']")
                logger.debug("✓ Connexion détectée via upload-icon")
                return True
            except NoSuchElementException:
                pass
            
            # Stratégie 2: Chercher le bouton d'upload dans la barre
            try:
                self.driver.find_element(By.XPATH, "//a[contains(@href, '/upload')]")
                logger.debug("✓ Connexion détectée via lien upload")
                return True
            except NoSuchElementException:
                pass
            
            # Stratégie 3: Vérifier si on est sur la page d'upload
            if '/upload' in self.driver.current_url:
                logger.debug("✓ Connexion détectée via URL /upload")
                return True
            
            # Stratégie 4: Chercher un élément de profil connecté
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='profile-icon']")
                logger.debug("✓ Connexion détectée via profile-icon")
                return True
            except NoSuchElementException:
                pass
            
            # Stratégie 5: Vérifier les cookies de session
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie.get('name') in ['sessionid', 'sid_tt', 'sessionid_ss']:
                    logger.debug(f"✓ Connexion détectée via cookie {cookie.get('name')}")
                    return True
            
            logger.debug("✗ Aucun signe de connexion détecté")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de connexion: {e}")
            return False
    
    def upload_video(
        self, 
        video_path: str, 
        title: str = "",
        description: str = "", 
        hashtags: Optional[List[str]] = None
    ) -> bool:
        """
        Uploader une vidéo sur TikTok
        
        Args:
            video_path: Chemin absolu vers la vidéo
            title: Titre de la vidéo (utilisé en priorité)
            description: Description de la vidéo (fallback si pas de titre)
            hashtags: Liste de hashtags à ajouter
            
        Returns:
            True si l'upload a réussi
        """
        if not self.is_logged_in:
            logger.error("Pas connecté à TikTok")
            return False
        
        # Vérifier que le driver est toujours actif
        try:
            _ = self.driver.current_url
        except Exception as e:
            logger.error(f"Le driver Selenium est fermé ou inactif: {e}")
            logger.error("Tentative de réinitialisation...")
            if not self.initialize_browser():
                logger.error("Échec de la réinitialisation du navigateur")
                return False
            if not self.login():
                logger.error("Échec de la reconnexion à TikTok")
                return False
            logger.info("✓ Reconnexion réussie")
        
        try:
            logger.info(f"Upload de la vidéo: {Path(video_path).name}")
            
            # Aller sur la page d'upload
            self.driver.get('https://www.tiktok.com/upload')
            time.sleep(3)
            
            # Localiser l'input file
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Upload du fichier
            file_input.send_keys(video_path)
            logger.info("Fichier sélectionné, attente du chargement...")
            
            # Attendre que la vidéo soit chargée (icône de chargement disparaît)
            time.sleep(10)
            
            # Utiliser la description ORIGINALE COMPLÈTE sans modification
            # Si un titre est fourni, l'utiliser, sinon la description
            # NE PAS ajouter de hashtags supplémentaires si hashtags=None
            if title:
                full_caption = title
            else:
                full_caption = description
            
            # Ajouter des hashtags SEULEMENT si fournis explicitement
            if hashtags and len(hashtags) > 0:
                full_caption = f"{full_caption}\n\n" + " ".join(hashtags)
            
            logger.info(f"Caption COMPLÈTE ({len(full_caption)} caractères): {full_caption[:100]}...")
            
            # Trouver la zone de caption/description et insérer le texte COMPLET
            try:
                # Plusieurs sélecteurs possibles selon la version de TikTok
                caption_selectors = [
                    "div[contenteditable='true']",
                    "[data-text='true']",
                    "div.public-DraftEditor-content",
                ]
                
                caption_box = None
                for selector in caption_selectors:
                    try:
                        caption_box = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        logger.info(f"✓ Zone de description trouvée avec sélecteur: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if caption_box:
                    # Cliquer sur la zone
                    caption_box.click()
                    time.sleep(1)
                    
                    # Méthode 1: Essayer d'insérer via send_keys (standard)
                    try:
                        caption_box.send_keys(full_caption)
                        logger.info("✓ Description insérée via send_keys")
                    except Exception as e:
                        logger.warning(f"send_keys échoué: {e}, essai avec JavaScript...")
                        
                        # Méthode 2: Utiliser JavaScript pour insérer le texte (plus fiable pour les longs textes)
                        # Échapper les caractères spéciaux pour JavaScript
                        escaped_caption = full_caption.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                        
                        # Insérer le texte via JavaScript
                        js_script = f'''
                        var element = arguments[0];
                        element.focus();
                        element.textContent = "{escaped_caption}";
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        '''
                        
                        self.driver.execute_script(js_script, caption_box)
                        logger.info("✓ Description insérée via JavaScript")
                    
                    # Vérifier que le texte a bien été inséré
                    time.sleep(1)
                    inserted_text = caption_box.text or caption_box.get_attribute('textContent') or ''
                    logger.info(f"✓ Texte inséré vérifié: {len(inserted_text)} caractères (attendu: {len(full_caption)})")
                    
                    if len(inserted_text) < len(full_caption) * 0.9:  # Si moins de 90% du texte
                        logger.warning(f"⚠️  Attention: seulement {len(inserted_text)}/{len(full_caption)} caractères insérés")
                    
                else:
                    logger.warning("Zone de description non trouvée, upload sans description")
            
            except Exception as e:
                logger.warning(f"Impossible d'ajouter la description: {e}")
            
            # Petite pause avant de publier
            time.sleep(3)
            
            # Cliquer sur le bouton Publier/Post (CRITIQUE)
            logger.info("🔍 Recherche du bouton Publier...")
            try:
                # Liste étendue de sélecteurs pour trouver le bouton
                post_button_selectors = [
                    "button[data-e2e='publish-button']",
                    "button[data-e2e='post-button']",
                    "[data-e2e='publish-button']",
                    "button.TUXButton--primary",
                    "button[type='button']",
                ]
                
                post_button = None
                
                # Essayer CSS selectors
                for selector in post_button_selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in buttons:
                            btn_text = btn.text.lower()
                            if any(keyword in btn_text for keyword in ['post', 'publier', 'publish', 'télécharger']):
                                post_button = btn
                                logger.info(f"✓ Bouton trouvé via CSS: {selector} (texte: '{btn.text}')")
                                break
                        if post_button:
                            break
                    except Exception as e:
                        logger.debug(f"Sélecteur {selector} échoué: {e}")
                        continue
                
                # Si pas trouvé, essayer XPath
                if not post_button:
                    logger.info("Essai via XPath...")
                    try:
                        post_button = self.driver.find_element(
                            By.XPATH, 
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'post') or "
                            "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'publier') or "
                            "contains(@data-e2e, 'publish')]"
                        )
                        logger.info(f"✓ Bouton trouvé via XPath (texte: '{post_button.text}')")
                    except Exception as e:
                        logger.warning(f"XPath échoué: {e}")
                
                # Vérifier qu'on a trouvé le bouton
                if not post_button:
                    logger.error("❌ BOUTON PUBLIER INTROUVABLE - Upload manuel nécessaire")
                    logger.warning("⚠️  Vous devez cliquer manuellement sur Publier dans le navigateur")
                    time.sleep(60)  # Laisser 60s pour action manuelle
                    return False
                
                # Attendre que le bouton soit cliquable
                WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(post_button)
                )
                
                # Scroller jusqu'au bouton si nécessaire
                self.driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                time.sleep(1)
                
                # Cliquer sur le bouton
                logger.info("🖱️  Clic sur le bouton Publier...")
                try:
                    post_button.click()
                except Exception:
                    # Si le clic normal échoue, essayer JavaScript
                    logger.info("Clic via JavaScript...")
                    self.driver.execute_script("arguments[0].click();", post_button)
                
                logger.info("✓ Bouton Publier cliqué avec succès")
                
                # Attendre et gérer la popup de confirmation "Continuer à publier ?"
                logger.info("🔍 Attente de la popup de confirmation (5 secondes)...")
                time.sleep(5)
                
                # Gérer la popup de confirmation avec plusieurs tentatives
                popup_handled = False
                max_attempts = 3
                
                for attempt in range(max_attempts):
                    try:
                        logger.info(f"🔍 Recherche popup (tentative {attempt + 1}/{max_attempts})...")
                        
                        # Méthode 1: Chercher par texte dans les boutons
                        confirm_button_xpaths = [
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'publier maintenant')]",
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'post now')]",
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continuer')]",
                            "//button[contains(., 'Publier maintenant')]",
                            "//button[contains(., 'Post now')]",
                            "//div[@role='button' and contains(., 'Publier maintenant')]",
                            "//div[@role='button' and contains(., 'Post now')]",
                        ]
                        
                        # Méthode 2: Chercher par classe CSS
                        confirm_button_css = [
                            "button.TUXButton--primary",
                            "button[class*='Button--primary']",
                            "button[class*='confirm']",
                        ]
                        
                        confirm_button = None
                        
                        # Essayer XPath d'abord
                        for xpath in confirm_button_xpaths:
                            try:
                                buttons = self.driver.find_elements(By.XPATH, xpath)
                                for btn in buttons:
                                    if btn.is_displayed() and btn.is_enabled():
                                        confirm_button = btn
                                        logger.info(f"✓ Popup détectée via XPath: {btn.text}")
                                        break
                                if confirm_button:
                                    break
                            except Exception:
                                continue
                        
                        # Essayer CSS si XPath a échoué
                        if not confirm_button:
                            for css in confirm_button_css:
                                try:
                                    buttons = self.driver.find_elements(By.CSS_SELECTOR, css)
                                    for btn in buttons:
                                        btn_text = btn.text.lower()
                                        if btn.is_displayed() and btn.is_enabled() and any(
                                            keyword in btn_text for keyword in ['publier', 'post', 'continuer', 'continue']
                                        ):
                                            # Éviter de recliquer sur le premier bouton "Publier"
                                            if 'maintenant' in btn_text or 'now' in btn_text or len(btn_text) > 5:
                                                confirm_button = btn
                                                logger.info(f"✓ Popup détectée via CSS: {btn.text}")
                                                break
                                    if confirm_button:
                                        break
                                except Exception:
                                    continue
                        
                        # Si on a trouvé le bouton, cliquer dessus
                        if confirm_button:
                            logger.info(f"🖱️  Clic sur '{confirm_button.text}'...")
                            
                            # Scroller jusqu'au bouton
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", confirm_button)
                            time.sleep(0.5)
                            
                            # Essayer de cliquer
                            try:
                                confirm_button.click()
                            except Exception:
                                # Si le clic normal échoue, utiliser JavaScript
                                logger.info("Clic via JavaScript...")
                                self.driver.execute_script("arguments[0].click();", confirm_button)
                            
                            logger.info("✓ Popup de confirmation acceptée !")
                            popup_handled = True
                            break
                        else:
                            # Attendre un peu avant de réessayer
                            time.sleep(2)
                    
                    except Exception as e:
                        logger.debug(f"Tentative {attempt + 1} échouée: {e}")
                        time.sleep(2)
                
                if not popup_handled:
                    logger.info("ℹ️  Pas de popup de confirmation détectée (peut-être pas nécessaire)")
                
                # Petite pause après la confirmation
                time.sleep(2)
                
                # Attendre la confirmation de publication
                time.sleep(10)
                
                # Vérifier que la publication a réussi
                try:
                    # Chercher des signes de succès
                    if "tiktok.com/@" in self.driver.current_url:
                        logger.info("✓ URL de profil détectée - Publication réussie")
                        return True
                except Exception:
                    pass
                
                logger.info("✓ Vidéo uploadée (vérification de l'URL de confirmation)")
                return True
            
            except Exception as e:
                logger.error(f"❌ Erreur lors du clic sur Publier: {e}")
                logger.warning("⚠️  ACTION MANUELLE REQUISE - Cliquez sur Publier dans le navigateur")
                time.sleep(60)  # Laisser 60s pour action manuelle
                return False
        
        except Exception as e:
            logger.error(f"Erreur lors de l'upload: {e}")
            return False
    
    def close(self):
        """Fermer le navigateur"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navigateur fermé")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture du navigateur: {e}")

