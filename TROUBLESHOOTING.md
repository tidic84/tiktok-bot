# Guide de Dépannage Avancé

## 🔍 Diagnostic Initial

### Vérifier l'Installation

```bash
python test_setup.py
```

Ce script vérifie :
- ✓ Tous les modules Python
- ✓ Toutes les dépendances
- ✓ La configuration
- ✓ La base de données
- ✓ Les dossiers
- ✓ Le fichier .env

## 🐛 Problèmes Courants et Solutions

### 1. Erreurs d'Import

#### Symptôme
```
ImportError: No module named 'TikTokApi'
ModuleNotFoundError: No module named 'selenium'
```

#### Solution
```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Réinstaller les dépendances
pip install -r requirements.txt

# Si le problème persiste
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
```

### 2. Problèmes avec TikTokApi

#### Symptôme
```
playwright._impl._api_types.Error: Browser closed
Error: Failed to launch browser
```

#### Solutions

**A. Réinstaller Playwright**
```bash
playwright install
# ou spécifiquement
playwright install chromium
```

**B. Permissions manquantes**
```bash
# Linux
sudo playwright install-deps

# Mac
xcode-select --install
```

**C. Mode headless problématique**
Dans `config.py` :
```python
HEADLESS_MODE = False  # Changer à False
```

### 3. Connexion TikTok Échoue

#### Symptôme
```
Erreur lors de la connexion
Timeout: connexion non effectuée
```

#### Solutions

**A. Supprimer les cookies**
```bash
rm tiktok_cookies.pkl
python main.py
```

**B. Vérifier les identifiants**
```bash
cat .env  # Vérifier USERNAME et PASSWORD
```

**C. Désactiver 2FA**
- Allez sur TikTok.com
- Paramètres > Sécurité
- Désactivez l'authentification à deux facteurs

**D. Connexion manuelle détaillée**
```python
# Le bot attend 5 minutes pour la connexion manuelle
# Si ce n'est pas assez, modifiez dans selenium_uploader.py :
max_wait = 600  # 10 minutes au lieu de 300
```

### 4. Aucune Vidéo Trouvée

#### Symptôme
```
✓ 0 vidéos de qualité trouvées
Aucune vidéo ne correspond aux critères
```

#### Solutions

**A. Assouplir les critères**
Dans `config.py` :
```python
MIN_LIKES = 5000       # Au lieu de 10000
MIN_VIEWS = 50000      # Au lieu de 100000
MIN_ENGAGEMENT_RATE = 0.02  # Au lieu de 0.05
```

**B. Vérifier les hashtags**
```python
TARGET_HASHTAGS = ['#fyp', '#viral']  # Hashtags très populaires
```

**C. Tester le scraper manuellement**
```python
# test_scraper.py
import asyncio
from config import Config
from scraper.tiktok_scraper import TikTokScraper

async def test():
    config = Config()
    scraper = TikTokScraper(config)
    await scraper.initialize()
    videos = await scraper.get_trending_videos(10)
    print(f"Trouvé {len(videos)} vidéos")
    for v in videos:
        print(f"- {v['id']}: {v['views']} vues, {v['likes']} likes")
    await scraper.close()

asyncio.run(test())
```

### 5. Échec de Téléchargement

#### Symptôme
```
Erreur HTTP lors du téléchargement
Erreur lors du téléchargement de XXXXX
```

#### Solutions

**A. Vérifier la connexion**
```bash
curl -I https://www.tiktok.com
```

**B. Problème de timeout**
Dans `downloader/video_downloader.py`, ligne 67 :
```python
timeout=120  # Au lieu de 60
```

**C. Problème d'URL**
```python
# Parfois l'URL de vidéo est None
# Vérifiez les logs pour voir si video_url est présent
```

### 6. Upload Échoue

#### Symptôme
```
Impossible de cliquer sur Publier
Erreur lors de l'upload
Zone de description non trouvée
```

#### Solutions

**A. Interface TikTok a changé**
```python
# TikTok change régulièrement son interface
# Il faut mettre à jour les sélecteurs CSS

# Dans selenium_uploader.py, ajoutez des logs pour debug :
print(self.driver.page_source)  # Voir le HTML de la page
```

**B. Téléchargement de la vidéo trop lent**
```python
# Augmenter le délai d'attente dans selenium_uploader.py :
time.sleep(15)  # Au lieu de 10, ligne 203
```

**C. Format de fichier**
```bash
# Vérifier que la vidéo est bien un MP4
file downloaded_videos/*.mp4
```

**D. Mode debug**
```python
# Dans selenium_uploader.py
# Commenter le headless pour voir ce qui se passe
options.add_argument('--headless=new')  # Commenter cette ligne
```

### 7. Compte Banni ou Shadowban

#### Symptômes
- Vidéos ne reçoivent aucune vue
- Compte ne peut plus publier
- Message "Account under review"

#### Solutions

**A. Prévention**
```python
# Réduire drastiquement l'activité
MAX_VIDEOS_PER_DAY = 3
MIN_DELAY_BETWEEN_UPLOADS = 1800  # 30 minutes
```

**B. Récupération**
```
1. Arrêtez le bot immédiatement
2. Utilisez le compte manuellement pendant 1-2 semaines
3. Publiez du contenu original de qualité
4. Interagissez avec d'autres créateurs
5. Ne relancez le bot qu'avec des limites très basses
```

**C. Nouveau départ**
```
1. Créez un nouveau compte
2. "Chauffez" le compte manuellement pendant 2 semaines
3. Publiez 5-10 vidéos manuellement
4. Suivez des comptes, likez, commentez
5. Lancez le bot avec MAX_VIDEOS_PER_DAY = 3
6. Augmentez progressivement
```

### 8. Problèmes de Performance

#### Symptôme
```
Le bot est très lent
Consomme beaucoup de RAM
```

#### Solutions

**A. Nettoyer les vidéos**
```python
# Dans config.py ou périodiquement
self.downloader.cleanup_old_videos(keep_count=20)  # Garder moins
```

**B. Limiter le scraping**
```python
TRENDING_VIDEOS_COUNT = 30  # Au lieu de 50
HASHTAG_VIDEOS_COUNT = 20   # Au lieu de 30
```

**C. Fermer les sessions**
```python
# S'assurer que tout est bien fermé
# Dans main.py, le finally devrait toujours s'exécuter
```

### 9. Erreurs de Base de Données

#### Symptôme
```
database is locked
Erreur lors de l'ajout de la vidéo
```

#### Solutions

**A. Corrupted database**
```bash
# Sauvegarder
cp tiktok_bot.db tiktok_bot.db.backup

# Vérifier
sqlite3 tiktok_bot.db "PRAGMA integrity_check;"

# Réparer si nécessaire
sqlite3 tiktok_bot.db ".dump" | sqlite3 tiktok_bot_new.db
mv tiktok_bot_new.db tiktok_bot.db
```

**B. Réinitialiser**
```bash
rm tiktok_bot.db
python main.py  # La DB sera recréée
```

### 10. Erreurs Selenium / WebDriver

#### Symptôme
```
WebDriverException
SessionNotCreatedException
ChromeDriver version mismatch
```

#### Solutions

**A. Mettre à jour ChromeDriver**
```bash
pip install --upgrade webdriver-manager
```

**B. Chrome non installé**
```bash
# Linux (Ubuntu/Debian)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Mac
brew install --cask google-chrome
```

**C. Version mismatch**
```python
# webdriver-manager le gère normalement automatiquement
# Mais si problème, forcer la réinstallation :
from webdriver_manager.chrome import ChromeDriverManager
ChromeDriverManager().install()
```

## 🔧 Mode Debug Avancé

### Activer les logs détaillés

Dans `main.py`, modifier le niveau de log :

```python
logging.basicConfig(
    level=logging.DEBUG,  # Au lieu de INFO
    # ...
)
```

### Logs par module

```python
# Logs spécifiques pour chaque composant
logging.getLogger('scraper').setLevel(logging.DEBUG)
logging.getLogger('uploader').setLevel(logging.DEBUG)
```

### Capturer les exceptions

```python
# Ajouter dans main.py
import traceback

try:
    # code...
except Exception as e:
    logger.error(f"Erreur: {e}")
    logger.error(traceback.format_exc())  # Stack trace complète
```

## 📊 Outils de Diagnostic

### 1. Vérifier l'état de la DB

```bash
sqlite3 tiktok_bot.db << EOF
.tables
.schema processed_videos
SELECT COUNT(*) FROM processed_videos;
SELECT * FROM processed_videos LIMIT 5;
EOF
```

### 2. Monitoring en temps réel

```bash
# Terminal 1 : Lancer le bot
python main.py

# Terminal 2 : Suivre les logs
tail -f logs/bot_$(date +%Y%m%d).log

# Terminal 3 : Monitoring système
watch -n 2 'ps aux | grep python'
```

### 3. Test de connexion TikTok

```bash
curl -v https://www.tiktok.com 2>&1 | grep -E "(HTTP|Location|Set-Cookie)"
```

### 4. Vérifier Playwright

```bash
playwright --version
playwright install --dry-run
```

## 🆘 Dernière Solution : Réinstallation Propre

```bash
# Sauvegarder les données importantes
cp .env .env.backup
cp tiktok_bot.db tiktok_bot.db.backup
cp tiktok_cookies.pkl tiktok_cookies.pkl.backup 2>/dev/null || true

# Tout supprimer
rm -rf venv/
rm -rf __pycache__/
rm -rf */__pycache__/
rm -rf *.pyc

# Réinstaller
bash install.sh

# Restaurer
cp .env.backup .env
cp tiktok_bot.db.backup tiktok_bot.db
```

## 📞 Obtenir de l'Aide

### Informations à fournir

Quand vous demandez de l'aide, incluez :

```bash
# 1. Version Python
python --version

# 2. Système d'exploitation
uname -a  # Linux/Mac
# ou
ver       # Windows

# 3. Logs pertinents
tail -50 logs/bot_$(date +%Y%m%d).log

# 4. Test d'installation
python test_setup.py

# 5. Versions des packages
pip list | grep -E "(TikTokApi|selenium|playwright)"
```

## 🔄 Mises à Jour

### Garder le bot à jour

```bash
git pull  # Si vous utilisez git
pip install --upgrade -r requirements.txt
playwright install
```

---

**Si aucune solution ne fonctionne, créez une issue avec tous les détails ci-dessus !**

