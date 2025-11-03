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
        """Sauvegarder les cookies de session"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info("Cookies sauvegardés")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des cookies: {e}")
    
    def load_cookies(self):
        """Charger les cookies de session"""
        try:
            if self.cookies_file.exists():
                self.driver.get('https://www.tiktok.com')
                time.sleep(2)
                
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                
                logger.info("Cookies chargés")
                return True
            return False
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
        Vérifier si on est connecté
        
        Returns:
            True si connecté
        """
        try:
            # Chercher un élément qui n'existe que quand on est connecté
            self.driver.find_element(By.CSS_SELECTOR, "[data-e2e='upload-icon']")
            return True
        except NoSuchElementException:
            return False
    
    def upload_video(
        self, 
        video_path: str, 
        description: str = "", 
        hashtags: Optional[List[str]] = None
    ) -> bool:
        """
        Uploader une vidéo sur TikTok
        
        Args:
            video_path: Chemin absolu vers la vidéo
            description: Description de la vidéo
            hashtags: Liste de hashtags à ajouter
            
        Returns:
            True si l'upload a réussi
        """
        if not self.is_logged_in:
            logger.error("Pas connecté à TikTok")
            return False
        
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
            
            # Préparer la caption
            if hashtags:
                full_caption = f"{description}\n\n" + " ".join(hashtags)
            else:
                full_caption = description
            
            # Trouver la zone de caption/description
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
                        break
                    except TimeoutException:
                        continue
                
                if caption_box:
                    caption_box.click()
                    time.sleep(1)
                    caption_box.send_keys(full_caption)
                    logger.info("Description ajoutée")
                else:
                    logger.warning("Zone de description non trouvée, upload sans description")
            
            except Exception as e:
                logger.warning(f"Impossible d'ajouter la description: {e}")
            
            # Petite pause avant de publier
            time.sleep(3)
            
            # Cliquer sur le bouton Publier/Post
            try:
                post_button_selectors = [
                    "button[data-e2e='publish-button']",
                    "button:contains('Post')",
                    "button:contains('Publier')",
                    "div[role='button']:contains('Post')",
                ]
                
                post_button = None
                for selector in post_button_selectors:
                    try:
                        post_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not post_button:
                    # Essayer de trouver par XPath
                    post_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((
                            By.XPATH, 
                            "//button[contains(text(), 'Post') or contains(text(), 'Publier')]"
                        ))
                    )
                
                post_button.click()
                logger.info("Bouton Publier cliqué")
                
                # Attendre la confirmation de publication
                time.sleep(10)
                
                logger.info("✓ Vidéo uploadée avec succès")
                return True
            
            except Exception as e:
                logger.error(f"Impossible de cliquer sur Publier: {e}")
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

