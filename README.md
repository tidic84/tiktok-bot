# Bot TikTok - Récupération et Republication Automatique

Bot Python automatisé qui récupère les vidéos TikTok les plus virales et les republie automatiquement sur un compte TikTok.

## ⚠️ Avertissements Importants

- **Légalité**: Ce bot peut violer les conditions d'utilisation de TikTok
- **Droits d'auteur**: Les vidéos appartiennent aux créateurs originaux
- **Risque de ban**: Votre compte peut être suspendu ou banni
- **Utilisation à vos risques**: Les développeurs ne sont pas responsables des conséquences

## 🎯 Fonctionnalités

- ✅ Récupération automatique des vidéos trending via TikTokApi
- ✅ Recherche par hashtags populaires (#viral, #fyp, #trending)
- ✅ Filtrage intelligent par engagement (likes, vues, commentaires)
- ✅ Téléchargement automatique des vidéos MP4
- ✅ Upload automatique via Selenium
- ✅ **Copie COMPLÈTE des descriptions originales avec tous les hashtags** 🆕
- ✅ Insertion robuste avec fallback JavaScript pour les textes longs 🆕
- ✅ Base de données SQLite pour éviter les doublons
- ✅ Rate limiting intelligent pour éviter les bans
- ✅ Simulation de comportement humain (délais aléatoires, heures d'activité)
- ✅ Logging complet de toutes les actions
- ✅ Sauvegarde des cookies pour connexion persistante

## 📋 Prérequis

- Python 3.8+
- Google Chrome installé
- Compte TikTok dédié (recommandé: nouveau compte)
- Connexion internet stable

## 🚀 Installation

### 1. Cloner ou télécharger le projet

```bash
cd Tiktok
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer Playwright (pour TikTokApi)

```bash
playwright install
```

### 5. Configuration

Copiez le fichier `.env.example` en `.env`:

```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos informations:

```env
TIKTOK_USERNAME=votre_username
TIKTOK_PASSWORD=votre_mot_de_passe
```

### 6. Personnaliser la configuration (optionnel)

Éditez `config.py` pour ajuster les paramètres:

```python
MIN_LIKES = 10000              # Minimum de likes requis
MIN_VIEWS = 100000             # Minimum de vues requis
MIN_ENGAGEMENT_RATE = 0.05     # Taux d'engagement minimum (5%)
MAX_VIDEOS_PER_DAY = 20        # Limite quotidienne
TARGET_HASHTAGS = [...]        # Hashtags à rechercher
```

## 🎮 Utilisation

### Lancement du bot

```bash
python main.py
```

### Première connexion

Lors du premier lancement:
1. Le bot ouvrira une fenêtre Chrome
2. Connectez-vous manuellement à TikTok
3. Le bot détectera la connexion et sauvegardera les cookies
4. Les prochaines fois, la connexion sera automatique

### Logs

Les logs sont sauvegardés dans le dossier `logs/`:
- `bot_YYYYMMDD.log`: Log du jour
- Aussi affichés dans la console en temps réel

## 📊 Structure du Projet

```
Tiktok/
├── main.py                    # Point d'entrée principal
├── config.py                  # Configuration
├── requirements.txt           # Dépendances
├── .env                       # Variables d'environnement
├── README.md                  # Documentation
├── scraper/                   # Module de scraping
│   ├── tiktok_scraper.py     # Récupération via TikTokApi
│   └── video_filter.py       # Filtrage par engagement
├── downloader/                # Module de téléchargement
│   └── video_downloader.py   # Download des MP4
├── uploader/                  # Module d'upload
│   └── selenium_uploader.py  # Upload automatique
├── database/                  # Module base de données
│   └── db_manager.py         # Gestion SQLite
├── utils/                     # Utilitaires
│   └── rate_limiter.py       # Gestion des délais
├── downloaded_videos/         # Vidéos téléchargées
├── logs/                      # Fichiers de log
└── tiktok_bot.db             # Base de données SQLite
```

## ⚙️ Fonctionnement

### Cycle de traitement

1. **Scraping**: Récupère 50 vidéos trending + 30 par hashtag
2. **Filtrage**: Sélectionne les vidéos avec meilleur engagement
3. **Vérification**: Check si déjà traitées (base de données)
4. **Téléchargement**: Download des vidéos MP4
5. **Upload**: Publication sur TikTok avec description/hashtags
6. **Pause**: Délai aléatoire 5-15 minutes entre uploads
7. **Répétition**: Nouveau cycle toutes les heures

### Stratégie anti-ban

- ✅ Délais aléatoires entre actions (5-15 minutes)
- ✅ Heures d'activité configurables (8h-23h)
- ✅ Pauses longues tous les 5 uploads (30-45 minutes)
- ✅ User-Agent aléatoire
- ✅ Cookies persistants
- ✅ Limite quotidienne (20 vidéos/jour)

## 🔧 Configuration Avancée

### Modifier les critères de sélection

Dans `config.py`:

```python
MIN_LIKES = 50000              # Vidéos plus virales
MIN_VIEWS = 500000
MIN_ENGAGEMENT_RATE = 0.10     # 10% minimum
```

### Changer les hashtags ciblés

```python
TARGET_HASHTAGS = [
    '#votre_niche',
    '#gaming',
    '#comedy',
    # etc.
]
```

### Ajuster la fréquence

```python
CHECK_INTERVAL = 7200          # 2 heures entre cycles
MAX_VIDEOS_PER_DAY = 30        # Plus de vidéos/jour
```

### Mode headless (sans interface)

```python
HEADLESS_MODE = True           # Navigateur invisible
```

## 🐛 Dépannage

### Problème: Le bot ne trouve pas de vidéos

- Vérifiez votre connexion internet
- Réduisez `MIN_LIKES` et `MIN_VIEWS` dans la config
- Vérifiez que TikTokApi fonctionne: `playwright install`

### Problème: Échec de connexion à TikTok

- Supprimez `tiktok_cookies.pkl` et reconnectez-vous
- Vérifiez vos identifiants dans `.env`
- Désactivez l'authentification à deux facteurs sur votre compte

### Problème: L'upload échoue

- TikTok change régulièrement son interface
- Vérifiez les sélecteurs CSS dans `selenium_uploader.py`
- Essayez en mode non-headless pour voir l'erreur

### Problème: Compte banni

- Utilisez un nouveau compte avec un email différent
- Réduisez `MAX_VIDEOS_PER_DAY` (ex: 5-10)
- Augmentez les délais entre uploads
- Utilisez un VPN ou proxy

## 📝 Description Complète - Nouvelle Fonctionnalité

### ✨ Copie Intégrale des Descriptions

Le bot copie maintenant **la description COMPLÈTE** des vidéos TikTok, incluant :

- ✅ **Tout le texte original** sans troncature
- ✅ **Tous les hashtags originaux** préservés
- ✅ **Tous les emojis** conservés
- ✅ **Vérification automatique** de l'insertion
- ✅ **Fallback JavaScript** pour les textes longs

### 🔍 Comment ça marche ?

1. **Récupération** : La description complète est extraite depuis l'API TikTok ou yt-dlp
2. **Conservation** : Aucune modification n'est appliquée (pas d'ajout de hashtags)
3. **Insertion** : Deux méthodes pour garantir l'insertion complète :
   - Méthode standard (`send_keys`)
   - Fallback JavaScript pour les cas difficiles
4. **Vérification** : Le bot vérifie que 100% du texte a été inséré

### 📊 Logs Détaillés

```
📝 Description originale complète (245 caractères): crispy beef tacos 🌮...
✓ Zone de description trouvée avec sélecteur: div[contenteditable='true']
✓ Description insérée via send_keys
✓ Texte inséré vérifié: 245 caractères (attendu: 245)
```

### 🧪 Tester la Fonctionnalité

Utilisez le script de test fourni :

```bash
python test_description_complete.py
```

Ce script récupère quelques vidéos et affiche les descriptions complètes pour vérification.

### 📖 Documentation Complète

Consultez `DESCRIPTION_COMPLETE.md` pour tous les détails techniques.

## 📈 Améliorations Futures

- [ ] Interface web pour monitoring
- [ ] Support multi-comptes
- [ ] Édition automatique (watermark, logo)
- [ ] Statistiques de performance
- [ ] Catégories par niche
- [ ] Support proxies rotatifs
- [ ] Notifications (Discord, Telegram)

## 🤝 Contribution

Les contributions sont les bienvenues! N'hésitez pas à:
- Signaler des bugs
- Proposer des nouvelles fonctionnalités
- Améliorer la documentation
- Partager vos configurations optimales

## 📝 Licence

Ce projet est fourni "tel quel" sans aucune garantie. Utilisez-le de manière responsable et éthique.

## 💡 Conseils d'Utilisation

### Pour maximiser le volume

1. **Nouveau compte**: Utilisez un compte récent, "chauffez-le" manuellement pendant 1-2 semaines
2. **Commencez doucement**: 5 vidéos/jour la première semaine, puis augmentez progressivement
3. **Diversifiez**: Changez les descriptions, variez les hashtags
4. **Horaires**: Publiez aux heures de forte activité (18h-23h)
5. **Qualité**: Ne descendez pas trop les critères de filtrage

### Pour éviter les bans

1. **Pas de spam**: Ne jamais dépasser 30 vidéos/jour
2. **Comportement humain**: Gardez les délais aléatoires activés
3. **IP unique**: Évitez de changer d'IP fréquemment
4. **Contenu varié**: Ne republier pas toujours du même créateur
5. **Crédit**: Mentionnez l'auteur original en description (optionnel mais recommandé)

## 📞 Support

Pour toute question ou problème:
- Consultez les logs dans `logs/`
- Vérifiez les issues GitHub existantes
- Créez une nouvelle issue avec détails et logs

---

**Disclaimer**: Ce projet est à but éducatif. Respectez les droits d'auteur et les conditions d'utilisation des plateformes.

