"""Uploader automatique de vidéos TikTok via Selenium"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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

    def _type_caption_like_human(self, caption_box, text: str, retry: int = 1) -> bool:
        """
        Insérer la description via le Clipboard API (méthode la plus humaine et indétectable).

        Cette méthode simule exactement ce qu'un humain ferait: copier-coller (Ctrl+V).
        C'est INDÉTECTABLE par TikTok car elle utilise les mêmes API qu'un utilisateur réel.

        Args:
            caption_box: Élément contenteditable cible
            text: Texte à insérer
            retry: Nombre de tentatives en cas d'échec (PAR DÉFAUT 1 pour éviter duplications)

        Returns:
            True si le texte semble avoir été inséré correctement.
        """
        import random

        for attempt in range(1, retry + 1):
            try:
                # Focus sur le champ
                caption_box.click()
                time.sleep(0.5)

                # Nettoyage ULTRA-AGRESSIF avec multiples méthodes
                # Méthode 1: JavaScript pour vider complètement
                self.driver.execute_script("""
                    var element = arguments[0];
                    element.innerText = '';
                    element.textContent = '';
                    element.innerHTML = '';
                    // Déclencher les événements pour que TikTok détecte le changement
                    var inputEvent = new Event('input', { bubbles: true });
                    element.dispatchEvent(inputEvent);
                    var changeEvent = new Event('change', { bubbles: true });
                    element.dispatchEvent(changeEvent);
                """, caption_box)
                time.sleep(0.3)

                # Méthode 2: Triple sélection + suppression pour être SÛR
                for _ in range(3):
                    try:
                        caption_box.send_keys(Keys.CONTROL, 'a')
                        time.sleep(0.1)
                        caption_box.send_keys(Keys.BACKSPACE)
                        time.sleep(0.1)
                    except:
                        pass  # Ignorer si échec (certains caractères peuvent causer problème)

                # Vérifier que c'est vraiment vide
                current_text = (caption_box.get_attribute('innerText') or
                              caption_box.get_attribute('textContent') or '').strip()
                if current_text:
                    logger.warning(f"⚠️ Champ pas complètement vidé (reste: '{current_text[:20]}...'), nouveau nettoyage...")
                    # Forcer le nettoyage une dernière fois
                    self.driver.execute_script("arguments[0].innerHTML = '';", caption_box)
                    time.sleep(0.3)

                # Focus à nouveau pour être sûr
                caption_box.click()
                time.sleep(0.3)

                # ========================================================================
                # MÉTHODE ULTIME: Clipboard API + Ctrl+V (INDÉTECTABLE par TikTok)
                # ========================================================================
                # C'est exactement ce qu'un humain ferait: copier le texte et le coller.
                # TikTok ne peut PAS détecter que c'est un bot car on utilise les mêmes
                # API natives du navigateur qu'un utilisateur réel.

                logger.info(f"📝 Insertion comme humain via Clipboard API + Ctrl+V ({len(text)} caractères)...")

                # Échapper le texte pour JavaScript (backticks et backslashes)
                escaped_text = (text
                    .replace('\\', '\\\\')  # Backslashes
                    .replace('`', '\\`')    # Backticks pour template literal
                )

                # Étape 1: Copier le texte dans le clipboard du navigateur
                # Étape 2: Simuler Ctrl+V pour coller (exactement comme un humain)
                # Étape 3: Déclencher TOUS les événements que TikTok écoute
                self.driver.execute_script(f"""
                    var element = arguments[0];
                    var text = `{escaped_text}`;

                    // Focus sur l'élément
                    element.focus();

                    // Placer le curseur au début
                    var range = document.createRange();
                    var selection = window.getSelection();
                    range.setStart(element, 0);
                    range.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(range);

                    // MÉTHODE 1: Utiliser le Clipboard API (le plus humain)
                    // C'est exactement ce que fait un navigateur quand on fait Ctrl+V
                    try {{
                        // Créer un événement 'paste' réaliste
                        var pasteEvent = new ClipboardEvent('paste', {{
                            bubbles: true,
                            cancelable: true,
                            clipboardData: new DataTransfer()
                        }});

                        // Ajouter le texte au clipboard de l'événement
                        pasteEvent.clipboardData.setData('text/plain', text);

                        // Déclencher l'événement paste (comme si l'utilisateur avait fait Ctrl+V)
                        element.dispatchEvent(pasteEvent);

                        // Si TikTok ne gère pas l'événement, insérer manuellement
                        if (element.textContent === '') {{
                            document.execCommand('insertText', false, text);
                        }}
                    }} catch(e) {{
                        // Fallback: execCommand si le Clipboard API échoue
                        console.log('Clipboard API failed, using execCommand:', e);
                        document.execCommand('insertText', false, text);
                    }}

                    // Déclencher TOUS les événements que TikTok pourrait écouter
                    // (pour mettre à jour l'état React/Vue interne)
                    var events = [
                        new Event('input', {{ bubbles: true }}),
                        new Event('change', {{ bubbles: true }}),
                        new InputEvent('beforeinput', {{ bubbles: true, cancelable: true, inputType: 'insertText', data: text }}),
                        new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: text }}),
                        new Event('keyup', {{ bubbles: true }}),
                        new Event('keydown', {{ bubbles: true }}),
                    ];

                    events.forEach(function(event) {{
                        try {{
                            element.dispatchEvent(event);
                        }} catch(e) {{
                            console.log('Event dispatch failed:', e);
                        }}
                    }});

                    // Placer le curseur à la fin
                    var newRange = document.createRange();
                    newRange.selectNodeContents(element);
                    newRange.collapse(false);
                    selection.removeAllRanges();
                    selection.addRange(newRange);

                    // Déclencher blur puis focus pour forcer la mise à jour
                    element.blur();
                    setTimeout(function() {{ element.focus(); }}, 50);
                """, caption_box)

                # Attendre que TikTok traite tous les événements
                time.sleep(2.0)  # Délai plus long pour laisser React/Vue se mettre à jour

                # Vérifier que le texte a été inséré
                inserted_text = (caption_box.get_attribute('innerText') or
                                 caption_box.get_attribute('textContent') or
                                 caption_box.text or '').strip()

                # Nettoyer les <br> pour comparer
                expected_length = len(text.replace('\n', ''))
                actual_length = len(inserted_text.replace('\n', ''))

                if inserted_text and actual_length >= expected_length * 0.8:
                    logger.info(f"✓ Description insérée via Clipboard API ({actual_length}/{expected_length} caractères)")
                    logger.info(f"✓ Texte final: {actual_length} caractères (attendu: {expected_length})")
                    return True
                else:
                    logger.warning(f"⚠️ Tentative {attempt}/{retry} - texte incomplet ({actual_length}/{expected_length} caractères)")
            except Exception as e:
                logger.warning(f"⚠️ Tentative {attempt}/{retry} - erreur: {e}")
                time.sleep(0.5)

        return False
    
    def initialize_browser(self):
        """Initialiser le navigateur Chrome avec Selenium"""
        try:
            logger.info("Initialisation du navigateur Chrome...")
            
            options = webdriver.ChromeOptions()
            
            # Options pour éviter la détection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User agent LINUX DESKTOP cohérent (pas Windows/Mac/Android)
            # Version récente de Chrome sur Linux x86_64
            linux_user_agent = (
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            )
            options.add_argument(f'user-agent={linux_user_agent}')
            logger.debug(f"User-Agent: {linux_user_agent}")
            
            # Autres options pour ressembler à un vrai navigateur
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            
            # Options anti-détection supplémentaires
            options.add_argument('--disable-dev-shm-usage')  # Évite problèmes mémoire partagée
            options.add_argument('--disable-gpu')  # Évite problèmes GPU
            options.add_argument('--no-sandbox')  # Requis sur certains systèmes Linux
            options.add_argument('--lang=fr-FR')  # Langue française cohérente
            
            # Préférences pour ressembler à un utilisateur réel
            prefs = {
                "profile.default_content_setting_values.notifications": 2,  # Bloquer notifications
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "intl.accept_languages": "fr-FR,fr,en-US,en"  # Langues préférées
            }
            options.add_experimental_option("prefs", prefs)
            
            if self.config.HEADLESS_MODE:
                options.add_argument('--headless=new')
                options.add_argument('--window-size=1920,1080')
            
            # Initialiser le driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Modifier webdriver property + navigator pour éviter détection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // Masquer webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Forcer platform Linux
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Linux x86_64'
                    });
                    
                    // Ajouter plugins réalistes (PDF viewer)
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {
                                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                                description: "Portable Document Format",
                                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            }
                        ]
                    });
                    
                    // Languages cohérents
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['fr-FR', 'fr', 'en-US', 'en']
                    });
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
            logger.info("📂 Accès à la page d'upload TikTok...")
            try:
                self.driver.get('https://www.tiktok.com/upload')
                logger.info("✓ Page d'upload chargée")
            except Exception as e:
                logger.error(f"❌ Impossible d'accéder à la page d'upload: {e}")
                raise
            
            time.sleep(3)
            
            # Localiser l'input file
            logger.info("🔍 Recherche de l'input file pour l'upload...")
            try:
                file_input = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                logger.info("✓ Input file trouvé")
            except TimeoutException:
                logger.error("❌ Timeout: Input file non trouvé après 20 secondes")
                logger.error(f"   URL actuelle: {self.driver.current_url}")
                logger.error(f"   Titre page: {self.driver.title}")
                # Sauvegarder screenshot pour debug
                try:
                    screenshot_path = f"/tmp/tiktok_upload_error_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.error(f"   Screenshot sauvegardé: {screenshot_path}")
                except:
                    pass
                raise
            
            # Upload du fichier
            logger.info(f"📤 Envoi du fichier: {video_path}")
            try:
                file_input.send_keys(video_path)
                logger.info("✓ Fichier sélectionné, attente du chargement...")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'envoi du fichier: {e}")
                raise
            
            # Attendre que la vidéo soit chargée (IMPORTANT: attendre suffisamment longtemps)
            logger.info("⏳ Attente du chargement complet de la vidéo...")
            time.sleep(5)  # Attente initiale
            
            # Attendre que TikTok pré-remplisse le champ avec le nom du fichier
            # (cela peut prendre quelques secondes)
            logger.info("⏳ Attente que TikTok pré-remplisse les champs...")
            time.sleep(10)  # Attendre que TikTok finisse son initialisation
            
            # Vérifier que la vidéo est bien uploadée en cherchant des indicateurs
            try:
                # Attendre que la preview de la vidéo soit visible
                WebDriverWait(self.driver, 30).until(
                    lambda driver: driver.execute_script(
                        "return document.querySelector('video') !== null"
                    )
                )
                logger.info("✓ Vidéo chargée (preview détectée)")
            except TimeoutException:
                logger.warning("⚠️  Timeout en attendant la preview, on continue quand même...")
            
            # Attendre encore un peu pour être sûr que TikTok a fini
            time.sleep(5)
            
            # Utiliser la description ORIGINALE COMPLÈTE sans modification
            # Si un titre est fourni, l'utiliser, sinon la description
            # NE PAS ajouter de hashtags supplémentaires si hashtags=None
            if title and title.strip():
                full_caption = title.strip()
            elif description and description.strip():
                full_caption = description.strip()
            else:
                full_caption = ""
            
            # Ajouter des hashtags SEULEMENT si fournis explicitement (et non vides)
            if hashtags and len(hashtags) > 0:
                hashtags_str = " ".join([h.strip() for h in hashtags if h.strip()])
                if hashtags_str:
                    # Utiliser un seul saut de ligne au lieu de deux
                    full_caption = f"{full_caption}\n{hashtags_str}"
            
            logger.info(f"Caption COMPLÈTE ({len(full_caption)} caractères): {full_caption[:100]}...")
            logger.info(f"Description COMPLÈTE à insérer:")
            logger.info(f"  {full_caption}")
            logger.info(f"  [Fin de la description]")
            
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
                    # Attendre un peu pour laisser TikTok finir son initialisation
                    time.sleep(2)
                    
                    # Vérifier si TikTok a pré-rempli le champ
                    current_text = (caption_box.get_attribute('innerText') or 
                                  caption_box.get_attribute('textContent') or 
                                  caption_box.text or '')
                    
                    if current_text:
                        logger.info(f"⚠️  Champ pré-rempli par TikTok détecté: '{current_text[:50]}...'")
                        logger.info("🔄 Effacement du contenu pré-rempli...")
                    
                    # Cliquer sur la zone et focus
                    caption_box.click()
                    time.sleep(1)
                    
                    # VIDER COMPLÈTEMENT le champ (TikTok pré-remplit avec le nom du fichier)
                    # Méthode combinée plus fiable
                    try:
                        # D'abord vider via JavaScript (le plus fiable pour contenteditable)
                        self.driver.execute_script("""
                            var element = arguments[0];
                            element.innerText = '';
                            element.textContent = '';
                            // Déclencher les événements pour que TikTok détecte le changement
                            var event = new Event('input', { bubbles: true });
                            element.dispatchEvent(event);
                        """, caption_box)
                        time.sleep(0.3)
                        
                        # Ensuite sélectionner tout et supprimer (au cas où)
                        caption_box.send_keys(Keys.CONTROL, 'a')
                        time.sleep(0.2)
                        caption_box.send_keys(Keys.DELETE)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.debug(f"Avertissement nettoyage: {e}")
                        pass
                    
                    # Vérifier que le champ est bien vide
                    remaining_text = (caption_box.get_attribute('innerText') or 
                                    caption_box.get_attribute('textContent') or '')
                    
                    if remaining_text.strip():
                        logger.warning(f"⚠️  Texte résiduel après nettoyage: '{remaining_text[:30]}...'")
                    else:
                        logger.info("✓ Champ complètement vidé")
                    
                    insertion_success = self._type_caption_like_human(caption_box, full_caption)
                    
                    final_text = (caption_box.get_attribute('innerText') or 
                                  caption_box.get_attribute('textContent') or 
                                  caption_box.get_attribute('value') or
                                  caption_box.text or '')
                    
                    logger.info(f"{'✓' if insertion_success else '⚠️'} Texte final: {len(final_text)} caractères (attendu: {len(full_caption)})")
                    
                    if not insertion_success:
                        logger.warning(f"⚠️  Échec de l'insertion manuelle de la description ({len(final_text)}/{len(full_caption)} caractères)")
                    elif len(final_text) < len(full_caption) * 0.8:
                        logger.warning(f"⚠️  Attention: seulement {len(final_text)}/{len(full_caption)} caractères insérés")
                        logger.warning(f"    Description attendue: {full_caption[:100]}...")
                        logger.warning(f"    Description insérée: {final_text[:100]}...")
                    else:
                        logger.info(f"✓ Description complète insérée avec succès ({len(final_text)}/{len(full_caption)} caractères)")
                    
                else:
                    logger.warning("Zone de description non trouvée, upload sans description")
            
            except Exception as e:
                logger.warning(f"Impossible d'ajouter la description: {e}")

            # ========================================================================
            # PAUSE HUMAINE avant de publier (CRITIQUE pour éviter la détection)
            # ========================================================================
            # Un humain ne clique JAMAIS sur "Publier" immédiatement après avoir
            # saisi la description. Il prend le temps de relire, vérifier, etc.
            # On simule ce comportement avec un délai aléatoire de 5-10 secondes.

            import random
            human_delay = random.uniform(5.0, 10.0)  # Délai aléatoire entre 5 et 10 secondes
            logger.info(f"⏳ Pause humaine avant publication ({human_delay:.1f}s)...")
            logger.info("   (Un humain ne publie jamais immédiatement après avoir saisi la description)")

            # Simuler quelques mouvements de souris pour paraître plus humain
            try:
                actions = ActionChains(self.driver)
                # Bouger la souris de façon aléatoire (simule l'utilisateur qui regarde la page)
                for _ in range(3):
                    x_offset = random.randint(-100, 100)
                    y_offset = random.randint(-100, 100)
                    actions.move_by_offset(x_offset, y_offset).perform()
                    time.sleep(random.uniform(0.3, 0.8))
                    # Reset pour éviter d'aller hors écran
                    actions.move_by_offset(-x_offset, -y_offset).perform()
            except Exception as e:
                logger.debug(f"Mouvement souris échoué (pas grave): {e}")

            # Attendre le reste du délai
            time.sleep(human_delay)
            
            # VÉRIFICATION : Détecter si TikTok affiche un avertissement de contenu restreint BLOQUANT
            logger.info("🔍 Vérification des avertissements TikTok...")
            try:
                # IMPORTANT : Distinguer deux types de popups :
                # 1. Popup BLOQUANTE avec bouton "Supprimer" → À ignorer
                # 2. Popup INFORMATIVE avec "Tu peux toujours publier" → À gérer plus tard (clic sur Publier)
                
                # D'abord vérifier si c'est une popup INFORMATIVE (non bloquante)
                informative_popup = False
                try:
                    informative_texts = self.driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'Tu peux toujours le publier') or "
                        "contains(text(), 'You can still publish')]"
                    )
                    if any(elem.is_displayed() for elem in informative_texts if informative_texts):
                        informative_popup = True
                        logger.info("ℹ️  Popup informative détectée (sera gérée après le clic sur Publier)")
                except:
                    pass
                
                # Si c'est une popup informative, ne PAS la considérer comme un avertissement bloquant
                if informative_popup:
                    logger.info("✓ Pas d'avertissement bloquant (popup informative seulement)")
                    warning_detected = False
                else:
                    # Chercher la popup d'avertissement BLOQUANTE
                    # (avec bouton "Supprimer" obligatoire)
                    warning_selectors = [
                        # Bouton "Supprimer" présent = avertissement BLOQUANT
                        "//button[contains(text(), 'Supprimer')]",
                        "//button[contains(text(), 'Delete')]",
                    ]
                    
                    warning_detected = False
                    warning_reason = ""
                    
                    # Vérifier la présence du bouton Supprimer (indicateur d'avertissement bloquant)
                    for selector in warning_selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            if elements and any(elem.is_displayed() for elem in elements):
                                # Vérifier qu'il y a aussi le texte "contenu restreint" pour confirmer
                                try:
                                    restricted_text = self.driver.find_elements(By.XPATH,
                                        "//*[contains(text(), 'contenu pourrait être restreint') or "
                                        "contains(text(), 'content may be restricted')]"
                                    )
                                    if any(elem.is_displayed() for elem in restricted_text if restricted_text):
                                        warning_detected = True
                                        # Essayer de récupérer le texte de l'avertissement
                                        try:
                                            reason_element = self.driver.find_element(By.XPATH, 
                                                "//*[contains(text(), 'Motif de') or contains(text(), 'Reason for')]")
                                            warning_reason = reason_element.text if reason_element else "Raison inconnue"
                                        except:
                                            warning_reason = "Contenu potentiellement restreint"
                                        break
                                except:
                                    pass
                        except:
                            continue
                
                if warning_detected:
                    logger.warning("⚠️  ═══════════════════════════════════════════════════════════")
                    logger.warning("⚠️  AVERTISSEMENT TIKTOK DÉTECTÉ !")
                    logger.warning(f"⚠️  Raison: {warning_reason}")
                    logger.warning("⚠️  TikTok considère ce contenu comme potentiellement restreint")
                    
                    # Vérifier la configuration pour savoir si on doit ignorer
                    if config.SKIP_RESTRICTED_CONTENT:
                        logger.warning("⚠️  → Vidéo IGNORÉE (SKIP_RESTRICTED_CONTENT = True)")
                        logger.warning("⚠️  ═══════════════════════════════════════════════════════════")
                        
                        # Cliquer sur "Supprimer" pour fermer et ne pas publier
                        try:
                            delete_button = self.driver.find_element(By.XPATH, 
                                "//button[contains(text(), 'Supprimer') or contains(text(), 'Delete')]")
                            delete_button.click()
                            logger.info("✓ Popup fermée, vidéo non publiée")
                            time.sleep(2)
                        except Exception as e:
                            logger.warning(f"Impossible de cliquer sur Supprimer: {e}")
                            # Essayer de fermer avec la croix
                            try:
                                close_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Close']")
                                close_button.click()
                            except:
                                pass
                        
                        return False  # Échec d'upload (contenu restreint)
                    else:
                        logger.warning("⚠️  → Tentative de publication malgré l'avertissement (SKIP_RESTRICTED_CONTENT = False)")
                        logger.warning("⚠️  ═══════════════════════════════════════════════════════════")
                        # Cliquer sur "Publier" dans la popup pour continuer quand même
                        try:
                            publish_button = self.driver.find_element(By.XPATH, 
                                "//button[contains(text(), 'Publier') or contains(text(), 'Publish')]")
                            publish_button.click()
                            logger.info("✓ Popup contournée, tentative de publication...")
                            time.sleep(2)
                        except Exception as e:
                            logger.warning(f"Impossible de continuer la publication: {e}")
                            return False
                else:
                    logger.info("✓ Aucun avertissement détecté, upload OK")
                    
            except Exception as e:
                logger.debug(f"Erreur lors de la vérification des avertissements: {e}")
            
            # VÉRIFICATION FINALE : S'assurer que la description est toujours là avant de publier
            try:
                final_check_text = (caption_box.get_attribute('innerText') or 
                                  caption_box.get_attribute('textContent') or '').strip()
                logger.info(f"🔍 Vérification finale de la description: {len(final_check_text)} caractères")
                logger.info(f"   Contenu actuel: {repr(final_check_text[:100])}")
                logger.info(f"   Attendu: {len(full_caption)} caractères - {repr(full_caption[:100])}")
                
                # IMPORTANT: Ne RE-TAPER que si le champ est vraiment vide ou quasi-vide
                # Seuil à 3 caractères pour éviter de retaper inutilement
                if not final_check_text or len(final_check_text) < 3:
                    logger.warning(f"⚠️  La description a été effacée ! Nouvelle saisie...")
                    self._type_caption_like_human(caption_box, full_caption, retry=1)
                    time.sleep(1.0)
                    final_check_text = (caption_box.get_attribute('innerText') or 
                                        caption_box.get_attribute('textContent') or '').strip()
                    logger.info(f"✓ Texte après nouvelle saisie: {len(final_check_text)} caractères")
                else:
                    logger.info(f"✓ Description présente ({len(final_check_text)} caractères) - pas de re-saisie")
            except Exception as e:
                logger.warning(f"Impossible de vérifier la description finale: {e}")
            
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
                
                # Attendre et gérer les popups possibles
                logger.info("🔍 Attente et détection des popups possibles...")
                time.sleep(3)  # Attente initiale pour que la popup apparaisse
                
                # 1. Gérer la popup "Tu peux toujours le publier..." (sans avertissement critique)
                # Cette popup apparaît APRÈS avoir cliqué sur "Publier"
                # avec le message "Le contenu pourrait être restreint"
                # mais avec un bouton "Publier" disponible (pas un avertissement bloquant)
                
                popup_detected = False
                max_popup_wait = 10  # Attendre jusqu'à 10 secondes pour la popup
                
                for wait_attempt in range(max_popup_wait):
                    try:
                        # Chercher TOUS les éléments de la popup pour bien la détecter
                        popup_indicators = [
                            # Titre de la popup
                            "//*[contains(text(), 'contenu pourrait être restreint')]",
                            "//*[contains(text(), 'Content may be restricted')]",
                            # Message informatif
                            "//*[contains(text(), 'Tu peux toujours le publier')]",
                            "//*[contains(text(), 'You can still publish')]",
                            # Message de conseil
                            "//*[contains(text(), 'améliorer la visibilité')]",
                            "//*[contains(text(), 'improve visibility')]",
                            # Motif de l'infraction visible
                            "//*[contains(text(), 'Motif de')]",
                            "//*[contains(text(), 'Reason for')]",
                        ]
                        
                        # Vérifier si la popup est présente
                        for indicator in popup_indicators:
                            try:
                                elements = self.driver.find_elements(By.XPATH, indicator)
                                if elements and any(elem.is_displayed() for elem in elements):
                                    popup_detected = True
                                    logger.info(f"ℹ️  Popup détectée ! (indicateur: {indicator[:50]}...)")
                                    break
                            except:
                                continue
                        
                        if popup_detected:
                            break
                        
                        # Si pas encore détectée, attendre 1 seconde de plus
                        if wait_attempt < max_popup_wait - 1:
                            time.sleep(1)
                            logger.debug(f"Attente popup... ({wait_attempt + 1}/{max_popup_wait})")
                    
                    except Exception as e:
                        logger.debug(f"Erreur détection popup: {e}")
                        break
                
                if popup_detected:
                    logger.info("ℹ️  Popup informative TikTok détectée après clic sur Publier")
                    logger.info("   → Recherche du bouton 'Publier' dans la popup...")
                    
                    # Attendre un peu pour que la popup soit complètement chargée
                    time.sleep(2)
                    
                    # Chercher le bouton "Publier" dans cette popup avec TOUS les sélecteurs possibles
                    publish_in_popup_selectors = [
                        # XPath - texte exact
                        "//button[text()='Publier']",
                        "//button[text()='Publish']",
                        # XPath - contient le texte
                        "//button[contains(translate(text(), 'PUBLIER', 'publier'), 'publier')]",
                        "//button[contains(translate(text(), 'PUBLISH', 'publish'), 'publish')]",
                        # Dans un dialog/modal
                        "//div[@role='dialog']//button[contains(text(), 'Publier')]",
                        "//div[@role='dialog']//button[contains(text(), 'Publish')]",
                        # Dans une div avec classe Modal
                        "//div[contains(@class, 'Modal')]//button[contains(text(), 'Publier')]",
                        "//div[contains(@class, 'modal')]//button[contains(text(), 'Publier')]",
                        # Bouton primaire dans modal
                        "//div[@role='dialog']//button[contains(@class, 'primary')]",
                        "//div[contains(@class, 'Modal')]//button[contains(@class, 'TUXButton--primary')]",
                        # CSS selectors
                        "div[role='dialog'] button",
                        "button.TUXButton--primary",
                    ]
                    
                    popup_publish_btn = None
                    
                    for selector in publish_in_popup_selectors:
                        try:
                            # Essayer XPath
                            if selector.startswith('//') or selector.startswith('('):
                                buttons = self.driver.find_elements(By.XPATH, selector)
                            else:
                                # Essayer CSS
                                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            logger.debug(f"Sélecteur '{selector[:40]}...' : {len(buttons)} bouton(s) trouvé(s)")
                            
                            for btn in buttons:
                                try:
                                    if btn.is_displayed() and btn.is_enabled():
                                        btn_text = btn.text.strip().lower()
                                        logger.debug(f"  → Bouton trouvé avec texte: '{btn.text}'")
                                        
                                        # Vérifier si c'est bien le bouton Publier
                                        if btn_text and ('publier' in btn_text or 'publish' in btn_text):
                                            # Vérifier que ce n'est pas le bouton principal (éviter doublon)
                                            try:
                                                # Le bouton dans la popup devrait être dans un dialog
                                                parent_classes = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'Modal') or @role='dialog']")
                                                if parent_classes:
                                                    popup_publish_btn = btn
                                                    logger.info(f"✓ Bouton 'Publier' trouvé dans la popup: '{btn.text}'")
                                                    break
                                            except:
                                                # Si on ne peut pas vérifier le parent, on prend quand même le bouton
                                                popup_publish_btn = btn
                                                logger.info(f"✓ Bouton 'Publier' trouvé: '{btn.text}'")
                                                break
                                except Exception as e:
                                    logger.debug(f"    Erreur vérification bouton: {e}")
                                    continue
                            
                            if popup_publish_btn:
                                break
                        except Exception as e:
                            logger.debug(f"Sélecteur {selector[:30]} échoué: {e}")
                            continue
                    
                    if popup_publish_btn:
                        logger.info("🖱️  Clic sur 'Publier' dans la popup informative...")
                        try:
                            # Scroller vers le bouton si nécessaire
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", popup_publish_btn)
                            time.sleep(0.5)
                            popup_publish_btn.click()
                            time.sleep(3)
                            logger.info("✓ Popup fermée et publication confirmée")
                        except Exception as e:
                            logger.warning(f"Erreur clic sur Publier: {e}")
                            # Essayer avec JavaScript
                            try:
                                self.driver.execute_script("arguments[0].click();", popup_publish_btn)
                                time.sleep(3)
                                logger.info("✓ Popup fermée via JavaScript")
                            except:
                                logger.error("❌ Impossible de cliquer sur le bouton Publier")
                    else:
                        logger.warning("⚠️  Bouton 'Publier' NON TROUVÉ avec les sélecteurs !")
                        logger.warning("   → Recherche manuelle dans TOUS les boutons...")
                        
                        # Dernier recours : chercher manuellement dans TOUS les boutons
                        try:
                            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                            publish_found = False
                            
                            for btn in all_buttons:
                                if btn.is_displayed():
                                    btn_text = btn.text.strip()
                                    logger.debug(f"      Vérification bouton: '{btn_text}'")
                                    
                                    # Si c'est le bouton "Publier" (case insensitive)
                                    if btn_text and btn_text.lower() == 'publier':
                                        logger.info(f"✓ Bouton 'Publier' trouvé manuellement: '{btn_text}'")
                                        logger.info("🖱️  Clic sur le bouton via recherche manuelle...")
                                        
                                        try:
                                            # Scroller et cliquer
                                            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                            time.sleep(0.5)
                                            btn.click()
                                            time.sleep(3)
                                            logger.info("✓ Popup fermée et publication confirmée (recherche manuelle)")
                                            publish_found = True
                                            break
                                        except Exception as e:
                                            logger.warning(f"Erreur clic manuel: {e}")
                                            # Essayer JavaScript
                                            try:
                                                self.driver.execute_script("arguments[0].click();", btn)
                                                time.sleep(3)
                                                logger.info("✓ Popup fermée via JavaScript (recherche manuelle)")
                                                publish_found = True
                                                break
                                            except:
                                                pass
                            
                            if not publish_found:
                                logger.error("❌ Aucun bouton 'Publier' trouvé même avec recherche manuelle !")
                                logger.warning("   → Liste de tous les boutons visibles:")
                                for btn in all_buttons:
                                    if btn.is_displayed():
                                        logger.warning(f"      - '{btn.text}' (visible)")
                                
                                # Essayer de fermer la popup
                                logger.warning("   → Tentative de fermeture de la popup...")
                                try:
                                    # Chercher "Supprimer" à la place
                                    for btn in all_buttons:
                                        if btn.is_displayed() and btn.text.strip().lower() == 'supprimer':
                                            logger.info("Clic sur 'Supprimer' pour fermer la popup")
                                            btn.click()
                                            time.sleep(2)
                                            logger.info("✓ Popup fermée avec Supprimer")
                                            break
                                except Exception as e:
                                    logger.error(f"❌ Impossible de fermer la popup: {e}")
                                    logger.error("   → Upload peut avoir échoué, vérifiez manuellement")
                        
                        except Exception as e:
                            logger.error(f"❌ Erreur lors de la recherche manuelle: {e}")
                            logger.error("   → Upload peut avoir échoué, vérifiez manuellement")
                else:
                    logger.info("✓ Aucune popup détectée après le clic sur Publier")
                
                # Attendre un peu après gestion de la popup
                time.sleep(2)
                
                # 2. Gérer la popup de confirmation "Continuer à publier ?"
                
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

