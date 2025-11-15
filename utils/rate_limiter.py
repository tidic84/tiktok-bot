"""Gestionnaire de limites et délais pour éviter les bans"""
import time
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Gère les délais entre actions pour simuler un comportement humain"""
    
    def __init__(self, config):
        """
        Initialiser le rate limiter
        
        Args:
            config: Objet de configuration
        """
        self.config = config
        self.last_action_time = None
        logger.info("RateLimiter initialisé")
    
    def wait_random_delay(self):
        """
        Attendre un délai aléatoire entre MIN et MAX configuré
        """
        delay = random.randint(
            self.config.MIN_DELAY_BETWEEN_UPLOADS,
            self.config.MAX_DELAY_BETWEEN_UPLOADS
        )
        
        minutes = delay / 60
        logger.info(f"⏳ Pause de {minutes:.1f} minutes...")
        time.sleep(delay)
        self.last_action_time = datetime.now()
    
    def is_active_hours(self) -> bool:
        """
        Vérifier si on est dans les heures d'activité configurées
        
        Returns:
            True si on est dans les heures actives
        """
        current_hour = datetime.now().hour
        is_active = self.config.ACTIVE_HOURS_START <= current_hour < self.config.ACTIVE_HOURS_END
        
        if not is_active:
            logger.info(
                f"Hors heures d'activité (actuellement {current_hour}h, "
                f"actif de {self.config.ACTIVE_HOURS_START}h à {self.config.ACTIVE_HOURS_END}h)"
            )
        
        return is_active
    
    def wait_until_active_hours(self):
        """
        Attendre jusqu'aux prochaines heures d'activité
        """
        while not self.is_active_hours():
            current_hour = datetime.now().hour
            
            if current_hour < self.config.ACTIVE_HOURS_START:
                # Avant les heures d'activité
                hours_to_wait = self.config.ACTIVE_HOURS_START - current_hour
            else:
                # Après les heures d'activité, attendre jusqu'au lendemain
                hours_to_wait = 24 - current_hour + self.config.ACTIVE_HOURS_START
            
            logger.info(f"En attente de {hours_to_wait}h jusqu'aux heures d'activité...")
            time.sleep(3600)  # Vérifier toutes les heures

    def should_take_break(self, actions_count: int, break_threshold: int = 5) -> bool:
        """
        Déterminer s'il faut prendre une pause plus longue
        
        Args:
            actions_count: Nombre d'actions effectuées
            break_threshold: Seuil pour déclencher une pause
            
        Returns:
            True s'il faut prendre une pause
        """
        return actions_count > 0 and actions_count % break_threshold == 0
    
    def take_long_break(self, min_minutes: int = 30, max_minutes: int = 60):
        """
        Prendre une pause longue pour simuler une absence
        
        Args:
            min_minutes: Durée minimum en minutes
            max_minutes: Durée maximum en minutes
        """
        delay_minutes = random.randint(min_minutes, max_minutes)
        delay_seconds = delay_minutes * 60
        
        logger.info(f"⏸️  Pause longue de {delay_minutes} minutes pour simuler comportement humain...")
        time.sleep(delay_seconds)

