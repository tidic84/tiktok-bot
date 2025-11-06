"""Gestionnaire de cookies pour TikTok - Support JSON et Pickle"""
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CookieManager:
    """Gestionnaire de cookies avec support JSON et Pickle"""
    
    def __init__(self, cookies_file: str):
        """
        Initialiser le gestionnaire de cookies
        
        Args:
            cookies_file: Chemin vers le fichier de cookies (pickle ou json)
        """
        self.cookies_file = Path(cookies_file)
        self.json_file = self.cookies_file.with_suffix('.json')
        logger.info(f"CookieManager initialisé (pickle: {self.cookies_file}, json: {self.json_file})")
    
    def load_cookies_from_json(self, json_file: Optional[str] = None) -> List[Dict]:
        """
        Charger les cookies depuis un fichier JSON
        
        Args:
            json_file: Chemin vers le fichier JSON (optionnel, utilise self.json_file par défaut)
            
        Returns:
            Liste de cookies au format Selenium
        """
        json_path = Path(json_file) if json_file else self.json_file
        
        try:
            if not json_path.exists():
                logger.warning(f"Fichier JSON non trouvé: {json_path}")
                return []
            
            with open(json_path, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            # Convertir le format JSON (Firefox/Chrome export) vers format Selenium
            selenium_cookies = []
            for cookie in cookies_data:
                selenium_cookie = self._convert_to_selenium_format(cookie)
                if selenium_cookie:
                    selenium_cookies.append(selenium_cookie)
            
            logger.info(f"✓ {len(selenium_cookies)} cookies chargés depuis {json_path}")
            return selenium_cookies
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur lors du chargement des cookies JSON: {e}")
            return []
    
    def _convert_to_selenium_format(self, cookie: Dict) -> Optional[Dict]:
        """
        Convertir un cookie du format JSON export vers format Selenium
        
        Args:
            cookie: Cookie au format JSON export
            
        Returns:
            Cookie au format Selenium ou None si invalide
        """
        try:
            # Format Selenium minimal requis
            selenium_cookie = {
                'name': cookie.get('name'),
                'value': cookie.get('value'),
                'domain': cookie.get('domain', ''),
            }
            
            # Champs optionnels
            if 'path' in cookie:
                selenium_cookie['path'] = cookie['path']
            if 'secure' in cookie:
                selenium_cookie['secure'] = cookie['secure']
            if 'httpOnly' in cookie:
                selenium_cookie['httpOnly'] = cookie['httpOnly']
            if 'sameSite' in cookie and cookie['sameSite']:
                # Selenium accepte: 'Strict', 'Lax', 'None'
                same_site = cookie['sameSite']
                if same_site == 'no_restriction':
                    selenium_cookie['sameSite'] = 'None'
                elif same_site in ['Strict', 'Lax', 'None']:
                    selenium_cookie['sameSite'] = same_site
            if 'expirationDate' in cookie and cookie['expirationDate']:
                # Convertir timestamp en entier
                selenium_cookie['expiry'] = int(cookie['expirationDate'])
            
            return selenium_cookie
            
        except Exception as e:
            logger.warning(f"Impossible de convertir le cookie {cookie.get('name', 'unknown')}: {e}")
            return None
    
    def save_cookies_to_pickle(self, cookies: List[Dict]) -> bool:
        """
        Sauvegarder les cookies au format Pickle
        
        Args:
            cookies: Liste de cookies au format Selenium
            
        Returns:
            True si succès
        """
        try:
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"✓ {len(cookies)} cookies sauvegardés dans {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des cookies pickle: {e}")
            return False
    
    def load_cookies_from_pickle(self) -> List[Dict]:
        """
        Charger les cookies depuis le fichier Pickle
        
        Returns:
            Liste de cookies au format Selenium
        """
        try:
            if not self.cookies_file.exists():
                logger.warning(f"Fichier pickle non trouvé: {self.cookies_file}")
                return []
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            logger.info(f"✓ {len(cookies)} cookies chargés depuis {self.cookies_file}")
            return cookies
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des cookies pickle: {e}")
            return []
    
    def save_cookies_to_json(self, cookies: List[Dict]) -> bool:
        """
        Sauvegarder les cookies au format JSON (pour backup/export)
        
        Args:
            cookies: Liste de cookies au format Selenium
            
        Returns:
            True si succès
        """
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ {len(cookies)} cookies sauvegardés dans {self.json_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des cookies JSON: {e}")
            return False
    
    def import_cookies_from_json(self, json_file: str) -> bool:
        """
        Importer des cookies depuis un fichier JSON et les convertir en pickle
        
        Args:
            json_file: Chemin vers le fichier JSON à importer
            
        Returns:
            True si succès
        """
        logger.info(f"Import des cookies depuis {json_file}...")
        
        # Charger depuis JSON
        cookies = self.load_cookies_from_json(json_file)
        
        if not cookies:
            logger.error("Aucun cookie valide trouvé dans le fichier JSON")
            return False
        
        # Sauvegarder en pickle pour utilisation future
        success = self.save_cookies_to_pickle(cookies)
        
        if success:
            logger.info(f"✓ {len(cookies)} cookies importés et sauvegardés")
            # Backup JSON aussi
            self.save_cookies_to_json(cookies)
        
        return success
    
    def get_cookies(self) -> List[Dict]:
        """
        Récupérer les cookies (essaie pickle d'abord, puis JSON)
        
        Returns:
            Liste de cookies au format Selenium
        """
        # Essayer pickle d'abord (plus rapide)
        cookies = self.load_cookies_from_pickle()
        
        if cookies:
            return cookies
        
        # Sinon essayer JSON
        logger.info("Pas de cookies pickle, essai avec JSON...")
        cookies = self.load_cookies_from_json()
        
        if cookies:
            # Sauvegarder en pickle pour la prochaine fois
            self.save_cookies_to_pickle(cookies)
        
        return cookies

