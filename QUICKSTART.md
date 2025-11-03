# Guide de Démarrage Rapide

## Installation en 3 minutes

### 1️⃣ Installation automatique

```bash
bash install.sh
```

Cela va :
- Créer l'environnement virtuel Python
- Installer toutes les dépendances
- Installer Playwright
- Créer le fichier .env

### 2️⃣ Configuration

Éditez le fichier `.env` :

```bash
nano .env
# ou
vim .env
# ou utilisez votre éditeur préféré
```

Remplissez vos identifiants TikTok :

```env
TIKTOK_USERNAME=votre_username
TIKTOK_PASSWORD=votre_mot_de_passe
```

### 3️⃣ Lancement

```bash
bash start.sh
# ou directement
python main.py
```

## Première Utilisation

1. **Connexion manuelle** : Le bot ouvrira Chrome et vous demandera de vous connecter manuellement à TikTok
2. **Sauvegarde** : Une fois connecté, le bot sauvegarde les cookies
3. **Automatique** : Les prochaines fois, la connexion sera automatique

## Commandes Utiles

### Voir les logs en temps réel

```bash
tail -f logs/bot_$(date +%Y%m%d).log
```

### Vérifier la base de données

```bash
sqlite3 tiktok_bot.db "SELECT COUNT(*) as total FROM processed_videos;"
sqlite3 tiktok_bot.db "SELECT COUNT(*) as uploaded FROM processed_videos WHERE is_uploaded=1;"
```

### Nettoyer les vidéos téléchargées

```bash
rm -rf downloaded_videos/*.mp4
```

### Réinitialiser les cookies

```bash
rm tiktok_cookies.pkl
```

## Personnalisation Rapide

### Changer le nombre de vidéos par jour

Dans `config.py`, ligne 22 :

```python
MAX_VIDEOS_PER_DAY = 20  # Changez cette valeur
```

### Modifier les critères de sélection

Dans `config.py`, lignes 14-16 :

```python
MIN_LIKES = 10000       # Minimum de likes
MIN_VIEWS = 100000      # Minimum de vues
MIN_ENGAGEMENT_RATE = 0.05  # Taux d'engagement minimum
```

### Ajouter des hashtags

Dans `config.py`, ligne 19 :

```python
TARGET_HASHTAGS = ['#viral', '#fyp', '#trending', '#votre_hashtag']
```

## Résolution de Problèmes

### Le bot ne trouve pas de vidéos

→ Réduisez les critères dans `config.py` :

```python
MIN_LIKES = 5000
MIN_VIEWS = 50000
```

### Problème de connexion TikTok

→ Supprimez les cookies et reconnectez-vous :

```bash
rm tiktok_cookies.pkl
python main.py
```

### Erreur Playwright

→ Réinstallez Playwright :

```bash
source venv/bin/activate
playwright install chromium
```

### Le navigateur ne s'ouvre pas

→ Désactivez le mode headless dans `config.py` :

```python
HEADLESS_MODE = False
```

## Conseils pour Débuter

### Stratégie Progressive

**Semaine 1** : 5 vidéos/jour
```python
MAX_VIDEOS_PER_DAY = 5
```

**Semaine 2** : 10 vidéos/jour
```python
MAX_VIDEOS_PER_DAY = 10
```

**Semaine 3+** : 15-20 vidéos/jour
```python
MAX_VIDEOS_PER_DAY = 20
```

### Optimiser les Heures de Publication

Modifiez dans `config.py` :

```python
ACTIVE_HOURS_START = 17  # Commence à 17h
ACTIVE_HOURS_END = 23    # Termine à 23h
```

### Cibler une Niche Spécifique

Dans `config.py` :

```python
TARGET_HASHTAGS = [
    '#gaming',
    '#fortnite', 
    '#minecraft',
    '#gamingclips'
]
```

## Statistiques

### Voir les performances

```bash
sqlite3 tiktok_bot.db << EOF
SELECT 
    COUNT(*) as total_traitees,
    SUM(CASE WHEN is_uploaded=1 THEN 1 ELSE 0 END) as uploadees,
    AVG(engagement_rate) as engagement_moyen
FROM processed_videos;
EOF
```

### Top 10 meilleures vidéos

```bash
sqlite3 tiktok_bot.db << EOF
SELECT id, author, views, likes, engagement_rate 
FROM processed_videos 
ORDER BY engagement_rate DESC 
LIMIT 10;
EOF
```

## Support

- **Logs** : Consultez `logs/bot_YYYYMMDD.log`
- **Documentation complète** : Voir `README.md`
- **Base de données** : Fichier `tiktok_bot.db`

## Arrêter le Bot

Appuyez sur `Ctrl+C` dans le terminal où le bot tourne.

Le bot se fermera proprement en quelques secondes.

---

**Bon republishing ! 🚀**

